import streamlit as st
from PIL import Image
from shapely.geometry import Polygon
import re

# --- Static Lookup Tables ---
FEEDSTOCK_DATA = {
    "Rice husk": {"density": 96, "yield_factor": 0.25, "default_height": 0.2},
    "Wood chips": {"density": 208, "yield_factor": 0.30, "default_height": 0.3},
    "Corn cobs": {"density": 190, "yield_factor": 0.28, "default_height": 0.25},
    "Coconut shells": {"density": 220, "yield_factor": 0.35, "default_height": 0.3},
    "Bamboo": {"density": 180, "yield_factor": 0.33, "default_height": 0.25},
    "Sugarcane bagasse": {"density": 140, "yield_factor": 0.22, "default_height": 0.2},
    "Groundnut shells": {"density": 130, "yield_factor": 0.26, "default_height": 0.2},
    "Sludge": {"density": 110, "yield_factor": 0.20, "default_height": 0.2},
}

DEFAULT_RESOLUTION = 10  # meters per pixel for JPEG images

st.set_page_config(page_title="Biochar Estimator", layout="centered")
st.title("🌱 Biochar Yield and Application Estimator")

st.markdown("""
This tool estimates:
1. Biomass input based on area and feedstock type.
2. Biochar yield using a predefined yield factor.
3. Biochar application rate in kg per hectare.
""")

# --- Feedstock Selection ---
feedstock_type = st.selectbox("Select Feedstock Type", list(FEEDSTOCK_DATA.keys()))
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
            polygon = Polygon(coords)
            area_m2 = polygon.area * (111_000 ** 2)  # crude lat/lon to m² conversion
            st.success(f"Polygon area: {area_m2/10000:.2f} hectares")
        else:
            st.info("Please enter at least 3 coordinate points.")
    except Exception:
        st.warning("Invalid coordinate format.")

elif area_input_method == "Upload JPEG Image":
    uploaded_image = st.file_uploader("Upload JPEG Image:", type=["jpg", "jpeg"])
    if uploaded_image:
        resolution_input = st.number_input(
            f"Enter image resolution (meters per pixel, leave 0 for default {DEFAULT_RESOLUTION} m/pixel):",
            min_value=0.0, value=0.0, step=0.1, format="%.2f"
        )
        resolution = resolution_input if resolution_input > 0 else DEFAULT_RESOLUTION

        image = Image.open(uploaded_image)
        width, height = image.size
        area_m2 = (width * height) * (resolution ** 2)
        st.success(f"Image size: {width} x {height} pixels | Resolution used: {resolution} m/pixel | Estimated area: {area_m2/10000:.2f} hectares")

# --- Pile Height ---
st.subheader("2️⃣ Enter Feedstock Pile Height")
def_height = feedstock_info["default_height"]
height_m = st.number_input(f"Enter height of biomass pile in meters (default: {def_height} m):", min_value=0.0, value=def_height, step=0.01)

# --- Calculate Button ---
calculate = st.button("Calculate Biochar Estimates")

# --- Calculations ---
if calculate:
    if area_m2 and height_m > 0:
        volume = area_m2 * height_m  # m³
        density = feedstock_info["density"]
        yield_factor = feedstock_info["yield_factor"]

        biomass_kg = volume * density
        biochar_kg = biomass_kg * yield_factor
        area_ha = area_m2 / 10000
        application_rate = biochar_kg / area_ha if area_ha > 0 else 0

        st.subheader("📊 Results")
        st.write(f"**Estimated Biomass Input:** {biomass_kg:,.2f} kg")
        st.write(f"**Estimated Biochar Yield:** {biochar_kg:,.2f} kg")
        st.write(f"**Application Rate:** {application_rate:,.2f} kg/ha")

        with st.expander("📌 Calculation Details"):
            st.write(f"Feedstock: {feedstock_type}")
            st.write(f"Area: {area_m2:.2f} m²")
            st.write(f"Height: {height_m} m")
            st.write(f"Density: {density} kg/m³")
            st.write(f"Yield Factor: {yield_factor}")
    else:
        st.info("Please complete all inputs to see results.")

# --- Footer ---
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("❤️ Made with love by **Mayank Kumar Sharma**")
