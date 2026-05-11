# nldate

`nldate` is a small Python library for parsing focused natural-language date
strings into `datetime.date` objects.

```python
from datetime import date

from nldate import parse

parse("5 days before December 1st, 2025")
# date(2025, 11, 26)

parse("next Tuesday", today=date(2025, 11, 24))
# date(2025, 11, 25)
```

## Development

This project is managed with `uv`.

```bash
uv sync
uv run pytest
uv run mypy
uv run ruff check
```
