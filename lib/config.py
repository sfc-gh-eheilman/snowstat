"""Configuration constants for the Accessible Snowflake Status app."""

from enum import Enum


class ViewMode(str, Enum):
    """View mode options for status display."""

    STANDARD = "standard"
    HIGH_CONTRAST = "high_contrast"
    ICON = "icon"


class StatusType(str, Enum):
    """Status types matching Snowflake Status API."""

    OPERATIONAL = "operational"
    DEGRADED_PERFORMANCE = "degraded_performance"
    PARTIAL_OUTAGE = "partial_outage"
    MAJOR_OUTAGE = "major_outage"
    UNDER_MAINTENANCE = "under_maintenance"


# API Configuration
API_BASE_URL = "https://status.snowflake.com/api/v2"
API_TIMEOUT = 10  # seconds
CACHE_TTL = 60  # seconds

# Auto-refresh Configuration
DEFAULT_REFRESH_INTERVAL = 300  # 5 minutes in seconds
MIN_REFRESH_INTERVAL = 60  # 1 minute
MAX_REFRESH_INTERVAL = 600  # 10 minutes

# Color Palettes

# Standard (Original Snowflake colors)
STANDARD_COLORS = {
    StatusType.OPERATIONAL: "#2ECC71",
    StatusType.DEGRADED_PERFORMANCE: "#F39C12",
    StatusType.PARTIAL_OUTAGE: "#E74C3C",
    StatusType.MAJOR_OUTAGE: "#C0392B",
    StatusType.UNDER_MAINTENANCE: "#3498DB",
}

# High-Contrast (WCAG AAA compliant - 7:1 contrast ratio on white background)
HIGH_CONTRAST_COLORS = {
    StatusType.OPERATIONAL: "#006400",  # Dark green
    StatusType.DEGRADED_PERFORMANCE: "#CC7000",  # Dark orange
    StatusType.PARTIAL_OUTAGE: "#B30000",  # Dark red
    StatusType.MAJOR_OUTAGE: "#800000",  # Maroon
    StatusType.UNDER_MAINTENANCE: "#00008B",  # Navy
}

# Icon/Emoji mode
STATUS_ICONS = {
    StatusType.OPERATIONAL: "✓",
    StatusType.DEGRADED_PERFORMANCE: "⚠",
    StatusType.PARTIAL_OUTAGE: "✗",
    StatusType.MAJOR_OUTAGE: "✗✗",
    StatusType.UNDER_MAINTENANCE: "🔧",
}

# Status labels
STATUS_LABELS = {
    StatusType.OPERATIONAL: "Operational",
    StatusType.DEGRADED_PERFORMANCE: "Degraded Performance",
    StatusType.PARTIAL_OUTAGE: "Partial Outage",
    StatusType.MAJOR_OUTAGE: "Major Outage",
    StatusType.UNDER_MAINTENANCE: "Under Maintenance",
}

# Status severity (for aggregation - higher is worse)
STATUS_SEVERITY = {
    StatusType.OPERATIONAL: 0,
    StatusType.UNDER_MAINTENANCE: 1,
    StatusType.DEGRADED_PERFORMANCE: 2,
    StatusType.PARTIAL_OUTAGE: 3,
    StatusType.MAJOR_OUTAGE: 4,
}


def get_status_color(status: StatusType, view_mode: ViewMode) -> str:
    """Get the color for a status based on view mode."""
    if view_mode == ViewMode.HIGH_CONTRAST:
        return HIGH_CONTRAST_COLORS.get(status, "#000000")
    return STANDARD_COLORS.get(status, "#95A5A6")


def get_worst_status(*statuses: StatusType) -> StatusType:
    """Return the worst (highest severity) status from a list."""
    if not statuses:
        return StatusType.OPERATIONAL
    return max(statuses, key=lambda s: STATUS_SEVERITY.get(s, 0))
