"""Reusable UI components for the Streamlit app."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from .config import (
    STATUS_ICONS,
    STATUS_LABELS,
    StatusType,
    ViewMode,
    get_status_color,
)
from .models import Component, Incident, Maintenance
from .utils import format_timestamp, order_services


def render_status_indicator(
    status: StatusType,
    view_mode: ViewMode,
    show_label: bool = True,
    size: str = "normal",
    tooltip: str | None = None,
) -> None:
    """
    Render a status indicator based on view mode.

    Args:
        status: Status to display
        view_mode: Current view mode (standard/high_contrast/icon)
        show_label: Whether to show text label
        size: Size of indicator ("small", "normal", "large")
        tooltip: Optional tooltip text to show on hover
    """
    label = STATUS_LABELS.get(status, "Unknown")

    if view_mode == ViewMode.ICON:
        icon = STATUS_ICONS.get(status, "?")
        icon_size = {"small": "1.0rem", "normal": "1.2rem", "large": "1.5rem"}[size]
        tooltip_attr = f' title="{tooltip}"' if tooltip else ""
        st.markdown(
            f'<span style="font-size: {icon_size}; cursor: help;"{tooltip_attr}>'
            f"{icon}</span> {label if show_label else ''}",
            unsafe_allow_html=True,
        )
    else:
        color = get_status_color(status, view_mode)
        dot_size = {"small": "8px", "normal": "12px", "large": "16px"}[size]
        tooltip_attr = f' title="{tooltip}"' if tooltip else ""
        st.markdown(
            f'<span style="display:inline-block;width:{dot_size};height:{dot_size};'
            f"background-color:{color};border-radius:50%;margin-right:8px;"
            f'vertical-align:middle;cursor:help;"{tooltip_attr}></span>'
            f"{label if show_label else ''}",
            unsafe_allow_html=True,
        )


def render_status_legend(view_mode: ViewMode) -> None:
    """
    Render legend showing all status types with their indicators.

    Args:
        view_mode: Current view mode to determine how to display indicators
    """
    st.markdown("### Status Legend")

    # Create columns for legend items
    cols = st.columns(5)

    statuses = [
        StatusType.OPERATIONAL,
        StatusType.DEGRADED_PERFORMANCE,
        StatusType.PARTIAL_OUTAGE,
        StatusType.MAJOR_OUTAGE,
        StatusType.UNDER_MAINTENANCE,
    ]

    for idx, status in enumerate(statuses):
        with cols[idx]:
            if view_mode == ViewMode.ICON:
                icon = STATUS_ICONS.get(status, "?")
                label = STATUS_LABELS.get(status, "Unknown")
                st.markdown(f"**{icon} {label}**")
            else:
                color = get_status_color(status, view_mode)
                label = STATUS_LABELS.get(status, "Unknown")
                st.markdown(
                    f'<div style="display:flex;align-items:center;margin-bottom:0.5rem;">'
                    f'<span style="display:inline-block;width:16px;height:16px;'
                    f'background-color:{color};border-radius:50%;margin-right:8px;"></span>'
                    f"<strong>{label}</strong></div>",
                    unsafe_allow_html=True,
                )


def render_global_status_banner(summary: dict | None, view_mode: ViewMode) -> None:
    """Render the global status banner at the top of the page."""
    if not summary or "status" not in summary:
        st.warning("⚠️ Unable to load status information. Please try again.")
        return

    status_info = summary["status"]
    description = status_info.get("description", "All Systems Operational")
    indicator = status_info.get("indicator", "none")

    # Map indicator to StatusType
    status_map = {
        "none": StatusType.OPERATIONAL,
        "minor": StatusType.DEGRADED_PERFORMANCE,
        "major": StatusType.PARTIAL_OUTAGE,
        "critical": StatusType.MAJOR_OUTAGE,
    }
    status = status_map.get(indicator, StatusType.OPERATIONAL)

    # Render banner
    color = get_status_color(status, view_mode)
    st.markdown(
        f'<div style="padding:1.5rem;background-color:{color};color:white;'
        f'border-radius:8px;margin-bottom:1rem;font-size:1.3rem;font-weight:600;">'
        f"{description}</div>",
        unsafe_allow_html=True,
    )

    # Show last updated
    if "page" in summary and summary["page"].get("updated_at"):
        updated = format_timestamp(
            datetime.fromisoformat(summary["page"]["updated_at"].replace("Z", "+00:00"))
        )
        st.caption(f"Last updated: {updated}")


def render_maintenance_banner(maintenance_list: list[Maintenance], view_mode: ViewMode) -> None:
    """Render active maintenance banner between status and tabs."""
    if not maintenance_list:
        return

    # Check if banner was dismissed this session
    if st.session_state.get("maintenance_banner_dismissed", False):
        return

    with st.container():
        col1, col2 = st.columns([0.95, 0.05])

        with col1:
            st.info(
                f"🔧 **Active Maintenance**: {len(maintenance_list)} maintenance "
                f"window{'s' if len(maintenance_list) > 1 else ''} in progress. "
                "See Maintenance page for details."
            )

        with col2:
            if st.button("✕", key="dismiss_maintenance"):
                st.session_state.maintenance_banner_dismissed = True
                st.rerun()


def render_status_matrix(
    region_services: dict[str, dict[str, Component]],
    view_mode: ViewMode,
    cloud: str,
) -> None:
    """
    Render status matrix for a specific cloud (region × service grid).

    Args:
        region_services: {region_name: {service_name: Component}}
        view_mode: Current view mode
        cloud: Cloud name (for display)
    """
    if not region_services:
        st.info(f"No regions found for {cloud}")
        return

    # Get all unique services across all regions, then order with canonical list
    all_services = set()
    for services in region_services.values():
        all_services.update(services.keys())

    services = order_services(all_services)
    regions = sorted(region_services.keys())

    # Create header row with wider region column (3:1 ratio)
    # Region column is 3x wider than service columns for better readability
    col_widths = [3] + [1] * len(services)

    header_cols = st.columns(col_widths)
    header_cols[0].markdown("**Region**")
    for idx, service in enumerate(services):
        header_cols[idx + 1].markdown(f"**{service}**")

    st.divider()

    # Render each region row
    for region in regions:
        cols = st.columns(col_widths)

        # Region name
        cols[0].markdown(f"**{region}**")

        # Service status cells
        for idx, service in enumerate(services):
            component = region_services[region].get(service)

            if not component:
                cols[idx + 1].markdown("—")  # No data
                continue

            # Build tooltip with status, name, and last update
            status_label = STATUS_LABELS.get(component.status, "Unknown")
            tooltip_parts = [
                f"Status: {status_label}",
                f"Component: {component.name}",
            ]
            if component.updated_at:
                updated_time = format_timestamp(component.updated_at)
                tooltip_parts.append(f"Last updated: {updated_time}")
            tooltip = "\n".join(tooltip_parts)

            # Render status indicator with tooltip on the icon/dot itself
            with cols[idx + 1]:
                render_status_indicator(
                    component.status,
                    view_mode,
                    show_label=False,
                    size="normal",
                    tooltip=tooltip,
                )

        st.divider()


def render_incident_card(incident: Incident, view_mode: ViewMode) -> None:
    """Render an individual incident card."""
    # Determine if incident is resolved
    is_resolved = incident.status in ["resolved", "postmortem"]

    # Status indicator

    with st.expander(
        f"{'✓' if is_resolved else '⚠️'} {incident.name}",
        expanded=not is_resolved,
    ):
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown(f"**Status:** {incident.status.replace('_', ' ').title()}")
            st.markdown(f"**Impact:** {incident.impact.title()}")

        with col2:
            if incident.created_at:
                st.markdown(f"**Created:** {format_timestamp(incident.created_at)}")
            if incident.resolved_at:
                st.markdown(f"**Resolved:** {format_timestamp(incident.resolved_at)}")

        # Incident updates
        if incident.updates:
            st.markdown("**Updates:**")
            for update in sorted(
                incident.updates,
                key=lambda u: u.created_at or datetime.min,
                reverse=True,
            ):
                timestamp = format_timestamp(update.created_at) if update.created_at else "Unknown"
                st.markdown(f"- **{timestamp}**: {update.body}")


def render_maintenance_card(maintenance: Maintenance, view_mode: ViewMode) -> None:
    """Render an individual maintenance card."""
    with st.expander(f"🔧 {maintenance.name}"):
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown(f"**Status:** {maintenance.status.replace('_', ' ').title()}")
            st.markdown(f"**Impact:** {maintenance.impact.title()}")

        with col2:
            if maintenance.scheduled_for:
                start_time = format_timestamp(maintenance.scheduled_for, relative=False)
                st.markdown(f"**Start:** {start_time}")
            if maintenance.scheduled_until:
                end_time = format_timestamp(maintenance.scheduled_until, relative=False)
                st.markdown(f"**End:** {end_time}")


def render_loading_indicator(message: str = "Refreshing...") -> None:
    """Render a non-blocking loading indicator."""
    st.caption(f"🔄 {message}")
