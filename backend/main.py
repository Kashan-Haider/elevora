from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.session import create_db_and_tables
from contextlib import asynccontextmanager
from endpoints.user.routes import router as user_router
from endpoints.project.routes import router as project_router

@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    print("Application startup: Creating database tables...")
    create_db_and_tables()
    print("Database tables created.")
    yield
    print("Application shutdown complete.")

app = FastAPI(title="Elevora", lifespan=lifespan_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(project_router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to Elevora API"}