"""API client for Snowflake Status API."""

from datetime import datetime, timedelta
from typing import Any

import requests
import streamlit as st

from .config import API_BASE_URL, API_TIMEOUT, CACHE_TTL
from .models import Component, Incident, Maintenance


class SnowflakeStatusAPI:
    """Client for interacting with Snowflake Status API."""

    def __init__(self, base_url: str = API_BASE_URL, timeout: int = API_TIMEOUT):
        """Initialize API client."""
        self.base_url = base_url
        self.timeout = timeout

    def _get(self, endpoint: str) -> dict[str, Any] | None:
        """Make GET request to API endpoint with error handling."""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            st.error(f"Request timed out after {self.timeout} seconds")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return None
        except ValueError as e:
            st.error(f"Failed to parse API response: {str(e)}")
            return None

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def get_summary(_self) -> dict[str, Any] | None:
        """Get status summary including components and incidents."""
        return _self._get("summary.json")

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def get_components(_self) -> list[Component]:
        """Get all components with status information."""
        data = _self._get("components.json")
        if not data or "components" not in data:
            return []

        components = []
        for comp_data in data["components"]:
            try:
                components.append(Component.from_api(comp_data))
            except Exception:
                continue  # Skip malformed components

        return components

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def get_incidents(_self, days: int = 30) -> list[Incident]:
        """Get incidents from the last N days."""
        data = _self._get("incidents.json")
        if not data or "incidents" not in data:
            return []

        # Filter to incidents within time window
        cutoff = datetime.now() - timedelta(days=days)
        incidents = []

        for inc_data in data["incidents"]:
            try:
                incident = Incident.from_api(inc_data)
                # Include if created within time window or still unresolved
                if (
                    incident.created_at
                    and incident.created_at >= cutoff
                    or incident.resolved_at is None
                ):
                    incidents.append(incident)
            except Exception:
                continue

        # Sort by created_at descending (most recent first)
        incidents.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
        return incidents

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def get_active_maintenance(_self) -> list[Maintenance]:
        """Get active maintenance windows."""
        data = _self._get("scheduled-maintenances/active.json")
        if not data or "scheduled_maintenances" not in data:
            return []

        maintenances = []
        for maint_data in data["scheduled_maintenances"]:
            try:
                maintenances.append(Maintenance.from_api(maint_data))
            except Exception:
                continue

        return maintenances

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def get_upcoming_maintenance(_self) -> list[Maintenance]:
        """Get upcoming maintenance windows."""
        data = _self._get("scheduled-maintenances/upcoming.json")
        if not data or "scheduled_maintenances" not in data:
            return []

        maintenances = []
        for maint_data in data["scheduled_maintenances"]:
            try:
                maintenances.append(Maintenance.from_api(maint_data))
            except Exception:
                continue

        return maintenances

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def get_all_maintenance(_self) -> list[Maintenance]:
        """Get all recent maintenance windows."""
        data = _self._get("scheduled-maintenances.json")
        if not data or "scheduled_maintenances" not in data:
            return []

        maintenances = []
        for maint_data in data["scheduled_maintenances"]:
            try:
                maintenances.append(Maintenance.from_api(maint_data))
            except Exception:
                continue

        # Sort by scheduled_for descending
        maintenances.sort(
            key=lambda x: x.scheduled_for or datetime.min,
            reverse=True,
        )
        return maintenances
