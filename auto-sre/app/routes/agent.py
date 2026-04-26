from fastapi import APIRouter
from auto_sre.agent.model import predict

router = APIRouter()


@router.post("/agent/action", tags=["Agent"])
async def agent_action(observation: dict):
    """
    Given environment observation, return next action from trained RL agent
    """
    action = predict(observation)
    return {"action": action}
