from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import APIRouter
import logging
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.Chatbot.wrapper_agent import ask_agent 

router = APIRouter(
    tags=["Chatbot"],
    prefix="/chatbot"
)

logger = logging.getLogger(__name__)

class Query(BaseModel):
    query: str

@router.post("/ask")
async def ask(query: Query):
    response = await ask_agent(query.query)
    return {"response": response}