from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import Booking
from app.schemas.chat import BookingDetails

async def create_booking(db: AsyncSession, session_id: str, details: BookingDetails) -> Booking:
    booking = Booking(
        session_id=session_id, name=details.name, email=str(details.email),
        booking_date=details.date, booking_time=details.time, timezone=details.timezone,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking
