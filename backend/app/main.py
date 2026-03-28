import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import Settings
from app.routes import auth, original_recipes, published_recipes, saved_recipes, workflow
from firebase_admin import credentials, initialize_app
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Initialize Settings
settings = Settings()

# Backend directory (parent of app/) — used to resolve relative credential paths
_BACKEND_DIR = Path(__file__).resolve().parent.parent


def _resolve_cred_path(cred_path: str) -> Path | None:
    """Resolve credential path. Works whether running from project root or backend/."""
    if not cred_path:
        return None
    p = Path(cred_path)
    if p.is_absolute() and p.exists():
        return p
    if p.exists():
        return p
    # Try relative to backend dir (e.g. env has "backend/.secrets/..." but cwd is backend/)
    fallback = _BACKEND_DIR / ".secrets" / "firebase-service-account.json"
    return fallback if fallback.exists() else p


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for Firebase initialization"""
    cred_path = settings.FIREBASE_SERVICE_ACCOUNT
    if cred_path and settings.FIREBASE_PROJECT_ID:
        resolved = _resolve_cred_path(cred_path)
        if not resolved or not resolved.exists():
            raise FileNotFoundError(
                f"Firebase service account not found. Tried: {cred_path} and {_BACKEND_DIR / '.secrets' / 'firebase-service-account.json'}"
            )
        cred = credentials.Certificate(str(resolved))
        initialize_app(cred)
        logger.info("Firebase initialized")
    yield
    logger.info("Firebase app shut down")

# Initialize FastAPI app
app = FastAPI(
    title="Meal Prepper API",
    description="Agentic workflow for converting regular recipes into meal prep",
    lifespan=lifespan
)

# Include routes
app.include_router(auth.router)
app.include_router(published_recipes.router)
app.include_router(original_recipes.router)
app.include_router(saved_recipes.router)
app.include_router(workflow.router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Meal Prepper API is running", "docs": "/docs"}

@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running"""
    return {"status": "healthy", "service": "meal-prepper-api"}