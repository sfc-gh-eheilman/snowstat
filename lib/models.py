"""Data models for Snowflake Status API responses."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .config import StatusType


@dataclass
class Component:
    """Represents a Snowflake service component."""

    id: str
    name: str
    status: StatusType
    group_id: str | None
    updated_at: datetime | None
    description: str | None = None
    group: bool = False
    components: list[str] | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Component":
        """Parse Component from API response."""
        # Parse updated_at timestamp
        updated_at = None
        if data.get("updated_at"):
            try:
                from dateutil import parser

                updated_at = parser.parse(data["updated_at"])
            except Exception:
                pass

        # Normalize status to our enum
        status_str = data.get("status", "operational").lower().replace(" ", "_")
        try:
            status = StatusType(status_str)
        except ValueError:
            status = StatusType.OPERATIONAL

        # Parse group and components fields
        group = data.get("group", False)
        components = data.get("components", []) if group else []

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unknown"),
            status=status,
            group_id=data.get("group_id"),
            updated_at=updated_at,
            description=data.get("description"),
            group=group,
            components=components or [],
        )


@dataclass
class IncidentUpdate:
    """Represents an incident update/message."""

    id: str
    status: str
    body: str
    created_at: datetime | None
    display_at: datetime | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "IncidentUpdate":
        """Parse IncidentUpdate from API response."""
        from dateutil import parser

        created_at = None
        display_at = None

        if data.get("created_at"):
            try:
                created_at = parser.parse(data["created_at"])
            except Exception:
                pass

        if data.get("display_at"):
            try:
                display_at = parser.parse(data["display_at"])
            except Exception:
                pass

        return cls(
            id=data.get("id", ""),
            status=data.get("status", ""),
            body=data.get("body", ""),
            created_at=created_at,
            display_at=display_at,
        )


@dataclass
class Incident:
    """Represents a status incident."""

    id: str
    name: str
    status: str
    impact: str
    created_at: datetime | None
    updated_at: datetime | None
    resolved_at: datetime | None
    shortlink: str | None
    updates: list[IncidentUpdate]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Incident":
        """Parse Incident from API response."""
        from dateutil import parser

        created_at = None
        updated_at = None
        resolved_at = None

        if data.get("created_at"):
            try:
                created_at = parser.parse(data["created_at"])
            except Exception:
                pass

        if data.get("updated_at"):
            try:
                updated_at = parser.parse(data["updated_at"])
            except Exception:
                pass

        if data.get("resolved_at"):
            try:
                resolved_at = parser.parse(data["resolved_at"])
            except Exception:
                pass

        updates = [IncidentUpdate.from_api(update) for update in data.get("incident_updates", [])]

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unnamed Incident"),
            status=data.get("status", ""),
            impact=data.get("impact", ""),
            created_at=created_at,
            updated_at=updated_at,
            resolved_at=resolved_at,
            shortlink=data.get("shortlink"),
            updates=updates,
        )


@dataclass
class Maintenance:
    """Represents a scheduled maintenance window."""

    id: str
    name: str
    status: str
    impact: str
    scheduled_for: datetime | None
    scheduled_until: datetime | None
    created_at: datetime | None
    updated_at: datetime | None
    shortlink: str | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Maintenance":
        """Parse Maintenance from API response."""
        from dateutil import parser

        scheduled_for = None
        scheduled_until = None
        created_at = None
        updated_at = None

        for field, var in [
            ("scheduled_for", "scheduled_for"),
            ("scheduled_until", "scheduled_until"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
        ]:
            if data.get(field):
                try:
                    locals()[var] = parser.parse(data[field])
                except Exception:
                    pass

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unnamed Maintenance"),
            status=data.get("status", ""),
            impact=data.get("impact", ""),
            scheduled_for=scheduled_for,
            scheduled_until=scheduled_until,
            created_at=created_at,
            updated_at=updated_at,
            shortlink=data.get("shortlink"),
        )
