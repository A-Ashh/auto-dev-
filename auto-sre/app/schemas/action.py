"""Pydantic models for agent actions (request payloads)."""

from pydantic import BaseModel, Field


class DevOpsAction(BaseModel):
    """An action submitted by the AI agent."""

    tool: str = Field(
        ...,
        description="Tool identifier, e.g. 'run_command'",
        examples=["run_command"],
    )
    arguments: str = Field(
        ...,
        description="The shell command string to execute",
        examples=["ls -la /etc/app", "mv conf.bak conf"],
    )


class ResetRequest(BaseModel):
    """Request body for the /reset endpoint."""

    task_id: str | None = Field(
        default=None,
        description="Identifier of the task scenario to load",
        examples=["t1_config", "t2_port", "t3_dep"],
    )
