from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from endpoints.audit_endpoint import router as audit_router  # Import from the new location
from db.session import create_db_and_tables
from contextlib import asynccontextmanager # Important for lifespan
from endpoints.user_endpoint import router as register_user_router

# Define your lifespan handler using @asynccontextmanager
@asynccontextmanager
async def lifespan_handler(app: FastAPI): # No 'app' argument needed for the lifespan function itself
    print("Application startup: Creating database tables...")
    create_db_and_tables() # Call the function to create tables
    print("Database tables created.")
    yield
    # Application shutdown (if needed)
    print("Application shutdown complete.")


# Instantiate FastAPI only once, and pass the lifespan handler here
app = FastAPI(title="Elevora", lifespan=lifespan_handler)

# Add CORS middleware configuration here
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your audit endpoint router
# app.include_router(audit_router)
app.include_router(register_user_router)

# Optional: Add a root endpoint to confirm the app is running
@app.get("/")
async def read_root():
    return {"message": "Welcome to Elevora API"}