"""Pydantic schemas for public service catalog (US-002)."""

from pydantic import BaseModel, ConfigDict

from app.models.service import Gender, ServiceType


class ServicePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: ServiceType
    gender: Gender
    base_duration_minutes: int
