"""
app.py - Streamlit Frontend for Rainwater Harvesting & Construction Water Estimator.

Run with:
    python -m streamlit run app.py
"""

import sys, os, tempfile, time
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from PIL import Image

# Backend imports
from area_detection.building_detection import detect_building_area_percentage
from api import get_rainfall_for_location
from calculations import (
    calculate_project_result_from_sqft,
    DEFAULT_RUNOFF_COEFFICIENT,
    DEFAULT_CURING_DAYS,
    SQFT_PER_SQM,
    DEFAULT_CONCRETE_M3_PER_SQM_FLOOR_AREA,
    DEFAULT_PLASTER_M3_PER_SQM_FLOOR_AREA,
)

# Database imports
from database import (
    initialize_database,
    save_project,
    get_all_projects,
    get_project_by_id,
    delete_project,
    SAVED_PROJECTS_DIR,
)

# ---------------------------------------------------------------------------
# INITIALIZE DATABASE AUTOMATICALLY
# ---------------------------------------------------------------------------
try:
    initialize_database()
except Exception as db_init_err:
    st.error(f"Database initialization warning: {db_init_err}")

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Rainwater Harvesting Estimator For Construction Site",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CUSTOM CSS - Modern SaaS Dashboard
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, p, span, div {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Hero Banner ── */
.hero-wrapper {
    background: linear-gradient(135deg, #091e3a 0%, #103b60 40%, #0d5c75 75%, #107050 100%);
    border-radius: 20px;
    padding: 2.2rem 2rem 1.8rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 12px 36px rgba(9, 30, 58, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.12);
    text-align: center;
    position: relative;
    overflow: hidden;
}
.hero-title {
    color: #ffffff !important;
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
    margin-bottom: 0.5rem !important;
    line-height: 1.2 !important;
}
.hero-subtitle {
    color: #cbd5e1 !important;
    font-size: 1.05rem !important;
    font-weight: 400 !important;
    max-width: 760px;
    margin: 0 auto !important;
    line-height: 1.5;
}

/* ── Section Titles ── */
.custom-section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 1.8rem 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid rgba(148, 163, 184, 0.2);
}
.section-tag {
    background: #0284c7;
    color: #ffffff;
    font-size: 0.72rem;
    font-weight: 800;
    padding: 3px 9px;
    border-radius: 6px;
    letter-spacing: 0.05em;
    font-family: 'JetBrains Mono', monospace;
}
.section-name {
    font-size: 1.2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0;
}

/* ── Card Containers ── */
.glass-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 16px;
    padding: 1.4rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    backdrop-filter: blur(10px);
    transition: all 0.2s ease;
    height: 100%;
}
.glass-card:hover {
    border-color: #0284c7;
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(2, 132, 199, 0.15);
}
.card-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
}
.card-desc {
    font-size: 0.82rem;
    opacity: 0.75;
    margin-bottom: 1rem;
}

/* ── Metric Box Tiles ── */
.stat-box {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 14px;
    padding: 1.3rem 1.1rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.2s ease;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}
.stat-box:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.12);
    border-color: #38bdf8;
}
.stat-icon {
    font-size: 1.8rem;
    margin-bottom: 0.3rem;
}
.stat-val {
    font-size: 1.7rem;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -0.03em;
    line-height: 1.2;
    margin: 0.2rem 0;
}
.stat-lbl {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    opacity: 0.75;
    font-weight: 700;
}
.stat-sub {
    font-size: 0.75rem;
    opacity: 0.6;
    margin-top: 0.3rem;
}

