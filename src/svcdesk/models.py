# ai-generated: 100% - Codex implemented the Lab 1 request validation model from API.md
from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints


ShortText = Annotated[str, StringConstraints(min_length=1, max_length=100)]
TitleText = Annotated[str, StringConstraints(min_length=1, max_length=200)]
DescriptionText = Annotated[str, StringConstraints(max_length=4000)]
Level = Annotated[StrictInt, Field(ge=1, le=3)]


class ReporterInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: ShortText
    email: str | None = None
    vip: bool = False


class TicketInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: TitleText
    description: DescriptionText = ""
    reporter: ReporterInput
    impact: Level
    urgency: Level
    related_to: str | None = None
