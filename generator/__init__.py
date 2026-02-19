"""Root package for stdlib-only data generation.

The public entrypoint is `generator.generate.generate()`.
"""

from __future__ import annotations

from .generate import generate

__all__ = ["generate"]
