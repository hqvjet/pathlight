from fastapi import APIRouter
from schemas.agent_schemas import AgentRequest
from schemas.context import State
from controllers.agent_controller import AgentController

router = APIRouter(prefix="/course", tags=["course"])
_controller = AgentController()

@router.post("/generate", response_model=State)
async def generate_course(request: AgentRequest) -> State:
    return await _controller.generate_course(request)
