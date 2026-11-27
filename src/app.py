"""Groundwork's HTTP door.

Run:  uvicorn src.app:app --reload

Lab 5:  POST   /act          one question, the tool loop (src/act.py), the answer and every tool call made
Lab 6:  POST   /chat         one turn, streamed as Server-Sent Events: token, tool, done
        GET    /me/memory    what we hold for this caller: the focus segment and how many recent turns
        DELETE /me/memory    forget it all, now. No model involved; never a tool the model holds

Identity and session come from headers (X-Founder, X-Session-Id): a stand-in for real sign-in until
Week 12. The model never sees either and cannot change them. No X-Founder: a visitor, offered no tool
that needs a caller and given no memory.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from . import memory
from .act import act
from .chat import chat_turn


@asynccontextmanager
async def lifespan(_app):
    memory.expire()                        # lifetimes are enforced, not just declared
    yield


app = FastAPI(title="Groundwork", lifespan=lifespan)


class Ask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=3, max_length=500)


@app.post("/act")
def act_endpoint(body: Ask, x_founder: str | None = Header(default=None, max_length=64)) -> dict:
    return act(body.question, caller=x_founder).to_dict()


def sse(events) -> StreamingResponse:
    """Server-Sent Events: one 'event:' line, one 'data:' line, a blank line."""
    def gen():
        for kind, payload in events:
            data = json.dumps({"text": payload} if kind == "token" else payload)
            yield f"event: {kind}\ndata: {data}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/chat")
def chat(body: Ask, x_session_id: str | None = Header(default=None, max_length=64),
         x_founder: str | None = Header(default=None, max_length=64)) -> StreamingResponse:
    return sse(chat_turn(body.question, session=x_session_id, founder=x_founder))


@app.get("/me/memory")
def my_memory(x_session_id: str | None = Header(default=None, max_length=64),
              x_founder: str | None = Header(default=None, max_length=64)) -> dict:
    return {"focus": memory.focus(x_founder) if x_founder else None,
            "recent_turns": len(memory.recent_turns(x_session_id)) if x_session_id else 0,
            "lifetimes": {"turns": "24 hours", "focus": "30 days"},
            "delete_with": "DELETE /me/memory"}


@app.delete("/me/memory")
def forget_me(x_session_id: str | None = Header(default=None, max_length=64),
              x_founder: str | None = Header(default=None, max_length=64)) -> dict:
    return memory.forget(x_founder, x_session_id)
