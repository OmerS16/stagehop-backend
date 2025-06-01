from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, date

from database import SessionLocal
from models import Event, Venue

app = FastAPI()

# Allow cross-origin requests from any origin (useful for frontend apps)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

def get_db():
    """
    Dependency that provides a database session and ensures it is closed after use.
    Yield:
        Session: a SQLAlchemy database session
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/events/today', response_model=dict)
def read_today_events(db: Session = Depends(get_db)):
    """
    Retrieve events happening today. If no events are found for today,
    fall back to events in the next three days.

    Args:
        db (Session): Database session injected via get_db dependency.

    Returns:
        dict: GeoJSON FeatureCollection of matching events.
    """

    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())

    # Try today's events
    events = (
        db.query(Event)
        .join(Event.venue)
        .filter(Event.date >= start, Event.date <= end)
        .all()
    )

    if not events:
        # Fallback: next 3 days
        end = start + timedelta(days=3)
        events = (
            db.query(Event)
            .join(Event.venue)
            .filter(Event.date >= start, Event.date <= end)
            .all()
        )

    return to_geojson(events)


@app.get('/events', response_model=dict)
def read_filtered_events(
    db: Session = Depends(get_db),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    venue_name: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=20),
    offset: int = Query(0, ge=0)
):
    """
    Retrieve events filtered by optional date range and/or venue name,
    with pagination support.

    Args:
        db (Session): Database session injected via get_db dependency.
        date_from (datetime, optional): Include events on or after this date.
        date_to (datetime, optional): Include events on or before this date.
        venue_name (str, optional): Filter events by venue name (case-insensitive, substring).
        limit (int): Maximum number of events to return (1–20).
        offset (int): Number of events to skip before collecting results.

    Returns:
        dict: GeoJSON FeatureCollection of matching events.
    """

    query = db.query(Event).join(Event.venue)

    if date_from:
        query = query.filter(Event.date >= date_from)
        
    # If date_from provided but date_to omitted, default date_to to end of date_from
    if date_from and not date_to:
        date_to = datetime.combine(date_from.date(), datetime.max.time())

    if date_to:
        query = query.filter(Event.date <= date_to)
    
    # Use case-insensitive match on Venue.name
    if venue_name:
        query = query.filter(Venue.name.ilike(f'%{venue_name}%'))

    # Apply pagination
    events = query.offset(offset).limit(limit).all()

    return to_geojson(events)


@app.get('/venues')
def get_venues(db: Session = Depends(get_db)):
    """
    Retrieve all venues stored in the database.

    Args:
        db (Session): Database session injected via get_db dependency.

    Returns:
        list: A list of venue dicts with keys 'id', 'name', 'lat', 'lon', 'logo'.
    """

    venues = db.query(Venue).all()
    return [
        {
            'id': v.id,
            'name': v.name,
            'lat': v.lat,
            'lon': v.lon,
            'logo': v.logo
        }
        for v in venues
    ]

@app.get('/ping')
def ping():
    """
    Simple health-check endpoint.

    Returns:
        dict: {'status': 'ok'} if the service is up.
    """

    return {'status': 'ok'}

def to_geojson(events):
    """
    Convert a list of Event ORM objects into a GeoJSON FeatureCollection.

    Only include events whose associated venue has latitude and longitude.

    Args:
        events (list[Event]): List of Event ORM instances.

    Returns:
        dict: GeoJSON FeatureCollection with event features.
    """

    geojson = {
        'type': 'FeatureCollection',
        'features': []
    }

    for e in events:
        # Only include events where venue coordinates are present
        if e.venue and e.venue.lat is not None and e.venue.lon is not None:
            geojson['features'].append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [e.venue.lon, e.venue.lat]
                },
                'properties': {
                    'id': e.id,
                    'show_name': e.show_name,
                    'date': e.date.isoformat() if e.date else None,
                    'link': e.link,
                    'img': e.img,
                    'venue': {
                        'id': e.venue.id,
                        'name': e.venue.name,
                        'logo': e.venue.logo
                    }
                }
            })

    return geojson
