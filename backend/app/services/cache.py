"""Shared GeoCache read/write helpers."""

import json
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.core.db import engine
from app.models import GeoCache


def get_cached(cache_key: str) -> dict | None:
    """Look up cached result from GeoCache table."""
    with Session(engine) as session:
        stmt = select(GeoCache).where(GeoCache.cache_key == cache_key)
        cached = session.exec(stmt).first()
        if cached and cached.expires_at > datetime.now(timezone.utc):
            return json.loads(cached.data_json)
    return None


def set_cached(cache_key: str, data: dict, ttl_days: int = 30) -> None:
    """Store result in GeoCache table with TTL."""
    with Session(engine) as session:
        stmt = select(GeoCache).where(GeoCache.cache_key == cache_key)
        existing = session.exec(stmt).first()
        expires = datetime.now(timezone.utc) + timedelta(days=ttl_days)
        if existing:
            existing.data_json = json.dumps(data)
            existing.expires_at = expires
        else:
            session.add(GeoCache(
                cache_key=cache_key,
                data_json=json.dumps(data),
                expires_at=expires,
            ))
        session.commit()


def purge_expired_cache() -> int:
    """Delete all expired cache entries. Returns count of deleted rows."""
    with Session(engine) as session:
        stmt = select(GeoCache).where(GeoCache.expires_at < datetime.now(timezone.utc))
        expired = session.exec(stmt).all()
        count = len(expired)
        for entry in expired:
            session.delete(entry)
        session.commit()
        return count
