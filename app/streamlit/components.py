"""Reusable UI components, sanitizers, and formatting adapters for Streamlit views.

Follows strict domain rules:
- Missing data is NULL / N/A, never 0.0 (Rule R1).
- Formula injection protection on all CSV exports (OWASP guidelines).
- Safe compatibility fallbacks so tests can run with or without full Streamlit.
"""

from __future__ import annotations

import csv
import io
import math
from collections.abc import Mapping
from contextlib import AbstractContextManager, nullcontext
from typing import Any, Protocol


class UI(Protocol):
    """Streamlit-compatible surface used by views and deterministic test suites."""

    session_state: Any

    def title(self, body: str) -> Any: ...

    def caption(self, body: str) -> Any: ...

    def info(self, body: str) -> Any: ...

    def warning(self, body: str) -> Any: ...

    def error(self, body: str) -> Any: ...

    def success(self, body: str) -> Any: ...

    def json(self, body: Any, **kwargs: Any) -> Any: ...

    def text_input(self, label: str, **kwargs: Any) -> str: ...

    def button(self, label: str, **kwargs: Any) -> bool: ...

    def selectbox(self, label: str, options: list[Any], **kwargs: Any) -> Any: ...

    def spinner(self, text: str) -> AbstractContextManager[None]: ...

    def number_input(self, label: str, **kwargs: Any) -> int | float: ...

    def checkbox(self, label: str, **kwargs: Any) -> bool: ...

    def expander(self, label: str, expanded: bool = False) -> AbstractContextManager[None]: ...


def ui_markdown(ui: UI, text: str) -> None:
    """Render markdown text if supported by UI, otherwise fallback to caption."""
    if hasattr(ui, "markdown"):
        ui.markdown(text)
    else:
        ui.caption(text)


def ui_subheader(ui: UI, text: str) -> None:
    """Render a subheader if supported, otherwise format as markdown/caption."""
    if hasattr(ui, "subheader"):
        ui.subheader(text)
    elif hasattr(ui, "markdown"):
        ui.markdown(f"### {text}")
    else:
        ui.caption(f"=== {text} ===")


def ui_divider(ui: UI) -> None:
    """Render a visual divider if supported."""
    if hasattr(ui, "divider"):
        ui.divider()
    elif hasattr(ui, "markdown"):
        ui.markdown("---")
    else:
        ui.caption("---")


def ui_dataframe(ui: UI, data: Any, **kwargs: Any) -> None:
    """Render tabular data via dataframe or table, falling back to JSON."""
    if hasattr(ui, "dataframe"):
        ui.dataframe(data, **kwargs)
    elif hasattr(ui, "table"):
        ui.table(data)
    else:
        ui.json(data)


def ui_metric(
    ui: UI,
    label: str,
    value: Any,
    delta: Any = None,
    help_text: str | None = None,
    **kwargs: Any,
) -> None:
    """Render a metric card if supported, otherwise display as caption."""
    if hasattr(ui, "metric"):
        if help_text:
            ui.metric(label, value, delta=delta, help=help_text, **kwargs)
        else:
            ui.metric(label, value, delta=delta, **kwargs)
    else:
        delta_str = f" ({delta})" if delta is not None else ""
        ui.caption(f"**{label}**: {value}{delta_str}")


def ui_download_button(
    ui: UI,
    label: str,
    data: Any,
    file_name: str | None = None,
    mime: str | None = None,
    **kwargs: Any,
) -> bool:
    """Render a download button if supported, otherwise return False."""
    if hasattr(ui, "download_button"):
        return bool(ui.download_button(label, data, file_name=file_name, mime=mime, **kwargs))
    return False


def ui_expander(ui: UI, label: str, expanded: bool = False) -> AbstractContextManager[None]:
    """Provide an expandable container if supported, otherwise a no-op context."""
    if hasattr(ui, "expander"):
        return ui.expander(label, expanded=expanded)
    return nullcontext()


def read_prop(value: Any, key: str, default: Any = None) -> Any:
    """Read a field from a Pydantic model, Mapping, or object without modifying value."""
    if value is None:
        return default
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def jsonable(value: Any) -> Any:
    """Serialize a typed service output for display while preserving exact semantics."""
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def format_metric(val: Any, decimals: int = 2, fallback: str = "N/A") -> str:
    """Format a numerical metric adhering to Rule R1 (NULL is never 0.0)."""
    if val is None:
        return fallback
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return fallback
    if isinstance(val, (int, float)):
        return f"{val:.{decimals}f}" if isinstance(val, float) else str(val)
    return str(val)


def format_pct(val: Any, decimals: int = 1, fallback: str = "N/A") -> str:
    """Format a percentage metric adhering to Rule R1."""
    if val is None:
        return fallback
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return fallback
    if isinstance(val, (int, float)):
        return f"{val:.{decimals}f}%"
    return str(val)


def sanitize_csv_cell(value: Any) -> str:
    """Sanitize a cell value to prevent CSV formula injection (OWASP).

    Prepends a single quote if string begins with =, +, -, @, tab, or carriage return.
    """
    if value is None:
        return ""
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def generate_safe_csv(headers: list[str], rows: list[list[Any]]) -> str:
    """Generate an RFC 4180 CSV string with guaranteed formula injection immunity."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([sanitize_csv_cell(h) for h in headers])
    for row in rows:
        writer.writerow([sanitize_csv_cell(cell) for cell in row])
    return output.getvalue()


__all__ = [
    "UI",
    "format_metric",
    "format_pct",
    "generate_safe_csv",
    "jsonable",
    "read_prop",
    "sanitize_csv_cell",
    "ui_dataframe",
    "ui_divider",
    "ui_download_button",
    "ui_expander",
    "ui_markdown",
    "ui_metric",
    "ui_subheader",
]
