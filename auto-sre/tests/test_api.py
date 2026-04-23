"""Integration tests for the FastAPI API routes."""

from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture(autouse=True)
def reset_session() -> None:
    """Ensure a fresh session for every test."""
    import app.routes._session as mod
    mod._session = None


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestResetEndpoint:
    @pytest.mark.asyncio
    async def test_reset_valid_task(self, client: AsyncClient) -> None:
        resp = await client.post("/reset", json={"task_id": "t1_config"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["info"]["task_id"] == "t1_config"
        assert data["observation"]["health_status"] is False

    @pytest.mark.asyncio
    async def test_reset_invalid_task(self, client: AsyncClient) -> None:
        resp = await client.post("/reset", json={"task_id": "nonexistent"})
        assert resp.status_code == 404


class TestStepEndpoint:
    @pytest.mark.asyncio
    async def test_step_without_reset(self, client: AsyncClient) -> None:
        resp = await client.post("/step", json={"tool": "run_command", "arguments": "ls"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["reward"] == pytest.approx(0.01, abs=0.01)

    @pytest.mark.asyncio
    async def test_step_valid_command(self, client: AsyncClient) -> None:
        await client.post("/reset", json={"task_id": "t1_config"})
        resp = await client.post("/step", json={"tool": "run_command", "arguments": "ls /etc/app"})
        assert resp.status_code == 200
        data = resp.json()
        assert "observation" in data
        assert "reward" in data

    @pytest.mark.asyncio
    async def test_step_disallowed_command(self, client: AsyncClient) -> None:
        await client.post("/reset", json={"task_id": "t1_config"})
        resp = await client.post("/step", json={"tool": "run_command", "arguments": "wget evil.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["reward"] == pytest.approx(0.01, abs=0.01)

    @pytest.mark.asyncio
    async def test_solve_t1(self, client: AsyncClient) -> None:
        """Full episode: solve t1_config by renaming the file."""
        await client.post("/reset", json={"task_id": "t1_config"})
        resp = await client.post(
            "/step",
            json={"tool": "run_command", "arguments": "mv /etc/app/conf.bak /etc/app/conf"},
        )
        data = resp.json()
        assert data["reward"] == pytest.approx(0.989, abs=0.01)
        assert data["done"] is True


class TestStateEndpoint:
    @pytest.mark.asyncio
    async def test_state_before_reset(self, client: AsyncClient) -> None:
        resp = await client.get("/state")
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] is None

    @pytest.mark.asyncio
    async def test_state_after_reset(self, client: AsyncClient) -> None:
        await client.post("/reset", json={"task_id": "t2_port"})
        resp = await client.get("/state")
        data = resp.json()
        assert data["task_id"] == "t2_port"
        assert data["step_count"] == 0


class TestFullEpisodes:
    @pytest.mark.asyncio
    async def test_solve_t2_port(self, client: AsyncClient) -> None:
        """Solve t2_port by killing the rogue process on port 8080."""
        await client.post("/reset", json={"task_id": "t2_port"})
        resp = await client.post(
            "/step",
            json={"tool": "run_command", "arguments": "kill -9 512"},
        )
        data = resp.json()
        assert data["reward"] == pytest.approx(0.989, abs=0.01)
        assert data["done"] is True

    @pytest.mark.asyncio
    async def test_solve_t3_dep(self, client: AsyncClient) -> None:
        """Solve t3_dep by running npm install in the app directory."""
        await client.post("/reset", json={"task_id": "t3_dep"})
        # cd into the app directory first
        await client.post(
            "/step",
            json={"tool": "run_command", "arguments": "cd /home/user/app"},
        )
        resp = await client.post(
            "/step",
            json={"tool": "run_command", "arguments": "npm install"},
        )
        data = resp.json()
        assert data["reward"] == pytest.approx(0.989, abs=0.01)
        assert data["done"] is True
