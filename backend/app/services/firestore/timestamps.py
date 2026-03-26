"""Convert Firestore Timestamp / DatetimeWithNanoseconds to datetime for Pydantic."""

from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def deep_convert_firestore_data(obj: Any) -> Any:
    """Recursively convert Firestore-native types to JSON/Pydantic-friendly values."""
    if isinstance(obj, dict):
        return {k: deep_convert_firestore_data(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_convert_firestore_data(v) for v in obj]
    if isinstance(obj, datetime):
        return ensure_utc(obj)
    # google.cloud.firestore_v1 types: Timestamp, DatetimeWithNanoseconds
    if hasattr(obj, "timestamp") and callable(getattr(obj, "timestamp")):
        try:
            ts = obj.timestamp()
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (TypeError, OSError, ValueError, AttributeError):
            pass
    return obj


def dump_datetimes_for_firestore(obj: Any) -> Any:
    """Ensure datetimes are UTC-aware for Firestore writes (accepts native datetime)."""
    if isinstance(obj, dict):
        return {k: dump_datetimes_for_firestore(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [dump_datetimes_for_firestore(v) for v in obj]
    if isinstance(obj, datetime):
        return ensure_utc(obj)
    return obj
