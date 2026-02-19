# generator/

Stdlib-only dummy data generator.

## Setup

Edit `generator/settings.py`:

- Set the vocab file paths:
  - `FIRST_NAMES_PATH`, `LAST_NAMES_PATH`
  - `ACCOUNT_NOUNS_PATH`, `ACCOUNT_SUFFIXES_PATH`
  - `INDUSTRIES_PATH`, `STAGES_PATH`
- Set `STATES_TO_REGION_JSON_PATH` to a JSON file containing a state->region mapping.

Text file format: **one token per line**. Blank lines are ignored.

## Usage

```python
from generator import generate

reps, accounts, opportunities, territories = generate(seed=123)
```

No files are written; the function returns four Python lists of dicts.

## Self-test

```bash
python -m generator.selftest
```
