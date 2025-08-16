import streamlit as st
from PIL import Image
from shapely.geometry import Polygon
import re
from pyproj import Geod

# --- Static Lookup Tables ---
FEEDSTOCK_DATA = {
    "Rice husk": {"density": 96, "yield_factor": 0.25, "default_height": 0.2},
    "Wood chips": {"density": 208, "yield_factor": 0.30, "default_height": 0.3},
    "Corn cobs": {"density": 190, "yield_factor": 0.28, "default_height": 0.25},
    "Coconut shells": {"density": 220, "yield_factor": 0.35, "default_height": 0.3},
    "Bamboo": {"density": 180, "yield_factor": 0.33, "default_height": 0.25},
    "Sugarcane bagasse": {"density": 140, "yield_factor": 0.22, "default_height": 0.2},
    "Groundnut shells": {"density": 130, "yield_factor": 0.26, "default_height": 0.2},
    "Sludge": {"density": 110, "yield_factor": 0.50, "default_height": 0.15},
}

# Fixed defaults
COVERAGE_FRACTION = 0.05    # 5% of land actually covered by feedstock piles
DEFAULT_RESOLUTION = 0.02   # fixed resolution (m/pixel)

# Geod for accurate area from lat/lon
geod = Geod(ellps="WGS84")

st.set_page_config(page_title="Biochar Estimator", layout="centered")
st.title("🌱 Biochar Yield and Application Estimator")

st.markdown("""
This tool estimates the **practical** biomass and biochar you can expect given:
- a feedstock type,
- land area (ha), and
- pile height (m).

**Practical estimate** assumes that only **5%** of your land is actually covered by biomass piles (this keeps results realistic for most farms).
""")

# --- Feedstock Selection ---
feedstock_type = st.selectbox(
    "Select Feedstock Type",
    list(FEEDSTOCK_DATA.keys())  # Only show feedstock names
)
feedstock_info = FEEDSTOCK_DATA[feedstock_type]

# --- Area Input Options ---
st.subheader("1️⃣ Enter Land Area")
area_input_method = st.radio("Choose area input method:", ["Direct (hectares)", "Polygon Coordinates", "Upload JPEG Image"])

area_m2 = None

if area_input_method == "Direct (hectares)":
    hectares = st.number_input("Enter area in hectares:", min_value=0.0, format="%.2f")
    area_m2 = hectares * 10000

elif area_input_method == "Polygon Coordinates":
    coords_text = st.text_area("Enter coordinates (lat,lon) one per line:", placeholder="25.2,73.1\n25.2,73.2\n...")
    try:
        coords = [tuple(map(float, re.split(r"[,\s]+", line.strip()))) for line in coords_text.strip().split("\n") if line.strip()]
        if len(coords) >= 3:
            lons, lats = zip(*[(lon, lat) for lat, lon in coords])
            area_m2, _ = geod.polygon_area_perimeter(lons, lats)
            area_m2 = abs(area_m2)
            st.success(f"Polygon area: {area_m2/10000:.2f} hectares")
        else:
            st.info("Please enter at least 3 coordinate points.")
    except Exception:
        st.warning("Invalid coordinate format. Please use 'lat,lon' per line.")

elif area_input_method == "Upload JPEG Image":
    uploaded_image = st.file_uploader("Upload JPEG Image:", type=["jpg", "jpeg"])
    if uploaded_image:
        image = Image.open(uploaded_image)
        width, height = image.size

        area_m2 = (width * DEFAULT_RESOLUTION) * (height * DEFAULT_RESOLUTION)

        st.success(f"Image size: {width} x {height} pixels | "
                   f"Resolution: {DEFAULT_RESOLUTION:.2f} m/pixel | "
                   f"Estimated area: {area_m2/10000:.2f} hectares")

# --- Pile Height ---
st.subheader("2️⃣ Enter Feedstock Pile Height")
def_height = feedstock_info["default_height"]
height_m = st.number_input(f"Enter pile height (meters) — default: {def_height} m:", min_value=0.0, value=def_height, step=0.01)

# --- Calculate Button ---
if st.button("📊 Show Practical Estimate"):
    if not area_m2 or height_m <= 0:
        st.info("Please complete all inputs (area and pile height) to see results.")
    else:
        density = feedstock_info["density"]
        yield_factor = feedstock_info["yield_factor"]
        area_ha = area_m2 / 10000.0

        pile_area_m2 = area_m2 * COVERAGE_FRACTION
        volume_m3 = pile_area_m2 * height_m
        biomass_kg = volume_m3 * density
        biochar_kg = biomass_kg * yield_factor
        application_rate_kg_per_ha = biochar_kg / area_ha if area_ha > 0 else 0

        st.subheader(f"✅ Practical Results (assuming {COVERAGE_FRACTION*100:.1f}% pile coverage)")
        st.write(f"**Estimated Biomass Input:** {biomass_kg:,.2f} kg")
        st.write(f"**Estimated Biochar Yield:** {biochar_kg:,.2f} kg")
        st.write(f"**Application Rate (over full area):** {application_rate_kg_per_ha:,.2f} kg/ha")

        if application_rate_kg_per_ha > 10000:
            st.warning("⚠ The application rate exceeds the recommended maximum of 10 t/ha. Consider reducing pile height or coverage.")

        with st.expander("📌 Calculation Details (practical)"):
            st.write(f"Feedstock: {feedstock_type}")
            st.write(f"Total area: {area_m2:.2f} m² ({area_ha:.2f} ha)")
            st.write(f"Pile footprint (assumed): {pile_area_m2:.2f} m² ({pile_area_m2/10000:.2f} ha)")
            st.write(f"Pile height: {height_m} m")
            st.write(f"Volume (piles): {volume_m3:.2f} m³")
            st.write(f"Density: {density} kg/m³")
            st.write(f"Yield factor: {yield_factor}")
            st.write(f"Coverage fraction used: {COVERAGE_FRACTION:.3f} ({COVERAGE_FRACTION*100:.1f}%)")

st.markdown("---")
st.markdown("Made with ❤️ by **Mayank Kumar Sharma**")

