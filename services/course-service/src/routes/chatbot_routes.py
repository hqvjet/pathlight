from fastapi import APIRouter, Depends, HTTPException, status, Request

from schemas.course_schemas import (
    ChatbotQuestionRequest,
    ChatbotQuestionResponse,
    ChatbotAnswerResponse,
)
from controllers.chatbot_controller import ChatbotController
from controllers.course_controller import _verify_token

router = APIRouter(tags=["chatbot"])

@router.post("/question", response_model=ChatbotQuestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_chatbot_question(
    req: Request,
    request: ChatbotQuestionRequest,
):
    user_id = _verify_token(req)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        controller = ChatbotController()
        return controller.submit_question(request=request, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/answer/{chat_id}", response_model=ChatbotAnswerResponse)
async def get_chatbot_answer(
    req: Request,
    chat_id: str,
):
    user_id = _verify_token(req)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        controller = ChatbotController()
        response = controller.get_answer(chat_id=chat_id, user_id=user_id)
        if response.status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.message)
        elif response.status == 403:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=response.message)
        elif response.status == 500:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response.message)
        elif response.status == 202:
            return response
        
        return response
        
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
