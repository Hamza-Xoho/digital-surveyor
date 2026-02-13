"""Shared GeoCache read/write helpers."""

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.core.db import engine
from app.models import GeoCache

logger = logging.getLogger(__name__)


def get_cached(cache_key: str) -> dict | None:
    """Look up cached result from GeoCache table."""
    with Session(engine) as session:
        stmt = select(GeoCache).where(GeoCache.cache_key == cache_key)
        cached = session.exec(stmt).first()
        if cached and cached.expires_at > datetime.now(timezone.utc):
            return json.loads(cached.data_json)
    return None


def set_cached(cache_key: str, data: dict, ttl_days: int = 30) -> None:
    """Store result in GeoCache table with TTL.

    Uses retry to handle race conditions when concurrent requests
    try to cache the same key simultaneously.
    """
    expires = datetime.now(timezone.utc) + timedelta(days=ttl_days)
    data_str = json.dumps(data)

    for attempt in range(2):
        try:
            with Session(engine) as session:
                stmt = select(GeoCache).where(GeoCache.cache_key == cache_key)
                existing = session.exec(stmt).first()
                if existing:
                    existing.data_json = data_str
                    existing.expires_at = expires
                else:
                    session.add(GeoCache(
                        cache_key=cache_key,
                        data_json=data_str,
                        expires_at=expires,
                    ))
                session.commit()
                return
        except Exception:
            if attempt == 0:
                logger.debug("Cache write conflict for %s, retrying", cache_key)
                continue
            logger.warning("Cache write failed for %s after retry", cache_key)


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
