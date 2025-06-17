from fastapi import APIRouter
from pydantic import BaseModel

from app.llm.generate import generate_response

router = APIRouter()

class LLMRequest(BaseModel):
    user_input: str

@router.get("/")
def welcome():
    return {"message": "Welcome here!"}

@router.post("/generate")
def llm_generate(llm_input: LLMRequest):
    user_input = llm_input.user_input
    response = generate_response(user_input)

    if isinstance(response, str):
        return { "error": response }

    if hasattr(response, "text") and response.text:
        return { "message": response.text }

    return {"error": "Response not generated"}

