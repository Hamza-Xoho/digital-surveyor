import json
import uuid
from typing import Any

from sqlmodel import Session, col, func, select

from app.core.security import get_password_hash, verify_password
from app.models import Assessment, SavedLocation, User, UserCreate, UserUpdate, VehicleProfile


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        # Prevent timing attacks by running password verification even when user doesn't exist
        # This ensures the response time is similar whether or not the email exists
        verify_password(password, DUMMY_HASH)
        return None
    verified, updated_password_hash = verify_password(password, db_user.hashed_password)
    if not verified:
        return None
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user


# --- Assessment CRUD ---


def create_assessment(
    *,
    session: Session,
    owner_id: uuid.UUID,
    postcode: str,
    latitude: float,
    longitude: float,
    easting: float,
    northing: float,
    overall_rating: str,
    results: dict,
) -> Assessment:
    """Persist an assessment result."""
    assessment = Assessment(
        owner_id=owner_id,
        postcode=postcode,
        latitude=latitude,
        longitude=longitude,
        easting=easting,
        northing=northing,
        overall_rating=overall_rating,
        results_json=json.dumps(results),
    )
    session.add(assessment)
    session.commit()
    session.refresh(assessment)
    return assessment


def get_assessment(
    *, session: Session, assessment_id: uuid.UUID
) -> Assessment | None:
    return session.get(Assessment, assessment_id)


def list_assessments(
    *,
    session: Session,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Assessment], int]:
    """List assessments for a user. Returns (items, total_count)."""
    count_stmt = (
        select(func.count())
        .select_from(Assessment)
        .where(Assessment.owner_id == owner_id)
    )
    total = session.exec(count_stmt).one()
    stmt = (
        select(Assessment)
        .where(Assessment.owner_id == owner_id)
        .order_by(col(Assessment.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    items = list(session.exec(stmt).all())
    return items, total


def update_assessment_notes(
    *,
    session: Session,
    assessment_id: uuid.UUID,
    owner_id: uuid.UUID,
    notes: str | None,
) -> Assessment | None:
    """Update notes on an assessment."""
    assessment = session.get(Assessment, assessment_id)
    if not assessment or assessment.owner_id != owner_id:
        return None
    assessment.notes = notes
    session.add(assessment)
    session.commit()
    session.refresh(assessment)
    return assessment


# --- Saved Location CRUD ---


def create_saved_location(
    *,
    session: Session,
    owner_id: uuid.UUID,
    label: str,
    postcode: str,
    latitude: float,
    longitude: float,
    notes: str | None = None,
) -> SavedLocation:
    """Create a saved location."""
    location = SavedLocation(
        owner_id=owner_id,
        label=label,
        postcode=postcode,
        latitude=latitude,
        longitude=longitude,
        notes=notes,
    )
    session.add(location)
    session.commit()
    session.refresh(location)
    return location


def list_saved_locations(
    *,
    session: Session,
    owner_id: uuid.UUID,
) -> list[SavedLocation]:
    """List all saved locations for a user."""
    stmt = (
        select(SavedLocation)
        .where(SavedLocation.owner_id == owner_id)
        .order_by(col(SavedLocation.created_at).desc())
    )
    return list(session.exec(stmt).all())


def get_saved_location(
    *,
    session: Session,
    location_id: uuid.UUID,
) -> SavedLocation | None:
    return session.get(SavedLocation, location_id)


def update_saved_location(
    *,
    session: Session,
    location_id: uuid.UUID,
    owner_id: uuid.UUID,
    label: str | None = None,
    notes: str | None = None,
) -> SavedLocation | None:
    """Update a saved location."""
    location = session.get(SavedLocation, location_id)
    if not location or location.owner_id != owner_id:
        return None
    if label is not None:
        location.label = label
    if notes is not None:
        location.notes = notes
    session.add(location)
    session.commit()
    session.refresh(location)
    return location


def delete_saved_location(
    *,
    session: Session,
    location_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> bool:
    """Delete a saved location. Returns True if deleted."""
    location = session.get(SavedLocation, location_id)
    if not location or location.owner_id != owner_id:
        return False
    session.delete(location)
    session.commit()
    return True


# --- Vehicle Profile CRUD ---


def list_vehicle_profiles(*, session: Session) -> list[VehicleProfile]:
    """List all custom vehicle profiles."""
    stmt = select(VehicleProfile).order_by(col(VehicleProfile.name))
    return list(session.exec(stmt).all())


def get_vehicle_profile(
    *, session: Session, vehicle_id: uuid.UUID
) -> VehicleProfile | None:
    return session.get(VehicleProfile, vehicle_id)


def create_vehicle_profile(
    *,
    session: Session,
    name: str,
    vehicle_class: str,
    width_m: float,
    length_m: float,
    height_m: float,
    weight_kg: int,
    turning_radius_m: float,
    mirror_width_m: float = 0.25,
) -> VehicleProfile:
    """Create a custom vehicle profile."""
    vehicle = VehicleProfile(
        name=name,
        vehicle_class=vehicle_class,
        width_m=width_m,
        length_m=length_m,
        height_m=height_m,
        weight_kg=weight_kg,
        turning_radius_m=turning_radius_m,
        mirror_width_m=mirror_width_m,
    )
    session.add(vehicle)
    session.commit()
    session.refresh(vehicle)
    return vehicle


def delete_vehicle_profile(
    *, session: Session, vehicle_id: uuid.UUID
) -> bool:
    """Delete a custom vehicle profile. Returns True if deleted."""
    vehicle = session.get(VehicleProfile, vehicle_id)
    if not vehicle:
        return False
    session.delete(vehicle)
    session.commit()
    return True
