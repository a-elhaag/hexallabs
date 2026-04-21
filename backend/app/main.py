from __future__ import annotations

from fastapi import FastAPI

from app.api.debug import router as debug_router

app = FastAPI(title="Hexal-LM Backend", version="0.1.0")
app.include_router(debug_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
