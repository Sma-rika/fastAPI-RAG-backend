from pydantic import BaseModel, EmailStr, Field

class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=8000)

class BookingDetails(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    timezone: str = "Asia/Kathmandu"

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    booking_created: bool = False
    booking_id: int | None = None
    sources: list[dict[str, str | int | float]] = Field(default_factory=list)
