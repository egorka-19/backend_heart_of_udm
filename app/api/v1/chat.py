import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import (
    ChatClassifyRequest,
    ChatClassifyResponse,
    ChatMessageCreate,
    ChatMessageOut,
    ChatSessionOut,
)
from app.services.llm import assistant_reply, classify_user_category_from_messages

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/classify-interest", response_model=ChatClassifyResponse)
async def classify_interest(
    payload: ChatClassifyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(deps.get_current_user),
) -> ChatClassifyResponse:
    cat = await classify_user_category_from_messages(payload.messages)
    user.category_user = cat
    db.add(user)
    db.commit()
    return ChatClassifyResponse(category_user=cat)


@router.post("/sessions", response_model=ChatSessionOut, status_code=201)
def create_session(db: Session = Depends(get_db), user: User = Depends(deps.get_current_user)) -> ChatSessionOut:
    s = ChatSession(user_id=user.id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return ChatSessionOut(id=s.id)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
def list_messages(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(deps.get_current_user),
) -> list[ChatMessageOut]:
    s = db.get(ChatSession, session_id)
    if s is None or s.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    msgs = db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
    ).scalars().all()
    return [
        ChatMessageOut(id=m.id, role=m.role, content=m.content, created_at=m.created_at)
        for m in msgs
    ]


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageOut)
async def post_message(
    session_id: uuid.UUID,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(deps.get_current_user),
) -> ChatMessageOut:
    s = db.get(ChatSession, session_id)
    if s is None or s.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    um = ChatMessage(session_id=session_id, role="user", content=payload.content)
    db.add(um)
    db.commit()
    db.refresh(um)

    history = db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
    ).scalars().all()
    summary = "\n".join(f"{m.role}: {m.content}" for m in history)
    answer = await assistant_reply(summary)
    am = ChatMessage(session_id=session_id, role="assistant", content=answer)
    db.add(am)
    db.commit()
    db.refresh(am)
    return ChatMessageOut(id=am.id, role=am.role, content=am.content, created_at=am.created_at)
