"""Lazy Firestore client (requires firebase_admin.initialize_app in app lifespan)."""

from firebase_admin import firestore


def get_firestore_client():
    return firestore.client()
