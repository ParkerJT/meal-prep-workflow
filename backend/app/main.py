from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import Settings
from app.routes import auth, test
from firebase_admin import credentials, initialize_app
from contextlib import asynccontextmanager

# Initialize Settings
settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for Firebase initialization"""
    cred_path = settings.FIREBASE_SERVICE_ACCOUNT
    if cred_path and settings.FIREBASE_PROJECT_ID:
        cred = credentials.Certificate(cred_path)
        initialize_app(cred)
        print("Firebase initialized")
    yield
    print("Firebase app shut down")

# Initialize FastAPI app
app = FastAPI(
    title="Meal Prepper API",
    description="Agentic workflow for converting regular recipes into meal prep",
    lifespan=lifespan
)

# Include routes
app.include_router(auth.router)
app.include_router(test.router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # To be replaced with frontend URL
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