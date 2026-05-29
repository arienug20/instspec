"""InstSpec - Instrument Data Sheet Generator & Sizer

Main Streamlit application entry point.
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from config import config

# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .status-ok {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point"""

    # Sidebar navigation
    with st.sidebar:
        st.title("🔧 InstSpec")
        st.markdown("---")

        # Main navigation
        page = st.selectbox(
            "Navigation",
            [
                "📊 Dashboard",
                "➕ New Instrument",
                "🔵 Orifice Sizer",
                "🔧 Control Valve",
                "📏 Flow Element",
                "📡 DP Transmitter",
                "🌡️ Thermowell",
                "📄 Data Sheet Preview",
                "📋 Project List",
                "⚙️ Settings"
            ],
            index=0
        )

        st.markdown("---")

        # Project info placeholder
        if "current_project" in st.session_state:
            project = st.session_state.current_project
            st.info(f"📁 Project: {project['name']}")
        else:
            st.info("📁 No project selected")

    # Main content area
    st.markdown(f'<h1 class="main-header">{config.APP_TITLE}</h1>', unsafe_allow_html=True)

    # Page routing
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "➕ New Instrument":
        show_new_instrument()
    elif page == "🔵 Orifice Sizer":
        show_orifice_sizer()
    elif page == "🔧 Control Valve":
        show_control_valve_sizer()
    elif page == "📏 Flow Element":
        show_flow_element_sizer()
    elif page == "📡 DP Transmitter":
        show_dp_transmitter_checker()
    elif page == "🌡️ Thermowell":
        show_thermowell_sizer()
    elif page == "📄 Data Sheet Preview":
        show_datasheet_preview()
    elif page == "📋 Project List":
        show_project_list()
    elif page == "⚙️ Settings":
        show_settings()


def show_dashboard():
    """Dashboard page with project overview"""
    st.markdown('<h2 class="section-header">Dashboard</h2>', unsafe_allow_html=True)

    if "current_project" not in st.session_state:
        st.info("👋 Welcome to InstSpec! Please select or create a project to get started.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 View Projects", use_container_width=True):
                st.session_state.page = "📋 Project List"
                st.rerun()
        with col2:
            if st.button("➕ Create New Project", use_container_width=True):
                show_new_project_dialog()
    else:
        project = st.session_state.current_project
        st.success(f"📁 Current Project: {project['name']}")

        # Project statistics placeholder
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Instruments", "0")
        with col2:
            st.metric("Drafts", "0")
        with col3:
            st.metric("Reviewed", "0")
        with col4:
            st.metric("Approved", "0")

        st.markdown("---")

        # Recent instruments placeholder
        st.markdown('<h3>Recent Instruments</h3>', unsafe_allow_html=True)
        st.info("No instruments added yet. Click 'New Instrument' to add your first instrument.")


def show_new_project_dialog():
    """Show dialog to create new project"""
    st.markdown('<h3>Create New Project</h3>', unsafe_allow_html=True)

    with st.form("new_project_form"):
        name = st.text_input("Project Name *")
        description = st.text_area("Description")
        client = st.text_input("Client")
        location = st.text_input("Location")

        submit = st.form_submit_button("Create Project", use_container_width=True)

        if submit:
            if not name:
                st.error("Project name is required")
                return

            # Create project in database
            from database import db
            project_id = db.create_project(
                name=name,
                description=description,
                client=client,
                location=location
            )

            # Set as current project
            st.session_state.current_project = {
                'id': project_id,
                'name': name,
                'description': description,
                'client': client,
                'location': location
            }

            st.success(f"✅ Project '{name}' created successfully!")
            st.rerun()


