"""Pydantic models for observations and step responses."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class Observation(BaseModel):
    """Snapshot of the terminal and system state after a command."""

    stdout: str = Field(default="", description="Standard output of the executed command")
    stderr: str = Field(default="", description="Standard error of the executed command")
    cwd: str = Field(default="/home/user", description="Current working directory")
    health_status: bool = Field(
        default=False, description="Whether the target service is healthy"
    )


class StepResponse(BaseModel):
    """Full response returned by the /step endpoint."""

    observation: Observation

    # 🔒 CRITICAL FIX: Use plain float (NO RootModel)
    reward: float = Field(
        default=0.01,
        ge=0.01,
        le=0.99,
        description="Reward — strictly in (0, 1), exclusive. Values 0.0 and 1.0 are not allowed."
    )

    done: bool = Field(default=False, description="Whether the episode has ended")
    info: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ResetResponse(BaseModel):
    """Response returned by the /reset endpoint."""

    observation: Observation
    info: dict[str, Any] = Field(default_factory=dict, description="Task metadata")
    state: dict[str, Any] = Field(
        default_factory=dict,
        description="World model snapshot: disk, memory, services, processes"
    )


class StateResponse(BaseModel):
    """Response returned by the /state endpoint (original fields preserved)."""

    task_id: str | None = Field(default=None, description="Active task identifier")
    step_count: int = Field(default=0, description="Steps taken in current episode")
    health_status: bool = Field(default=False, description="Service health")
    is_done: bool = Field(default=False, description="Whether episode is over")


class CommandEntry(BaseModel):
    """A single entry in the command history."""

    command: str = Field(description="The shell command that was run")
    stdout: str = Field(default="", description="Standard output produced")
    stderr: str = Field(default="", description="Standard error produced")


class RichStateResponse(StateResponse):
    """
    Extended /state response — all original StateResponse fields preserved,
    plus rich environment snapshot fields.
    """

    # Task info
    current_task: Optional[str] = Field(default=None, description="Active task ID")
    task_description: Optional[str] = Field(default=None, description="Task description")
    max_steps: int = Field(default=0, description="Maximum steps for the current episode")

    # Environment snapshot
    cwd: str = Field(default="/home/user", description="Current working directory")
    files: list[str] = Field(default_factory=list, description="Visible files in the sandbox")
    processes: list[str] = Field(default_factory=list, description="Simulated running processes")

    # Last command output
    last_command: Optional[str] = Field(default=None, description="Most recent command")
    last_stdout: str = Field(default="", description="Stdout of the most recent command")
    last_stderr: str = Field(default="", description="Stderr of the most recent command")

    # Rolling history
    history: list[CommandEntry] = Field(
        default_factory=list,
        description="Last up-to-10 commands with their outputs",
    )