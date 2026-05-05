import base64
from typing import Any

from google.cloud.firestore import Query

from app.services.agents.models import SavedRecipe
from app.services.firestore.timestamps import deep_convert_firestore_data


def encode_cursor(owner_user_id: str, saved_recipe_id: str) -> str:
    raw = f"{owner_user_id}::{saved_recipe_id}".encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[str, str]:
    pad = "=" * (-len(cursor) % 4)
    raw = base64.urlsafe_b64decode(cursor + pad).decode()
    owner_user_id, saved_recipe_id = raw.split("::", 1)
    return owner_user_id, saved_recipe_id


def _parse_saved_recipes_path(path: str) -> tuple[str, str] | None:
    # users/{uid}/saved_recipes/{doc_id}
    parts = path.split("/")
    if len(parts) != 4 or parts[0] != "users" or parts[2] != "saved_recipes":
        return None
    return parts[1], parts[3]


def list_published(
    db: Any,
    *,
    limit: int,
    cursor: str | None,
    exclude_owner_user_id: str | None = None,
) -> tuple[list[dict], str | None]:
    """
    Returns rows with owner_user_id, saved_recipe_id, saved_at, converted_recipe (no notes).
    next_cursor is the cursor for the next page (last item of this page), or None.
    """
    q = (
        db.collection_group("saved_recipes")
        .where("published", "==", True)
        .order_by("saved_at", direction=Query.DESCENDING)
        .limit(limit + 1)
    )
    if cursor:
        owner_uid, sid = decode_cursor(cursor)
        cur_snap = (
            db.collection("users")
            .document(owner_uid)
            .collection("saved_recipes")
            .document(sid)
            .get()
        )
        if cur_snap.exists:
            q = q.start_after(cur_snap)

    docs = list(q.stream())
    has_more = len(docs) > limit
    page = docs[:limit]

    rows: list[dict] = []
    last_owner: str | None = None
    last_sid: str | None = None
    for doc in page:
        parsed = _parse_saved_recipes_path(doc.reference.path)
        if not parsed:
            continue
        owner_user_id, saved_recipe_id = parsed
        data = deep_convert_firestore_data(doc.to_dict() or {})
        data.pop("notes", None)
        sr = SavedRecipe.model_validate(data)
        if exclude_owner_user_id and owner_user_id == exclude_owner_user_id:
            continue
        rows.append(
            {
                "owner_user_id": owner_user_id,
                "saved_recipe_id": saved_recipe_id,
                "saved_at": sr.saved_at,
                "converted_recipe": sr.converted_recipe,
            }
        )
        last_owner = owner_user_id
        last_sid = saved_recipe_id

    next_cursor: str | None = None
    if has_more and last_owner and last_sid:
        next_cursor = encode_cursor(last_owner, last_sid)

    return rows, next_cursor


def get_published_detail(
    db: Any,
    owner_user_id: str,
    saved_recipe_id: str,
) -> dict | None:
    snap = (
        db.collection("users")
        .document(owner_user_id)
        .collection("saved_recipes")
        .document(saved_recipe_id)
        .get()
    )
    if not snap.exists:
        return None
    data = deep_convert_firestore_data(snap.to_dict() or {})
    if not data.get("published"):
        return None
    data.pop("notes", None)
    sr = SavedRecipe.model_validate(data)
    return {
        "owner_user_id": owner_user_id,
        "saved_recipe_id": saved_recipe_id,
        "saved_at": sr.saved_at,
        "converted_recipe": sr.converted_recipe,
        "recipe_id": sr.recipe_id,
    }
