from typing import Any

from app.services.agents.models import OriginalRecipeDocument
from app.services.firestore.timestamps import (
    deep_convert_firestore_data,
    dump_datetimes_for_firestore,
    ensure_utc,
    utc_now,
)


def get_original_recipe(db: Any, recipe_id: str) -> OriginalRecipeDocument | None:
    snap = db.collection("original_recipes").document(recipe_id).get()
    if not snap.exists:
        return None
    data = deep_convert_firestore_data(snap.to_dict() or {})
    data["id"] = snap.id
    return OriginalRecipeDocument.model_validate(data)


def upsert_original_recipe(db: Any, doc: OriginalRecipeDocument) -> OriginalRecipeDocument:
    ref = db.collection("original_recipes").document(doc.id)
    snap = ref.get()
    payload = dump_datetimes_for_firestore(doc.model_dump(mode="python"))
    payload["id"] = doc.id
    if snap.exists:
        old = deep_convert_firestore_data(snap.to_dict() or {})
        if old.get("created_at"):
            payload["created_at"] = ensure_utc(old["created_at"])
    else:
        payload.setdefault("created_at", doc.created_at if doc.created_at else utc_now())
    ref.set(payload, merge=True)
    out = get_original_recipe(db, doc.id)
    assert out is not None
    return out
