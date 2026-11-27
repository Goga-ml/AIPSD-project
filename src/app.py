"""Groundwork's HTTP door.

Run:  uvicorn src.app:app --reload

Lab 5:  POST /act    one question, the tool loop (src/act.py), the answer and every tool call made

Identity comes from the X-Founder header: a stand-in for real sign-in until Week 12. The model never
sees it and cannot change it. No header: a visitor, offered no tool that needs a caller.
"""
from __future__ import annotations

from fastapi import FastAPI, Header
from pydantic import BaseModel, ConfigDict, Field

from .act import act

app = FastAPI(title="Groundwork")


class Ask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=3, max_length=500)


@app.post("/act")
def act_endpoint(body: Ask, x_founder: str | None = Header(default=None, max_length=64)) -> dict:
    return act(body.question, caller=x_founder).to_dict()
