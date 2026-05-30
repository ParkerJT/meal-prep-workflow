from typing import Any, Literal

from google.cloud.firestore import Query

from app.services.agents.models import ConvertedRecipe, OriginalRecipe, SavedRecipe
from app.services.firestore.timestamps import (
    deep_convert_firestore_data,
    dump_datetimes_for_firestore,
)


def _collection(db: Any, uid: str):
    return db.collection("users").document(uid).collection("saved_recipes")


def list_saved(db: Any, uid: str) -> list[tuple[str, SavedRecipe]]:
    docs = (
        _collection(db, uid)
        .order_by("saved_at", direction=Query.DESCENDING)
        .stream()
    )
    out: list[tuple[str, SavedRecipe]] = []
    for doc in docs:
        data = deep_convert_firestore_data(doc.to_dict() or {})
        out.append((doc.id, SavedRecipe.model_validate(data)))
    return out


def get_saved(db: Any, uid: str, saved_recipe_id: str) -> tuple[str, SavedRecipe] | None:
    snap = _collection(db, uid).document(saved_recipe_id).get()
    if not snap.exists:
        return None
    data = deep_convert_firestore_data(snap.to_dict() or {})
    return snap.id, SavedRecipe.model_validate(data)


def create_saved(db: Any, uid: str, recipe: SavedRecipe) -> tuple[str, SavedRecipe]:
    ref = _collection(db, uid).document()
    payload = dump_datetimes_for_firestore(recipe.model_dump(mode="python"))
    ref.set(payload)
    snap = ref.get()
    data = deep_convert_firestore_data(snap.to_dict() or {})
    return ref.id, SavedRecipe.model_validate(data)


def delete_saved(db: Any, uid: str, saved_recipe_id: str) -> bool:
    ref = _collection(db, uid).document(saved_recipe_id)
    snap = ref.get()
    if not snap.exists:
        return False
    ref.delete()
    return True


def patch_saved(
    db: Any,
    uid: str,
    saved_recipe_id: str,
    *,
    notes: str | None = None,
    converted_recipe: ConvertedRecipe | None = None,
    original_recipe: OriginalRecipe | None = None,
    source_url: str | None = None,
    source_type: Literal["web", "youtube", "text"] | None = None,
) -> tuple[str, SavedRecipe] | None:
    ref = _collection(db, uid).document(saved_recipe_id)
    snap = ref.get()
    if not snap.exists:
        return None
    current = SavedRecipe.model_validate(deep_convert_firestore_data(snap.to_dict() or {}))
    update: dict = {}
    if notes is not None:
        update["notes"] = notes
    if converted_recipe is not None:
        update["converted_recipe"] = dump_datetimes_for_firestore(
            converted_recipe.model_dump(mode="python")
        )
    if original_recipe is not None:
        update["original_recipe"] = dump_datetimes_for_firestore(
            original_recipe.model_dump(mode="python")
        )
    if source_url is not None:
        update["source_url"] = source_url
    if source_type is not None:
        update["source_type"] = source_type
    if not update:
        return snap.id, current
    ref.update(update)
    snap2 = ref.get()
    data = deep_convert_firestore_data(snap2.to_dict() or {})
    return snap2.id, SavedRecipe.model_validate(data)
