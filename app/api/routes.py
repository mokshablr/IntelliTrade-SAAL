from fastapi import APIRouter
from pydantic import BaseModel

from app.llm.generate import generate_response
from app.data.ingest import ingest_stock

router = APIRouter()

class LLMRequest(BaseModel):
    user_input: str

class IngestStockData(BaseModel):
    symbol: str
    start: str
    end: str

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


@router.get("/ingest-stock")
def ingest_stock_route(ingest_details: IngestStockData):
    symbol = ingest_details.symbol
    start = ingest_details.start
    end = ingest_details.end

    ingest_stock(symbol, start, end)
    return {"status": "Data ingested successfully"}
