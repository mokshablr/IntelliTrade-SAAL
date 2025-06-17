from fastapi import FastAPI
from app.api import routes

fastapi_app = FastAPI()

fastapi_app.include_router(routes.router, prefix="/api")
