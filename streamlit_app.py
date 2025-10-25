"""Main entry point for Accessible Snowflake Status app."""

import time

import streamlit as st

from lib.api import SnowflakeStatusAPI
from lib.components import (
    render_global_status_banner,
    render_maintenance_banner,
    render_status_legend,
    render_status_matrix,
)
from lib.config import DEFAULT_REFRESH_INTERVAL, ViewMode
from lib.utils import build_status_matrix

# Page configuration
st.set_page_config(
    page_title="SnowStat - Icon-based Snowflake Status",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "view_mode" not in st.session_state:
    st.session_state.view_mode = ViewMode.ICON  # Default to icon mode

if "auto_refresh_enabled" not in st.session_state:
    st.session_state.auto_refresh_enabled = False

if "refresh_interval" not in st.session_state:
    st.session_state.refresh_interval = DEFAULT_REFRESH_INTERVAL

if "maintenance_banner_dismissed" not in st.session_state:
    st.session_state.maintenance_banner_dismissed = False

# Header with Snowflake branding
col1, col2 = st.columns([0.1, 0.9])
with col1:
    st.markdown("# ❄️")
with col2:
    st.title("SnowStat")
    st.caption("Snowflake operational health, made visually clear for everyone.")

# Inject custom CSS to style cloud tabs (wider, larger text, borders, active highlight)
st.markdown(
    """
    <style>
    /* Make the tab list fill width and add spacing */
    div[data-testid="stTabs"] > div[role="tablist"] {
        gap: 12px;
    }
    /* Base tab button style */
    div[data-testid="stTabs"] button[role="tab"] {
        flex: 1 1 0;
        justify-content: center;
        font-size: 16px;             /* per selection */
        font-weight: 600;
        padding: 10px 16px;          /* larger touch target */
        border: 1.5px solid rgba(0, 0, 0, 0.15);
        border-radius: 10px;
        background: transparent;
        color: inherit;              /* respect theme text color */
    }
    /* Active tab: fixed Snowflake blue background + white text */
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background-color: #29B5E8;
        color: #ffffff !important;
        border-color: #29B5E8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.divider()

# Sidebar - Settings and links
with st.sidebar:
    st.markdown("## View Settings")

    view_mode = st.radio(
        "Display Mode",
        options=[ViewMode.ICON, ViewMode.STANDARD],
        format_func=lambda x: {
            ViewMode.ICON: "🎯 Icon Mode (Default)",
            ViewMode.STANDARD: "🎨 Standard Colors",
        }[x],
        index=[ViewMode.ICON, ViewMode.STANDARD].index(st.session_state.view_mode),
        help="Choose how status indicators are displayed",
    )

    if view_mode != st.session_state.view_mode:
        st.session_state.view_mode = view_mode
        st.rerun()

    st.divider()

    st.markdown("## Auto-Refresh")
    auto_refresh = st.toggle(
        "Enable Auto-Refresh",
        value=st.session_state.get("auto_refresh_enabled", False),
        help="Automatically refresh status data at the specified interval",
    )
    if auto_refresh != st.session_state.get("auto_refresh_enabled", False):
        st.session_state.auto_refresh_enabled = auto_refresh

    if auto_refresh:
        interval_minutes = st.slider(
            "Refresh Interval (minutes)",
            min_value=1,
            max_value=10,
            value=max(1, min(10, st.session_state.get("refresh_interval", DEFAULT_REFRESH_INTERVAL) // 60)),
            help="How often to refresh data automatically",
        )
        st.session_state.refresh_interval = interval_minutes * 60

    st.divider()

    st.markdown("### Quick Links")
    st.markdown("[Snowflake Status](https://status.snowflake.com)")
    st.markdown("[Incident History](https://status.snowflake.com/history)")

    st.divider()

    st.markdown("## About")
    st.markdown(
        """
        **Accessible Snowflake Status** is a colorblind-friendly alternative to the 
        [official Snowflake Status page](https://status.snowflake.com).

        **Features:**
        - Icon-based and standard color display modes
        - Auto-refresh with configurable interval
        - Local timezone support for all timestamps

        **Data Source:** Snowflake Status API

        **Version:** 0.1.0

        ---

        Built by **Eric Heilman**, Sr. Solution Engineer at Snowflake

        *This is an open-source community tool and is not officially affiliated with Snowflake Inc.*
        """
    )

# Content: Single-page Status view
view_mode = st.session_state.get("view_mode")
api = SnowflakeStatusAPI()

# Subtle indicator when refreshing is enabled
if st.session_state.get("auto_refresh_enabled", False):
    st.caption("🔄 Refreshing enabled")

# Fetch and render
try:
    summary = api.get_summary()
    components = api.get_components()
    active_maintenance = api.get_active_maintenance()
except Exception as e:
    st.error(f"Failed to load status data: {str(e)}")
    if st.button("🔄 Retry"):
        st.rerun()
    st.stop()

render_global_status_banner(summary, view_mode)
render_status_legend(view_mode)
st.divider()
render_maintenance_banner(active_maintenance, view_mode)
st.divider()

# Build and render matrix
matrix = build_status_matrix(components)
if not matrix:
    st.warning("No component data available at this time.")
    if st.button("🔄 Refresh"):
        st.rerun()
    st.stop()

clouds = ["AWS", "AZURE", "GCP"]
available_clouds = [c for c in clouds if c in matrix]
if not available_clouds:
    st.info("No cloud components found")
else:
    tabs = st.tabs(available_clouds)
    for idx, cloud in enumerate(available_clouds):
        with tabs[idx]:
            st.markdown(f"### {cloud} Status")
            render_status_matrix(matrix[cloud], view_mode, cloud)

# Auto-refresh loop
if st.session_state.get("auto_refresh_enabled", False):
    time.sleep(st.session_state.get("refresh_interval", DEFAULT_REFRESH_INTERVAL))
    st.rerun()
