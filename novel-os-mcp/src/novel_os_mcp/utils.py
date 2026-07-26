import json
from datetime import datetime, date
from typing import Any


def _serialize_value(v: Any) -> Any:
    """Convert non-serializable types to serializable forms."""
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


def row_to_dict(row) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: _serialize_value(v) for k, v in dict(row).items()}


def rows_to_dicts(rows) -> list[dict[str, Any]]:
    return [row_to_dict(row) for row in rows if row is not None]


class _JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), cls=_JsonEncoder)


def ensure_json_value(value: Any) -> Any:
    """If value is a string that looks like JSON, parse it; otherwise return as-is."""
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("{", "[")):
            try:
                return json.loads(text)
            except Exception:
                return value
    return value

