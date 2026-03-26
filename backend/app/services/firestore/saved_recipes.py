from typing import Any

from google.cloud.firestore import Query

from app.services.agents.models import ConvertedRecipe, SavedRecipe
from app.services.firestore.timestamps import (
    deep_convert_firestore_data,
    dump_datetimes_for_firestore,
    utc_now,
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
    published: bool | None = None,
    recipe_id: str | None = None,
) -> tuple[str, SavedRecipe] | None:
    ref = _collection(db, uid).document(saved_recipe_id)
    snap = ref.get()
    if not snap.exists:
        return None
    current = SavedRecipe.model_validate(deep_convert_firestore_data(snap.to_dict() or {}))
    if published is True and current.copied_from_saved_recipe_id:
        raise PermissionError("Cannot publish a recipe created by copying a published recipe")
    update: dict = {}
    if notes is not None:
        update["notes"] = notes
    if converted_recipe is not None:
        update["converted_recipe"] = dump_datetimes_for_firestore(
            converted_recipe.model_dump(mode="python")
        )
    if published is not None:
        update["published"] = published
    if recipe_id is not None:
        update["recipe_id"] = recipe_id
    if not update:
        return snap.id, current
    ref.update(update)
    snap2 = ref.get()
    data = deep_convert_firestore_data(snap2.to_dict() or {})
    return snap2.id, SavedRecipe.model_validate(data)


def copy_from_published(
    db: Any,
    uid: str,
    *,
    source_owner_user_id: str,
    source_saved_recipe_id: str,
    notes: str = "",
) -> tuple[str, SavedRecipe]:
    src_ref = (
        db.collection("users")
        .document(source_owner_user_id)
        .collection("saved_recipes")
        .document(source_saved_recipe_id)
    )
    snap = src_ref.get()
    if not snap.exists:
        raise ValueError("Source saved recipe not found")
    raw = deep_convert_firestore_data(snap.to_dict() or {})
    if not raw.get("published"):
        raise ValueError("Source recipe is not published")
    new_recipe = SavedRecipe(
        recipe_id=raw["recipe_id"],
        saved_at=utc_now(),
        notes=notes,
        converted_recipe=(
            ConvertedRecipe.model_validate(raw["converted_recipe"])
            if raw.get("converted_recipe")
            else None
        ),
        published=False,
        copied_from_user_id=source_owner_user_id,
        copied_from_saved_recipe_id=source_saved_recipe_id,
    )
    return create_saved(db, uid, new_recipe)
