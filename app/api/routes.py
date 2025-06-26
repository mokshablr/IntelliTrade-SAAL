from fastapi import APIRouter
from pydantic import BaseModel

from app.llm.generate import generate_response
from app.data.ingest import ingest_stock, ingest_crypto

router = APIRouter()

class LLMRequest(BaseModel):
    user_input: str

class IngestStockData(BaseModel):
    symbol: str
    interval: str

class IngestCryptoData(BaseModel):
    symbol: str
    interval: str

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
    interval = ingest_details.interval
    # outputsize = ingest_details.outputsize
    outputsize = "compact"
    ingest_stock(symbol, interval, outputsize)
    return {"status": "Stock data ingested successfully"}

@router.get("/ingest-crypto")
def ingest_crypto_route(ingest_details: IngestCryptoData):
    symbol = ingest_details.symbol
    interval = ingest_details.interval
    ingest_crypto(symbol, interval)
    return {"status": "Crypto data ingested successfully"}
