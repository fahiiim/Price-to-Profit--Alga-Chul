from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.activity.enums import ActivityAction


class ActivityRead(BaseModel):
    """One entry of the activity log."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int | None = Field(
        description="Business this change belongs to, or null for platform-wide events."
    )
    action: ActivityAction = Field(description="What happened.")
    entity_type: str = Field(
        description="Kind of record that changed.", examples=["quote"]
    )
    entity_id: int | None = Field(description="ID of the record that changed.")
    summary: str = Field(
        description="Readable sentence for the activity feed.",
        examples=["Quote Q-0007 created for Sara Ahmed"],
    )
    created_at: datetime
