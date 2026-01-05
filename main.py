from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from firebase.firebase_init import initialize_firebase
from routes import router

# Initialize Firebase
print("--- Starting API ---")
try:
    initialize_firebase()
    print("--- Firebase Initialized ---")
except Exception as e:
    print(f"--- Firebase Failed: {e} ---")

# Create FastAPI app
app = FastAPI(
    title="Joke API",
    description="FastAPI service with Firebase authentication for joke management",
    version="1.0.0"
)

# Add CORS middleware to allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the UI
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(router, prefix="/api", tags=["api"])

@app.get("/")
async def root():
    return {"message": "Joke API is running", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import google.generativeai as genai
    from firebase.config import GEMINI_API_KEY
    
    # Configure Gemini API
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # List all available models
        print("\n=== Available Gemini Models ===")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model Name: {m.name}")
        print("===============================\n")
    else:
        print("Warning: GEMINI_API_KEY not set. Cannot list models.")

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

