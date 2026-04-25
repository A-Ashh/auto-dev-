"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import reset, step, state, tasks, grader, baseline


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup/shutdown hooks."""
    yield


app = FastAPI(
    title="Auto-SRE OpenEnv",
    description="An OpenEnv-compliant environment for evaluating AI SRE agents on Linux infrastructure repair tasks.",
    version="0.1.0",
    lifespan=lifespan,
    root_path=""
)

# CORS (allow all during development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(reset.router, tags=["Environment"])
app.include_router(step.router, tags=["Environment"])
app.include_router(state.router, tags=["Environment"])
app.include_router(tasks.router, tags=["Environment"])
app.include_router(grader.router, tags=["Environment"])
app.include_router(baseline.router, tags=["Evaluation"])

@app.get("/healthz", tags=["Health"])
async def healthz() -> dict[str, str]:
    """Health-check endpoint."""
    return {"status": "ok", "service": "auto-sre"}


# Mount the Gradio UI at root — FastAPI API routes take priority over Gradio's wildcard
import gradio as gr
from app.ui import demo
app = gr.mount_gradio_app(app, demo, path="/")

def main():
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=7860)
