import logging

import httpx
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from .database import create_conversation, create_message, init_db, list_conversations, list_messages
from .llm import OllamaResponseError, generate_assistant_reply

app = FastAPI(title="AI Chat Test API")
logger = logging.getLogger(__name__)


class MessageCreate(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1)


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class ChatOut(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation_endpoint() -> ConversationOut:
    data = create_conversation()
    return ConversationOut(**data)


@app.get("/conversations")
def list_conversations_endpoint() -> list[ConversationOut]:
    rows = list_conversations()
    return [ConversationOut(**row) for row in rows]


@app.get("/conversations/{conversation_id}/messages")
def list_messages_endpoint(conversation_id: str) -> list[MessageOut]:
    try:
        rows = list_messages(conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return [MessageOut(**row) for row in rows]


@app.post("/conversations/{conversation_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def create_message_endpoint(conversation_id: str, payload: MessageCreate) -> MessageOut:
    try:
        data = create_message(conversation_id, payload.role, payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return MessageOut(**data)


@app.post("/conversations/{conversation_id}/chat", response_model=ChatOut)
def chat_endpoint(conversation_id: str, payload: ChatRequest) -> ChatOut:
    try:
        user_message = create_message(conversation_id, "user", payload.content)
        history = list_messages(conversation_id)
        assistant_content = generate_assistant_reply(
            [{"role": message["role"], "content": message["content"]} for message in history]
        )
        assistant_message = create_message(conversation_id, "assistant", assistant_content)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (httpx.HTTPError, OllamaResponseError) as exc:
        logger.exception("Failed to get a response from Ollama")
        raise HTTPException(status_code=502, detail="Failed to get a response from Ollama") from exc

    return ChatOut(
        user_message=MessageOut(**user_message),
        assistant_message=MessageOut(**assistant_message),
    )
