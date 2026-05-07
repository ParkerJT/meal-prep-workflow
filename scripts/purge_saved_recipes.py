"""Purge saved recipes from Firestore users/{uid}/saved_recipes.

Default behavior is dry-run. Use --execute to apply deletes.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from firebase_admin import credentials, firestore, initialize_app

DEFAULT_BATCH_SIZE = 400


def resolve_service_account_path(explicit_path: str | None) -> Path:
    if explicit_path:
        path = Path(explicit_path)
        if path.exists():
            return path
        raise FileNotFoundError(f"Service account file not found: {path}")

    env_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
        raise FileNotFoundError(f"FIREBASE_SERVICE_ACCOUNT points to missing file: {path}")

    fallback = Path("backend/.secrets/firebase-service-account.json")
    if fallback.exists():
        return fallback

    raise FileNotFoundError(
        "No service account found. Provide --service-account or set FIREBASE_SERVICE_ACCOUNT."
    )


def collect_saved_recipe_refs(db: firestore.Client, user_id: str | None) -> list:
    if user_id:
        docs = (
            db.collection("users")
            .document(user_id)
            .collection("saved_recipes")
            .stream()
        )
        return [doc.reference for doc in docs]

    docs = db.collection_group("saved_recipes").stream()
    return [doc.reference for doc in docs]


def chunked(items: list, size: int):
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def main() -> None:
    parser = argparse.ArgumentParser(description="Purge users/*/saved_recipes/* documents.")
    parser.add_argument("--execute", action="store_true", help="Actually delete matched documents.")
    parser.add_argument("--user-id", help="Only purge saved recipes for a specific user uid.")
    parser.add_argument(
        "--service-account",
        help="Path to Firebase service account JSON. Defaults to FIREBASE_SERVICE_ACCOUNT or backend/.secrets fallback.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Max docs per batch commit (default: {DEFAULT_BATCH_SIZE}).",
    )
    args = parser.parse_args()

    if args.batch_size < 1 or args.batch_size > 450:
        raise ValueError("--batch-size must be between 1 and 450")

    cred_path = resolve_service_account_path(args.service_account)
    initialize_app(credentials.Certificate(str(cred_path)))
    db = firestore.client()

    refs = collect_saved_recipe_refs(db, args.user_id)
    total = len(refs)
    mode = "EXECUTE" if args.execute else "DRY-RUN"

    scope = f"user {args.user_id}" if args.user_id else "all users"
    print(f"[{mode}] Matched {total} saved_recipes docs for {scope}.")

    if total == 0:
        return

    if not args.execute:
        preview_count = min(total, 25)
        print(f"[DRY-RUN] Previewing first {preview_count} document paths:")
        for ref in refs[:preview_count]:
            print(f" - {ref.path}")
        if total > preview_count:
            print(f"[DRY-RUN] ...and {total - preview_count} more.")
        print("[DRY-RUN] Re-run with --execute to delete.")
        return

    deleted = 0
    for chunk_index, ref_chunk in enumerate(chunked(refs, args.batch_size), start=1):
        batch = db.batch()
        for ref in ref_chunk:
            batch.delete(ref)
        batch.commit()
        deleted += len(ref_chunk)
        print(f"[EXECUTE] Batch {chunk_index}: deleted {len(ref_chunk)} (total {deleted}/{total})")

    print(f"[EXECUTE] Done. Deleted {deleted} saved_recipes documents.")


if __name__ == "__main__":
    main()
