"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# existing routes
from auto_sre.app.routes import reset, step, state, tasks, grader, baseline

# 👉 NEW IMPORT
from auto_sre.app.routes import agent

from auto_sre.app.ui import demo

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(
    title="Auto-SRE OpenEnv",
    description="An OpenEnv-compliant environment for evaluating AI SRE agents on Linux infrastructure repair tasks.",
    version="0.1.0",
    lifespan=lifespan,
    root_path=""
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# existing routers
app.include_router(reset.router, tags=["Environment"])
app.include_router(step.router, tags=["Environment"])
app.include_router(state.router, tags=["Environment"])
app.include_router(tasks.router, tags=["Environment"])
app.include_router(grader.router, tags=["Environment"])
app.include_router(baseline.router, tags=["Evaluation"])

# 👉 ADD THIS LINE
app.include_router(agent.router, tags=["Agent"])


@app.get("/healthz", tags=["Health"])
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "auto-sre"}


@app.get("/ping")
def ping():
    return {"msg": "pong"}


# Gradio UI
import gradio as gr
app = gr.mount_gradio_app(app, demo, path="/")


def main():
    import uvicorn
    uvicorn.run("auto_sre.app.main:app", host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
