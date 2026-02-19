"""Tests for generator.io module."""
import json
import os
import tempfile

import pytest

from generator.io import read_text_list, read_json, parse_state_region_mapping


class TestReadTextList:
    def test_reads_lines(self, tmp_path):
        f = tmp_path / "words.txt"
        f.write_text("alpha\nbeta\ngamma\n")
        result = read_text_list(str(f))
        assert result == ["alpha", "beta", "gamma"]

    def test_strips_whitespace(self, tmp_path):
        f = tmp_path / "words.txt"
        f.write_text("  hello  \n  world  \n")
        result = read_text_list(str(f))
        assert result == ["hello", "world"]

    def test_skips_blank_lines(self, tmp_path):
        f = tmp_path / "words.txt"
        f.write_text("a\n\nb\n\n\nc\n")
        result = read_text_list(str(f))
        assert result == ["a", "b", "c"]

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            read_text_list("/nonexistent/path/file.txt")

    def test_empty_file_raises(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("\n\n\n")
        with pytest.raises(ValueError, match="empty"):
            read_text_list(str(f))


class TestReadJson:
    def test_reads_json(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text(json.dumps({"key": "value"}))
        result = read_json(str(f))
        assert result == {"key": "value"}

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            read_json("/nonexistent/path/data.json")

    def test_reads_list(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text(json.dumps([1, 2, 3]))
        result = read_json(str(f))
        assert result == [1, 2, 3]


class TestParseStateRegionMapping:
    def test_flat_dict_shape(self):
        obj = {"CA": "West", "NY": "Northeast"}
        result = parse_state_region_mapping(obj)
        assert result == {"CA": "West", "NY": "Northeast"}

    def test_states_list_shape(self):
        obj = {
            "states": [
                {"state": "CA", "region": "West"},
                {"state": "NY", "region": "Northeast"},
            ]
        }
        result = parse_state_region_mapping(obj)
        assert result == {"CA": "West", "NY": "Northeast"}

    def test_invalid_shape_raises(self):
        with pytest.raises(ValueError):
            parse_state_region_mapping([1, 2, 3])

    def test_empty_states_list_raises(self):
        with pytest.raises(ValueError):
            parse_state_region_mapping({"states": []})

    def test_states_list_skips_bad_entries(self):
        obj = {
            "states": [
                {"state": "CA", "region": "West"},
                "bad entry",
                {"state": 123, "region": "East"},
                {"state": "NY", "region": "Northeast"},
            ]
        }
        result = parse_state_region_mapping(obj)
        assert result == {"CA": "West", "NY": "Northeast"}

    def test_mixed_types_in_flat_dict_falls_through(self):
        obj = {"CA": "West", "bad": 123}
        with pytest.raises(ValueError):
            parse_state_region_mapping(obj)
