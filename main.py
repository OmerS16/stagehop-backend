from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, date

from database import SessionLocal
from models import Event, Venue

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/events/today', response_model=dict)
def read_today_events(db: Session = Depends(get_db)):
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
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    query = db.query(Event).join(Event.venue)

    if date_from:
        query = query.filter(Event.date >= date_from)
    if date_to:
        query = query.filter(Event.date <= date_to)
    if venue_name:
        query = query.filter(Venue.name.ilike(f'%{venue_name}%'))

    events = query.offset(offset).limit(limit).all()
    return to_geojson(events)


@app.get('/venues')
def get_venues(db: Session = Depends(get_db)):
    venues = db.query(Venue).all()
    return [
        {
            'id': v.id,
            'name': v.name,
            'lat': v.lat,
            'lon': v.lon,
        }
        for v in venues
    ]

@app.get('/ping')
def ping():
    return {'status': 'ok'}

def to_geojson(events):
    geojson = {
        'type': 'FeatureCollection',
        'features': []
    }

    for e in events:
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
                    }
                }
            })

    return geojson
