"""Tests for generator.rng module."""
import pytest
from generator.rng import Rng


class TestRng:
    def test_from_seed_deterministic(self):
        a = Rng.from_seed(42)
        b = Rng.from_seed(42)
        assert a.randint(0, 100) == b.randint(0, 100)

    def test_different_seeds_differ(self):
        a = Rng.from_seed(1)
        b = Rng.from_seed(2)
        results_a = [a.randint(0, 1000) for _ in range(10)]
        results_b = [b.randint(0, 1000) for _ in range(10)]
        assert results_a != results_b

    def test_randint_range(self):
        rng = Rng.from_seed(0)
        for _ in range(100):
            v = rng.randint(5, 10)
            assert 5 <= v <= 10

    def test_uniform_range(self):
        rng = Rng.from_seed(0)
        for _ in range(100):
            v = rng.uniform(1.0, 2.0)
            assert 1.0 <= v <= 2.0

    def test_choice(self):
        rng = Rng.from_seed(0)
        items = ["a", "b", "c"]
        for _ in range(20):
            assert rng.choice(items) in items

    def test_shuffle(self):
        rng = Rng.from_seed(0)
        original = [1, 2, 3, 4, 5]
        shuffled = list(original)
        rng.shuffle(shuffled)
        assert set(shuffled) == set(original)

    def test_sample(self):
        rng = Rng.from_seed(0)
        population = list(range(20))
        s = rng.sample(population, 5)
        assert len(s) == 5
        assert len(set(s)) == 5
        assert all(x in population for x in s)

    def test_random_zero_to_one(self):
        rng = Rng.from_seed(0)
        for _ in range(100):
            v = rng.random()
            assert 0.0 <= v < 1.0

    def test_paretovariate_positive(self):
        rng = Rng.from_seed(0)
        for _ in range(50):
            v = rng.paretovariate(1.0)
            assert v >= 1.0

    def test_date_between_same_day(self):
        rng = Rng.from_seed(0)
        d = rng.date_between("2026-01-15", "2026-01-15")
        assert d == "2026-01-15"

    def test_date_between_range(self):
        rng = Rng.from_seed(0)
        for _ in range(50):
            d = rng.date_between("2026-01-01", "2026-12-31")
            assert "2026-01-01" <= d <= "2026-12-31"

    def test_date_between_iso_format(self):
        rng = Rng.from_seed(0)
        d = rng.date_between("2026-03-01", "2026-03-31")
        import datetime as _dt
        parsed = _dt.date.fromisoformat(d)
        assert isinstance(parsed, _dt.date)

    def test_date_between_invalid_window_raises(self):
        rng = Rng.from_seed(0)
        with pytest.raises(ValueError):
            rng.date_between("2026-12-31", "2026-01-01")
