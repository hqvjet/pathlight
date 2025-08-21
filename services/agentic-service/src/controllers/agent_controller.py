from factories.agent_factory import invoke_course_agent
from schemas.agent_schemas import AgentRequest, AgentResponse

class AgentController:
    def __init__(self):
        pass

    def generate_course(self, request: AgentRequest) -> AgentResponse:
        results = invoke_course_agent(request)
        print(results)
        return results
