"""Utility functions for data processing and formatting."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import yaml

from .config import StatusType
from .models import Component

# Legacy parsing functions (kept for backward compatibility and tests)
# NOTE: These are replaced by build_status_matrix for the new group-based API structure


def parse_component_info(component: Component) -> tuple[str | None, str | None, str | None]:
    """
    LEGACY: Extract cloud, region, and service from component name.

    NOTE: This function is deprecated in favor of the new group-based parsing.
    Kept for backward compatibility and existing tests.

    Returns: (cloud, region, service)
    Examples:
        "AWS - US West (Oregon) - Virtual Warehouses"
            -> ("AWS", "US West (Oregon)", "Virtual Warehouses")
        "Azure - West Europe" -> ("Azure", "West Europe", None)
    """
    name = component.name

    # Try to match pattern: Cloud - Region - Service
    match = re.match(r"^(AWS|Azure|GCP)\s*-\s*([^-]+?)(?:\s*-\s*(.+))?$", name, re.IGNORECASE)
    if match:
        cloud = match.group(1).upper()
        region = match.group(2).strip()
        service = match.group(3).strip() if match.group(3) else None
        return cloud, region, service

    # Fallback: try to identify cloud anywhere in name
    cloud = None
    for c in ["AWS", "Azure", "GCP"]:
        if c.lower() in name.lower():
            cloud = c.upper()
            break

    return cloud, None, None


def group_components_by_cloud(
    components: list[Component],
) -> dict[str, dict[str, dict[str, list[Component]]]]:
    """
    LEGACY: Group components by cloud -> region -> service.

    NOTE: This function is deprecated in favor of build_status_matrix.
    Kept for backward compatibility.

    Returns: {cloud: {region: {service: [components]}}}
    """
    grouped: dict[str, dict[str, dict[str, list[Component]]]] = {}

    for comp in components:
        cloud, region, service = parse_component_info(comp)

        if not cloud or not region:
            continue  # Skip components we can't place

        if cloud not in grouped:
            grouped[cloud] = {}
        if region not in grouped[cloud]:
            grouped[cloud][region] = {}

        service_key = service or "Other"
        if service_key not in grouped[cloud][region]:
            grouped[cloud][region][service_key] = []

        grouped[cloud][region][service_key].append(comp)

    return grouped


def format_timestamp(dt: datetime | None, relative: bool = True) -> str:
    """
    Format datetime in user's local timezone.

    Args:
        dt: Datetime to format
        relative: If True, show relative time for recent timestamps

    Returns: Formatted string like "2 minutes ago" or "2024-01-15 10:30 AM PST"
    """
    if dt is None:
        return "Unknown"

    # Convert to local timezone
    local_dt = dt.astimezone()

    if relative:
        now = datetime.now(UTC).astimezone()
        delta = now - local_dt

        if delta.days < 0:
            return local_dt.strftime("%b %d, %Y %I:%M %p %Z")

        if delta.days == 0:
            if delta.seconds < 60:
                return "Just now"
            elif delta.seconds < 3600:
                mins = delta.seconds // 60
                return f"{mins} minute{'s' if mins != 1 else ''} ago"
            else:
                hours = delta.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif delta.days == 1:
            return "Yesterday"
        elif delta.days < 7:
            return f"{delta.days} days ago"

    return local_dt.strftime("%b %d, %Y %I:%M %p %Z")


def aggregate_component_status(components: list[Component]) -> StatusType:
    """
    Get the worst status from a list of components.

    Args:
        components: List of components to aggregate

    Returns: Worst StatusType from the list
    """
    from .config import get_worst_status

    if not components:
        return StatusType.OPERATIONAL

    statuses = [comp.status for comp in components]
    return get_worst_status(*statuses)


# New parsing functions for group-based API structure


def build_component_lookup(components: list[Component]) -> dict[str, Component]:
    """Create ID->Component mapping for fast lookups."""
    return {comp.id: comp for comp in components}


def extract_cloud_from_name(name: str) -> str | None:
    """Extract cloud provider from region name."""
    match = re.match(r"^(AWS|Azure|GCP)\s*-", name, re.IGNORECASE)
    return match.group(1).upper() if match else None


def build_status_matrix(
    components: list[Component],
) -> dict[str, dict[str, dict[str, Component]]]:
    """
    Build matrix structure: {cloud: {region: {service: Component}}}.

    Uses group components as regions, resolves child IDs to get services.
    """
    lookup = build_component_lookup(components)
    matrix: dict[str, dict[str, dict[str, Component]]] = {}

    regions = [c for c in components if c.group]

    for region in regions:
        cloud = extract_cloud_from_name(region.name)
        if not cloud:
            continue

        if cloud not in matrix:
            matrix[cloud] = {}

        region_name = region.name
        matrix[cloud][region_name] = {}

        if region.components:
            for comp_id in region.components:
                service_comp = lookup.get(comp_id)
                if service_comp:
                    service_name = service_comp.name
                    matrix[cloud][region_name][service_name] = service_comp

    return matrix


# Service ordering (canonical + unknowns)

_DEF_SERVICES_PATH = Path(".streamlit/services_order.yaml")


def load_canonical_services(path: Path = _DEF_SERVICES_PATH) -> list[str]:
    """Load canonical services list from YAML; returns empty list on failure."""
    try:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        services = data.get("services", [])
        return [s for s in services if isinstance(s, str) and s.strip()]
    except Exception:
        return []


def order_services(all_services: Iterable[str]) -> list[str]:
    """
    Return services ordered with canonical first, then unknown services appended alphabetically.
    """
    canonical = load_canonical_services()
    seen = set()

    # Preserve canonical order (exact string match only)
    ordered: list[str] = []
    for s in canonical:
        if s in all_services:
            ordered.append(s)
            seen.add(s)

    # Append unknowns alphabetically at the end
    unknowns = sorted([s for s in all_services if s not in seen])
    ordered.extend(unknowns)
    return ordered