/* ── Highlight Water Balance Hero ── */
.balance-card {
    border-radius: 20px;
    padding: 2.2rem 2rem;
    text-align: center;
    margin: 1.8rem 0;
    position: relative;
    box-shadow: 0 14px 40px rgba(0,0,0,0.15);
}
.balance-card.surplus {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.18) 0%, rgba(5, 150, 105, 0.28) 100%);
    border: 2px solid #10b981;
}
.balance-card.shortfall {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.18) 0%, rgba(185, 28, 28, 0.28) 100%);
    border: 2px solid #ef4444;
}
.balance-status-tag {
    display: inline-block;
    padding: 4px 16px;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.balance-card.surplus .balance-status-tag { background: #10b981; color: white; }
.balance-card.shortfall .balance-status-tag { background: #ef4444; color: white; }

.balance-amount {
    font-size: 3.2rem;
    font-weight: 900;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin: 0.4rem 0;
}
.balance-card.surplus .balance-amount { color: #10b981; }
.balance-card.shortfall .balance-amount { color: #ef4444; }

.balance-expl {
    font-size: 0.98rem;
    font-weight: 500;
    opacity: 0.9;
    max-width: 620px;
    margin: 0.5rem auto 0;
}

/* ── Buttons ── */
div.stButton > button:first-child {
    background: linear-gradient(135deg, #0284c7 0%, #0d9488 100%) !important;
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.04em !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.8rem 2.4rem !important;
    box-shadow: 0 6px 20px rgba(2, 132, 199, 0.35) !important;
    transition: all 0.2s ease !important;
}
div.stButton > button:first-child:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 28px rgba(2, 132, 199, 0.5) !important;
}

/* ── Save Project Card ── */
.save-card {
    background: rgba(2, 132, 199, 0.08);
    border: 1.5px solid #0284c7;
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1.5rem 0;
}

/* ── Project History Table & Badges ── */
.badge-surplus {
    background: #10b981;
    color: white;
    padding: 3px 10px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 0.78rem;
}
.badge-shortfall {
    background: #ef4444;
    color: white;
    padding: 3px 10px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 0.78rem;
}

/* ── Empty State ── */
.empty-state {
    text-align: center;
    padding: 4.5rem 2rem;
    border: 2px dashed rgba(148, 163, 184, 0.25);
    border-radius: 20px;
    margin: 2rem 0;
}
.empty-state-icon {
    font-size: 3.5rem;
    margin-bottom: 0.8rem;
}
.empty-state-title {
    font-size: 1.35rem;
    font-weight: 800;
    margin-bottom: 0.4rem;
}
.empty-state-desc {
    font-size: 0.95rem;
    opacity: 0.7;
    max-width: 500px;
    margin: 0 auto;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# HERO SECTION
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero-wrapper">
    <div class="hero-title">Rainwater Harvesting Estimator For Construction Site</div>
    <div class="hero-subtitle">
        Estimate rooftop rainwater collection potential and compare against site construction water demand.
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SIDEBAR NAVIGATION & PROJECT HISTORY
# ---------------------------------------------------------------------------
st.sidebar.markdown("### 🗂️ Navigation")
app_mode = st.sidebar.radio(
    "Choose Mode:",
    ["Site Analysis (New Project)", "Project History"],
    index=0 if "view_project_id" not in st.session_state else 1,
    key="nav_mode"
)

# "Start New Project" button in sidebar
if st.sidebar.button("➕ Start New Project", use_container_width=True):
    if "results" in st.session_state:
        del st.session_state["results"]
    if "view_project_id" in st.session_state:
        del st.session_state["view_project_id"]
    if "delete_confirm_id" in st.session_state:
        del st.session_state["delete_confirm_id"]
    st.session_state["nav_mode"] = "Site Analysis (New Project)"
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<small style='opacity: 0.7;'>Rainwater Harvesting & Construction Water Estimator<br>Database: SQLite (database/project_data.db)</small>",
    unsafe_allow_html=True,
)


# ===========================================================================
# MODE 1: SITE ANALYSIS (NEW / CURRENT PROJECT)
# ===========================================================================
if app_mode == "Site Analysis (New Project)":
    # Clear any project view lock
    if "view_project_id" in st.session_state:
        del st.session_state["view_project_id"]

    # ── INPUT SECTION ──
    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        st.markdown("""
        <div class="glass-card">
            <div class="card-title">📷 Site Imagery</div>
            <div class="card-desc">Upload drone / satellite / aerial photography</div>
        """, unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload aerial image",
            type=["png", "jpg", "jpeg", "bmp", "webp"],
            label_visibility="collapsed",
            key="site_image_uploader"
        )
        if uploaded_file:
            st.image(uploaded_file, caption="Selected site image", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="glass-card">
            <div class="card-title">📍 Site Information</div>
            <div class="card-desc">Location for rainfall lookup + physical site area</div>
        """, unsafe_allow_html=True)
        address = st.text_input("Site Location / City", placeholder="e.g. Powai, Mumbai", key="site_address")
        site_area_sqft = st.number_input(
            "Total Site Area (sq ft)",
            min_value=1.0,
            value=10000.0 * SQFT_PER_SQM,
            step=1000.0,
            key="site_area_sqft",
            help="Enter the physical site area represented by the full uploaded image.",
        )
        number_of_floors = st.number_input(
            "Number of Floors",
            min_value=1,
            value=1,
            step=1,
            key="number_of_floors",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="glass-card">
            <div class="card-title">⚙️ Estimate Assumptions</div>
            <div class="card-desc">Construction quantities and fixed defaults</div>
        """, unsafe_allow_html=True)
        st.caption(f"Runoff coefficient: {DEFAULT_RUNOFF_COEFFICIENT:.2f} (default)")
        st.caption(f"Curing duration: {DEFAULT_CURING_DAYS:.0f} days (default)")
        st.caption(
            "Volume assumptions per sq ft of total floor area: "
            f"concrete {DEFAULT_CONCRETE_M3_PER_SQM_FLOOR_AREA / SQFT_PER_SQM:.4f} m³, "
            f"plaster {DEFAULT_PLASTER_M3_PER_SQM_FLOOR_AREA / SQFT_PER_SQM:.4f} m³. "
            "The detected footprint is assumed to be the same on each floor."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    _, center_col, _ = st.columns([1, 1.8, 1])
    with center_col:
        analyze_clicked = st.button("⚡ ANALYZE SITE", use_container_width=True)

    # ── PROCESSING PIPELINE ──
    if analyze_clicked:
        if not uploaded_file:
            st.error("📷 Please upload an aerial image of the site before running the analysis.")
            st.stop()
        if not address.strip():
            st.error("📍 Please enter a location / city address.")
            st.stop()

        status_placeholder = st.empty()
        with status_placeholder.container():
            st.markdown("""
            <div class="glass-card" style="margin: 1.5rem 0; border: 1px solid #0284c7;">
                <div style="display:flex; align-items:center; gap: 12px;">
                    <div style="font-size: 1.5rem;">⏳</div>
                    <div>
                        <strong style="font-size: 1.05rem;">Calculating Site Estimates...</strong>
                        <div style="font-size: 0.85rem; opacity: 0.8;">Fetching rainfall records and computing water balance</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            progress_bar = st.progress(10)

        # 1. Save uploaded image to temp file
        suffix = os.path.splitext(uploaded_file.name)[1]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=tempfile.gettempdir())
        tmp.write(uploaded_file.getbuffer())
        tmp.close()
        temp_image_path = tmp.name

        progress_bar.progress(30)

        # 2. OpenCV Detection
        try:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
            detection = detect_building_area_percentage(temp_image_path, output_dir=output_dir)
            rooftop_pct = detection["rooftop_percentage"]
        except Exception as e:
            status_placeholder.empty()
            st.error(f"❌ Building detection failed: {e}")
            st.stop()

        progress_bar.progress(60)

        # 3. Weather API Lookup
        try:
            weather_res = get_rainfall_for_location(address, "2024-01-01", "2024-12-31")
            rainfall_mm = weather_res["total_rainfall_mm"]
        except Exception as e:
            rainfall_mm = 2200.0

        progress_bar.progress(85)

        # 4. Calculations
        try:
            result = calculate_project_result_from_sqft(
                site_area_sqft=site_area_sqft,
                rooftop_percentage=rooftop_pct,
                rainfall_mm=rainfall_mm,
                number_of_floors=number_of_floors,
            )
        except Exception as e:
            status_placeholder.empty()
            st.error(f"❌ Calculation error: {e}")
            st.stop()

        progress_bar.progress(100)
        time.sleep(0.3)

        # Save to session_state so results persist across reruns
        st.session_state["results"] = {
            "result": result,
            "rainfall_mm": rainfall_mm,
            "site_area_sqft": site_area_sqft,
            "runoff_coeff": result["runoff_coefficient"],
            "location": address,
            "temp_image_path": temp_image_path,
            "original_filename": uploaded_file.name,
            "inputs": {
                "runoff_coefficient": result["runoff_coefficient"],
                "concrete_volume_m3": result["concrete_volume_m3"],
                "plaster_volume_m3": result["plaster_volume_m3"],
                "curing_duration_days": DEFAULT_CURING_DAYS,
            }
        }

        # Clear the processing banner completely
        status_placeholder.empty()

    # ── RENDER RESULTS DASHBOARD (IF AVAILABLE) ──
    if "results" in st.session_state:
        data = st.session_state["results"]
        res = data["result"]
        demand = res["demand_breakdown"]

        # ── 01 WATER SUPPLY ──
        st.markdown("""
        <div class="custom-section-header">
            <span class="section-tag">01</span>
            <h2 class="section-name">Rainwater Harvesting Potential (Water Supply)</h2>
        </div>
        """, unsafe_allow_html=True)

        s1, s2, s3, s4 = st.columns(4, gap="medium")
        with s1:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-icon">💧</div>
                <div class="stat-val" style="color: #0284c7;">{res['harvested_water_litres']:,.0f} L</div>
                <div class="stat-lbl">Harvestable Water Yield</div>
                <div class="stat-sub">{res['harvested_water_kl']:,.2f} kL / year</div>
            </div>
            """, unsafe_allow_html=True)
        with s2:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-icon">🌧️</div>
                <div class="stat-val">{data['rainfall_mm']:,.1f} mm</div>
                <div class="stat-lbl">Annual Rainfall</div>
                <div class="stat-sub">Historical precipitation</div>
            </div>
            """, unsafe_allow_html=True)
        with s3:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-icon">🏠</div>
                <div class="stat-val">{res['building_footprint_sqft']:,.0f} sq ft</div>
                <div class="stat-lbl">Estimated Building Footprint</div>
                <div class="stat-sub">Effective runoff area</div>
            </div>
            """, unsafe_allow_html=True)
        with s4:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-icon">📊</div>
                <div class="stat-val">{data['runoff_coeff']:.2f}</div>
                <div class="stat-lbl">Runoff Coefficient</div>
                <div class="stat-sub">Harvesting efficiency</div>
            </div>
            """, unsafe_allow_html=True)

        # ── 02 CONSTRUCTION DEMAND ──
        st.markdown("""
        <div class="custom-section-header">
            <span class="section-tag">02</span>
            <h2 class="section-name">Construction Water Demand Breakdown</h2>
        </div>
        """, unsafe_allow_html=True)

        st.caption(
            f"Estimated total floor area: {res['gross_floor_area_sqft']:,.0f} sq ft "
            f"({res['number_of_floors']:.0f} floor(s)). "
            f"Estimated material volumes: {res['concrete_volume_m3']:,.1f} m³ concrete, "
            f"{res['plaster_volume_m3']:,.1f} m³ plaster. These are planning estimates."
        )

        d1, d2, d3, d4 = st.columns(4, gap="medium")
        with d1:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-icon">🧱</div>
                <div class="stat-val">{demand['concrete_water_litres']:,.0f} L</div>
                <div class="stat-lbl">Concrete Production</div>
                <div class="stat-sub">{demand['concrete_water_litres'] / 1000.0:,.1f} kL</div>
            </div>
            """, unsafe_allow_html=True)
        with d2:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-icon">🎨</div>
                <div class="stat-val">{demand['plaster_water_litres']:,.0f} L</div>
                <div class="stat-lbl">Plastering Works</div>
                <div class="stat-sub">{demand['plaster_water_litres'] / 1000.0:,.1f} kL</div>
            </div>
            """, unsafe_allow_html=True)
        with d3:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-icon">💦</div>
                <div class="stat-val">{demand['curing_water_litres']:,.0f} L</div>
                <div class="stat-lbl">Curing Allowance</div>
                <div class="stat-sub">{demand['curing_water_litres'] / 1000.0:,.1f} kL</div>
            </div>
            """, unsafe_allow_html=True)
        with d4:
            st.markdown(f"""
            <div class="stat-box" style="border-color: #f97316;">
                <div class="stat-icon">🏗️</div>
                <div class="stat-val" style="color: #f97316;">{res['construction_water_demand_litres']:,.0f} L</div>
                <div class="stat-lbl">Total Demand</div>
                <div class="stat-sub">{res['construction_water_demand_kl']:,.1f} kL required</div>
            </div>
            """, unsafe_allow_html=True)

        # ── 03 WATER BALANCE HERO ──
        st.markdown("""
        <div class="custom-section-header">
            <span class="section-tag">03</span>
            <h2 class="section-name">Overall Water Balance & Feasibility</h2>
        </div>
        """, unsafe_allow_html=True)

        diff = res["difference_litres"]
        status = res["status"]

        if status == "SURPLUS":
            balance_cls = "surplus"
            sign = "+"
            amount = res["surplus_litres"]
            microcopy = "Harvested rainwater is <strong>fully sufficient</strong> to meet all construction water requirements for this site."
        elif status == "SHORTFALL":
            balance_cls = "shortfall"
            sign = "-"
            amount = res["shortfall_litres"]
            microcopy = "Harvested water leaves a deficit. An <strong>external municipal or tanker source</strong> is required to bridge the gap."
        else:
            balance_cls = "surplus"
            sign = ""
            amount = 0
            microcopy = "Supply and demand are in exact balance."

        st.markdown(f"""
        <div class="balance-card {balance_cls}">
            <div class="balance-status-tag">{status}</div>
            <div class="balance-amount">{sign}{amount:,.0f} Litres</div>
            <div class="balance-expl">{microcopy}</div>
        </div>
        """, unsafe_allow_html=True)

        # ── 04 SUPPLY VS DEMAND CHART ──
        st.markdown("""
        <div class="custom-section-header">
            <span class="section-tag">04</span>
            <h2 class="section-name">Supply vs Demand Visualization</h2>
        </div>
        """, unsafe_allow_html=True)

        try:
            import pandas as pd
            import altair as alt

            chart_df = pd.DataFrame({
                "Component": ["Harvestable Rainwater (Supply)", "Construction Demand"],
                "Litres": [res["harvested_water_litres"], res["construction_water_demand_litres"]],
                "Type": ["Supply", "Demand"]
            })

            bar_chart = (
                alt.Chart(chart_df)
                .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, size=70)
                .encode(
                    x=alt.X("Component:N", title=None, axis=alt.Axis(labelAngle=0, labelFontSize=13, labelFontWeight='bold')),
                    y=alt.Y("Litres:Q", title="Volume (Litres)", axis=alt.Axis(format=",.0f", titleFontSize=13)),
                    color=alt.Color(
                        "Type:N",
                        scale=alt.Scale(domain=["Supply", "Demand"], range=["#10b981", "#f97316"]),
                        legend=None
                    ),
                    tooltip=[
                        alt.Tooltip("Component:N", title="Category"),
                        alt.Tooltip("Litres:Q", title="Volume (L)", format=",.0f"),
                    ]
                )
                .properties(height=340)
            )
            st.altair_chart(bar_chart, use_container_width=True)
        except Exception as chart_err:
            st.info("Chart module not available.")

        # ── 05 SAVE PROJECT FEATURE ──
        st.markdown("""
        <div class="custom-section-header">
            <span class="section-tag">05</span>
            <h2 class="section-name">Save Project to Database</h2>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="save-card">', unsafe_allow_html=True)
            col_save_name, col_save_btn = st.columns([3, 1], gap="medium")
            with col_save_name:
                project_name_input = st.text_input(
                    "Project Name",
                    value=f"{data['location']} Construction Site",
                    placeholder="e.g. Kalyan Construction Site",
                    key="save_project_name_input",
                )
            with col_save_btn:
                st.write("")
                st.write("")
                save_btn_clicked = st.button("💾 Save Project", use_container_width=True)

            if save_btn_clicked:
                try:
                    new_prj_id = save_project(
                        project_name=project_name_input.strip() or f"Project {data['location']}",
                        location=data["location"],
                        site_area_m2=data["site_area_sqft"] / SQFT_PER_SQM,
                        inputs=data["inputs"],
                        results=res,
                        source_image_path=data.get("temp_image_path"),
                    )
                    st.success(f"✅ Project saved successfully with ID: **{new_prj_id}**")
                    st.info("You can view or manage this project anytime in the **Project History** tab in the sidebar.")
                except Exception as save_err:
                    st.error(f"❌ Failed to save project: {save_err}")
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        # Empty state when user hasn't clicked Analyze yet
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">💧</div>
            <div class="empty-state-title">Ready to Analyze Site</div>
            <div class="empty-state-desc">
                Upload an aerial image, configure the location and construction parameters above, then click <strong>⚡ ANALYZE SITE</strong> to calculate complete water yields and balances.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ===========================================================================
# MODE 2: PROJECT HISTORY & SAVED PROJECT VIEWER
# ===========================================================================
elif app_mode == "Project History":
    st.markdown("""
    <div class="custom-section-header">
        <span class="section-tag">DB</span>
        <h2 class="section-name">Project History & Saved Records</h2>
    </div>
    """, unsafe_allow_html=True)

    try:
        all_projects = get_all_projects()
    except Exception as err:
        st.error(f"Error fetching projects from database: {err}")
        all_projects = []

    if not all_projects:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📂</div>
            <div class="empty-state-title">No Saved Projects Yet</div>
            <div class="empty-state-desc">
                Analyze a site and click <strong>Save Project</strong> to store records in the SQLite database.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── SUMMARY TABLE ──
        table_rows = []
        for p in all_projects:
            status_badge = (
                f'<span class="badge-surplus">SURPLUS (+{p.get("net_water_balance_liters", 0):,.0f} L)</span>'
                if p.get("status") == "SURPLUS"
                else f'<span class="badge-shortfall">SHORTFALL ({p.get("net_water_balance_liters", 0):,.0f} L)</span>'
            )
            table_rows.append({
                "Project ID": p["project_id"],
                "Project Name": p["project_name"],
                "Location": p["location"],
                "Site Area": f"{p['site_area_m2'] * SQFT_PER_SQM:,.0f} sq ft",
                "Created At": p["created_at"],
                "Status": p.get("status", "N/A"),
            })

        import pandas as pd
        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # ── PROJECT SELECTOR FOR VIEWING & DELETION ──
        col_sel, col_action = st.columns([3, 1], gap="medium")
        with col_sel:
            project_options = [f"{p['project_id']} - {p['project_name']} ({p['location']})" for p in all_projects]
            selected_option = st.selectbox("Select Project to View or Manage:", project_options)
            selected_id = selected_option.split(" - ")[0] if selected_option else None

        with col_action:
            st.write("")
            st.write("")
            delete_trigger = st.button("🗑️ Delete Selected Project", use_container_width=True)

        # Confirmation Dialog for Deletion
        if delete_trigger:
            st.session_state["delete_confirm_id"] = selected_id

        if st.session_state.get("delete_confirm_id") == selected_id:
            st.warning(f"⚠️ Are you sure you want to permanently delete **{selected_id}**? All associated inputs and results will be removed.")
            col_yes, col_no, _ = st.columns([1, 1, 3])
            with col_yes:
                if st.button("Yes, Delete", type="primary", use_container_width=True):
                    try:
                        delete_project(selected_id)
                        st.success(f"Project **{selected_id}** deleted successfully.")
                        del st.session_state["delete_confirm_id"]
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as del_err:
                        st.error(f"Failed to delete project: {del_err}")
            with col_no:
                if st.button("Cancel", use_container_width=True):
                    del st.session_state["delete_confirm_id"]
                    st.rerun()

        # ── VIEW SAVED PROJECT DETAILS ──
        if selected_id:
            proj_data = get_project_by_id(selected_id)
            if proj_data:
                p_meta = proj_data["project"]
                p_in = proj_data["inputs"]
                p_res = proj_data["results"]

                st.markdown(f"""
                <div class="custom-section-header">
                    <span class="section-tag">{p_meta['project_id']}</span>
                    <h2 class="section-name">{p_meta['project_name']}</h2>
                </div>
                """, unsafe_allow_html=True)

                # Show saved input image if available
                img_path = p_meta.get("image_filename")
                if img_path:
                    abs_img = Path(__file__).resolve().parent / img_path
                    if abs_img.exists():
                        with st.expander("📷 View Saved Aerial Image"):
                            st.image(str(abs_img), caption=f"Saved image for {p_meta['project_id']}", use_container_width=True)

                # Metadata & Input parameters card
                st.markdown("#### 📋 Project & Construction Parameters")
                param_c1, param_c2, param_c3, param_c4 = st.columns(4, gap="medium")
                with param_c1:
                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="stat-icon">📍</div>
                        <div class="stat-val" style="font-size:1.15rem;">{p_meta['location']}</div>
                        <div class="stat-lbl">Location</div>
                        <div class="stat-sub">Site address</div>
                    </div>
                    """, unsafe_allow_html=True)
                with param_c2:
                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="stat-icon">🌐</div>
                        <div class="stat-val">{p_meta['site_area_m2'] * SQFT_PER_SQM:,.0f} sq ft</div>
                        <div class="stat-lbl">Site Area</div>
                        <div class="stat-sub">Physical boundary</div>
                    </div>
                    """, unsafe_allow_html=True)
                with param_c3:
                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="stat-icon">🏠</div>
                        <div class="stat-val">{p_res.get('rooftop_area_m2', 0) * SQFT_PER_SQM:,.0f} sq ft</div>
                        <div class="stat-lbl">Estimated Rooftop Area</div>
                        <div class="stat-sub">{p_res.get('rooftop_percentage', 0):.2f}% coverage</div>
                    </div>
                    """, unsafe_allow_html=True)
                with param_c4:
                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="stat-icon">🌧️</div>
                        <div class="stat-val">{p_res.get('rainfall_mm', 0):,.1f} mm</div>
                        <div class="stat-lbl">Annual Rainfall</div>
                        <div class="stat-sub">Historical</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.write("")
                # Detailed construction inputs
                in_c1, in_c2, in_c3, in_c4 = st.columns(4, gap="medium")
                with in_c1:
                    st.metric("Runoff Coefficient", f"{p_in.get('runoff_coefficient', DEFAULT_RUNOFF_COEFFICIENT):.2f}")
                with in_c2:
                    st.metric("Concrete Volume", f"{p_in.get('concrete_volume_m3', 0):,.0f} m³")
                with in_c3:
                    st.metric("Plaster Volume", f"{p_in.get('plaster_volume_m3', 0):,.0f} m³")
                with in_c4:
                    st.metric("Curing Duration", f"{p_in.get('curing_duration_days', DEFAULT_CURING_DAYS):.0f} days")

                st.markdown("---")

                # Water Supply & Demand
                st.markdown("#### 💧 Water Yield & Construction Demand")
                res_c1, res_c2, res_c3, res_c4 = st.columns(4, gap="medium")
                with res_c1:
                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="stat-icon">💧</div>
                        <div class="stat-val" style="color: #0284c7;">{p_res.get('harvestable_water_liters', 0):,.0f} L</div>
                        <div class="stat-lbl">Harvestable Rainwater</div>
                        <div class="stat-sub">{p_res.get('harvestable_water_liters', 0) / 1000.0:,.2f} kL</div>
                    </div>
                    """, unsafe_allow_html=True)
                with res_c2:
                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="stat-icon">🧱</div>
                        <div class="stat-val">{p_res.get('concrete_water_liters', 0):,.0f} L</div>
                        <div class="stat-lbl">Concrete Water</div>
                        <div class="stat-sub">{p_res.get('concrete_water_liters', 0) / 1000.0:,.1f} kL</div>
                    </div>
                    """, unsafe_allow_html=True)
                with res_c3:
                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="stat-icon">🎨</div>
                        <div class="stat-val">{p_res.get('plaster_water_liters', 0):,.0f} L</div>
                        <div class="stat-lbl">Plaster Water</div>
                        <div class="stat-sub">{p_res.get('plaster_water_liters', 0) / 1000.0:,.1f} kL</div>
                    </div>
                    """, unsafe_allow_html=True)
                with res_c4:
                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="stat-icon">💦</div>
                        <div class="stat-val">{p_res.get('curing_water_liters', 0):,.0f} L</div>
                        <div class="stat-lbl">Curing Allowance</div>
                        <div class="stat-sub">{p_res.get('curing_water_liters', 0) / 1000.0:,.1f} kL</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.write("")
                # Total demand callout
                st.info(f"**Total Construction Water Demand:** {p_res.get('total_construction_demand_liters', 0):,.0f} Litres ({p_res.get('total_construction_demand_liters', 0)/1000.0:,.2f} kL)")

                # Water balance hero
                status = p_res.get("status", "BALANCED")
                net_balance = p_res.get("net_water_balance_liters", 0)
                conclusion_text = p_res.get("conclusion", "")

                bal_cls = "surplus" if status == "SURPLUS" else "shortfall" if status == "SHORTFALL" else "surplus"
                sign = "+" if net_balance > 0 else ""

                st.markdown(f"""
                <div class="balance-card {bal_cls}">
                    <div class="balance-status-tag">{status}</div>
                    <div class="balance-amount">{sign}{net_balance:,.0f} Litres</div>
                    <div class="balance-expl">{conclusion_text}</div>
                </div>
                """, unsafe_allow_html=True)

                # Supply vs Demand Chart
                try:
                    import pandas as pd
                    import altair as alt

                    chart_df = pd.DataFrame({
                        "Component": ["Harvestable Rainwater (Supply)", "Construction Demand"],
                        "Litres": [p_res["harvestable_water_liters"], p_res["total_construction_demand_liters"]],
                        "Type": ["Supply", "Demand"]
                    })

                    bar_chart = (
                        alt.Chart(chart_df)
                        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, size=70)
                        .encode(
                            x=alt.X("Component:N", title=None, axis=alt.Axis(labelAngle=0, labelFontSize=13, labelFontWeight='bold')),
                            y=alt.Y("Litres:Q", title="Volume (Litres)", axis=alt.Axis(format=",.0f", titleFontSize=13)),
                            color=alt.Color(
                                "Type:N",
                                scale=alt.Scale(domain=["Supply", "Demand"], range=["#10b981", "#f97316"]),
                                legend=None
                            ),
                            tooltip=[
                                alt.Tooltip("Component:N", title="Category"),
                                alt.Tooltip("Litres:Q", title="Volume (L)", format=",.0f"),
                            ]
                        )
                        .properties(height=320)
                    )
                    st.altair_chart(bar_chart, use_container_width=True)
                except Exception:
                    pass