def show_new_instrument():
    """New instrument wizard"""
    st.markdown('<h2 class="section-header">New Instrument</h2>', unsafe_allow_html=True)

    if "current_project" not in st.session_state:
        st.warning("⚠️ Please select or create a project first")
        return

    # Step 1: Select instrument type
    st.markdown('<h3>Step 1: Select Instrument Type</h3>', unsafe_allow_html=True)

    instrument_types = [
        "Orifice Plate",
        "Control Valve",
        "Flow Element (Venturi/Nozzle/V-Cone/Wedge)",
        "DP Transmitter",
        "Thermowell",
        "Flow Transmitter",
        "Pressure Transmitter",
        "Temperature Element",
        "Level Transmitter"
    ]

    selected_type = st.selectbox("Instrument Type", instrument_types)

    if selected_type:
        st.info(f"📌 Selected: {selected_type}")

        # Step 2: Basic information
        st.markdown('<h3>Step 2: Basic Information</h3>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            tag_number = st.text_input("Tag Number *", placeholder="e.g., FT-101")
            service = st.text_input("Service", placeholder="e.g., Crude Oil Transfer")

        with col2:
            line_number = st.text_input("Line Number", placeholder="e.g., 100-PT-101")
            location = st.text_input("Location", placeholder="e.g., Platform A")

        # Continue button
        if st.button("Continue to Sizing", use_container_width=True):
            if not tag_number:
                st.error("Tag number is required")
                return

            # Store in session state
            st.session_state.new_instrument = {
                'tag_number': tag_number,
                'service': service,
                'line_number': line_number,
                'location': location,
                'instrument_type': selected_type
            }

            # Redirect to appropriate sizer page
            if "Orifice" in selected_type:
                st.session_state.page = "🔵 Orifice Sizer"
            elif "Control Valve" in selected_type:
                st.session_state.page = "🔧 Control Valve"
            elif "Flow Element" in selected_type:
                st.session_state.page = "📏 Flow Element"
            elif "Thermowell" in selected_type:
                st.session_state.page = "🌡️ Thermowell"

            st.rerun()


def show_orifice_sizer():
    """Orifice plate sizing page"""
    st.markdown('<h2 class="section-header">Orifice Plate Sizer</h2>', unsafe_allow_html=True)
    st.info("🚧 Orifice plate sizer is under development. This feature will be available in Sprint 2.")

    # Placeholder for basic structure
    with st.expander("Input Parameters", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.text_input("Pipe Size (mm)")
            st.text_input("Schedule")

        with col2:
            st.text_input("Normal Flow (kg/h)")
            st.text_input("Max Flow (kg/h)")

    if st.button("Calculate", use_container_width=True):
        st.warning("🔨 Calculation engine will be implemented in Sprint 2")


def show_control_valve_sizer():
    """Control valve sizing page"""
    st.markdown('<h2 class="section-header">Control Valve Sizer</h2>', unsafe_allow_html=True)
    st.info("🚧 Control valve sizer is under development. This feature will be available in Sprint 3.")

    if st.button("Calculate", use_container_width=True):
        st.warning("🔨 Calculation engine will be implemented in Sprint 3")


def show_flow_element_sizer():
    """Flow element sizing page"""
    st.markdown('<h2 class="section-header">Flow Element Sizer</h2>', unsafe_allow_html=True)
    st.info("🚧 Flow element sizer is under development. This feature will be available in Sprint 4.")

    if st.button("Calculate", use_container_width=True):
        st.warning("🔨 Calculation engine will be implemented in Sprint 4")


def show_dp_transmitter_checker():
    """DP transmitter range checker page"""
    st.markdown('<h2 class="section-header">DP Transmitter Range Checker</h2>', unsafe_allow_html=True)
    st.info("🚧 DP transmitter checker is under development. This feature will be available in Sprint 4.")

    if st.button("Check Range", use_container_width=True):
        st.warning("🔨 Calculation engine will be implemented in Sprint 4")


def show_thermowell_sizer():
    """Thermowell sizing page"""
    st.markdown('<h2 class="section-header">Thermowell Wake Frequency Calculator</h2>', unsafe_allow_html=True)
    st.info("🚧 Thermowell sizer is under development. This feature will be available in Sprint 4.")

    if st.button("Calculate", use_container_width=True):
        st.warning("🔨 Calculation engine will be implemented in Sprint 4")


def show_datasheet_preview():
    """Data sheet preview page"""
    st.markdown('<h2 class="section-header">Data Sheet Preview</h2>', unsafe_allow_html=True)
    st.info("🚧 Data sheet generator is under development. This feature will be available in Sprint 5.")


def show_project_list():
    """Project list page"""
    st.markdown('<h2 class="section-header">Project List</h2>', unsafe_allow_html=True)

    # Load projects from database
    from database import db
    projects = db.list_projects()

    if not projects:
        st.info("No projects found. Create your first project below:")
        if st.button("➕ Create Project", use_container_width=True):
            show_new_project_dialog()
        return

    # Display projects
    for project in projects:
        with st.expander(f"📁 {project['name']}", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Client:** {project['client'] or 'N/A'}")
                st.write(f"**Location:** {project['location'] or 'N/A'}")

            with col2:
                st.write(f"**Created:** {project['created_at'][:10]}")
                st.write(f"**Updated:** {project['updated_at'][:10]}")

            if project['description']:
                st.write(f"**Description:** {project['description']}")

            button_col1, button_col2 = st.columns(2)
            with button_col1:
                if st.button(f"📂 Open", key=f"open_{project['id']}"):
                    st.session_state.current_project = project
                    st.rerun()
            with button_col2:
                if st.button(f"🗑️ Delete", key=f"delete_{project['id']}"):
                    if st.confirm(f"Are you sure you want to delete '{project['name']}'?"):
                        db.delete_project(project['id'])
                        st.rerun()

    st.markdown("---")
    if st.button("➕ Create New Project", use_container_width=True):
        show_new_project_dialog()


def show_settings():
    """Settings page"""
    st.markdown('<h2 class="section-header">Settings</h2>', unsafe_allow_html=True)

    # Default units
    st.markdown('<h3>Default Units</h3>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.selectbox(
            "Pressure Unit",
            ["bar", "kPa", "MPa", "psi", "kgf/cm2"],
            index=0
        )

    with col2:
        st.selectbox(
            "Temperature Unit",
            ["°C", "K", "°F"],
            index=0
        )

    with col3:
        st.selectbox(
            "Flow Unit",
            ["kg/h", "kg/s", "m³/h", "GPM", "BPD"],
            index=0
        )

    # Company information
    st.markdown('<h3>Company Information</h3>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Company Name")
        st.text_input("Logo URL")

    with col2:
        st.text_input("Address")
        st.text_input("Contact Email")

    st.markdown("---")

    # Database management
    st.markdown('<h3>Database</h3>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Reset Database", use_container_width=True):
            st.warning("⚠️ This will delete all data. Use with caution!")

    with col2:
        if st.button("💾 Export Data", use_container_width=True):
            st.info("Data export feature coming soon")


if __name__ == "__main__":
    main()