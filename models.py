from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    lat = Column(Float)
    lon = Column(Float)

    events = relationship("Event", back_populates="venue")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    show_name = Column(String)
    date = Column(DateTime)
    link = Column(String)
    img = Column(String)
    venue_id = Column(Integer, ForeignKey("venues.id"))

    venue = relationship("Venue", back_populates="events")
