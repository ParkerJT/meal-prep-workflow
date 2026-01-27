from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import Settings
from app.routes import auth, test

# Initialize Settings
settings = Settings()

# Initialize FastAPI app
app = FastAPI(
    title="Meal Prepper API",
    description="Agentic workflow for converting regular recipes into meal prep"
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