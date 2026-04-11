from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, council, ws, test_ui

app = FastAPI(title="Hexallabs API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://hexallabs.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(council.router)
app.include_router(ws.router)
app.include_router(test_ui.router)
