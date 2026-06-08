"""users/{uid}/generation_preferences/default — account-level generate instructions."""

from __future__ import annotations

from typing import Any

from app.services.firestore.timestamps import deep_convert_firestore_data, utc_now

PREFERENCES_SUBCOLLECTION = "generation_preferences"
PREFERENCES_DOC_ID = "default"


def _preferences_ref(db: Any, uid: str):
    return (
        db.collection("users")
        .document(uid)
        .collection(PREFERENCES_SUBCOLLECTION)
        .document(PREFERENCES_DOC_ID)
    )


def get_generation_preferences(db: Any, uid: str) -> str:
    snap = _preferences_ref(db, uid).get()
    if not snap.exists:
        return ""
    data = deep_convert_firestore_data(snap.to_dict() or {})
    return str(data.get("global_instructions") or "")


def set_generation_preferences(db: Any, uid: str, global_instructions: str) -> str:
    ref = _preferences_ref(db, uid)
    ref.set(
        {
            "global_instructions": global_instructions,
            "updated_at": utc_now(),
        }
    )
    return global_instructions
