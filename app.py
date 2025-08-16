import streamlit as st
import math
from shapely.geometry import Polygon
from PIL import Image

# Feedstock data
feedstocks = {
    "Rice husk": {"density": 96, "yield_factor": 0.25, "default_height": 1.0},
    "Wood chips": {"density": 208, "yield_factor": 0.30, "default_height": 1.2},
    "Corncob": {"density": 200, "yield_factor": 0.28, "default_height": 1.0},
    "Sugarcane bagasse": {"density": 160, "yield_factor": 0.23, "default_height": 0.8},
    "Coconut shell": {"density": 320, "yield_factor": 0.35, "default_height": 0.7},
    "Bamboo": {"density": 300, "yield_factor": 0.33, "default_height": 1.5},
    "Groundnut shell": {"density": 190, "yield_factor": 0.26, "default_height": 0.9},
}

st.title("🌱 Biochar Estimation Tool")

# Feedstock input
feedstock_type = st.selectbox("Select Feedstock Type:", list(feedstocks.keys()))

# Land area input method
area_method = st.radio("Choose land area input method:", [
    "Direct entry (hectares)",
    "Polygon coordinates (lat/lon)",
    "Upload JPEG image"
])

land_area_m2 = None

if area_method == "Direct entry (hectares)":
    land_area_ha = st.number_input("Enter land area (hectares):", min_value=0.0, step=0.1)
    land_area_m2 = land_area_ha * 10000

elif area_method == "Polygon coordinates (lat/lon)":
    coords_text = st.text_area("Enter polygon coordinates (lat,lon per line):")
    if coords_text:
        try:
            coords = [tuple(map(float, line.split(','))) for line in coords_text.splitlines()]
            poly = Polygon(coords)
            land_area_m2 = poly.area * (111320 ** 2)  # rough conversion lat/lon -> meters²
            st.success(f"Calculated area from polygon: {land_area_m2/10000:.2f} hectares")
        except Exception as e:
            st.error(f"Error parsing coordinates: {e}")

elif area_method == "Upload JPEG image":
    resolution_choice = st.selectbox(
        "Select image source (defines resolution):",
        ["Rooftop (~0.1 m/pixel)", "Low Drone (~0.5 m/pixel)", "High Drone (~1 m/pixel)", "Satellite (~0.08 m/pixel)"]
    )

    resolution_map = {
        "Rooftop (~0.1 m/pixel)": 0.1,
        "Low Drone (~0.5 m/pixel)": 0.5,
        "High Drone (~1 m/pixel)": 1.0,
        "Satellite (~0.08 m/pixel)": 0.08,
    }
    resolution = resolution_map[resolution_choice]

    uploaded_file = st.file_uploader("Upload JPEG image", type=["jpg", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        width, height = image.size
        st.image(image, caption="Uploaded Image", use_container_width=True)  # ✅ FIXED HERE

        # Calculate area in hectares
        land_area_m2 = (width * resolution) * (height * resolution)
        land_area_ha = land_area_m2 / 10000

        # ✅ Show user how many hectares were calculated
        st.success(f"Calculated land area from image: **{land_area_ha:.2f} hectares**")

# Pile height input
if feedstock_type:
    default_height = feedstocks[feedstock_type]["default_height"]
    pile_height = st.number_input(
        "Enter pile height (m):",
        min_value=0.1, step=0.1, value=default_height
    )

# Perform calculations if area is available
if land_area_m2 and feedstock_type:
    density = feedstocks[feedstock_type]["density"]
    yield_factor = feedstocks[feedstock_type]["yield_factor"]

    volume = land_area_m2 * pile_height
    biomass_mass = volume * density
    biochar_yield = biomass_mass * yield_factor
    application_rate = biochar_yield / (land_area_m2 / 10000)

    st.subheader("Results")
    st.write(f"**Biochar Yield:** {biochar_yield:,.2f} kg")
    st.write(f"**Land Area Covered:** {land_area_m2/10000:.2f} hectares")
    st.write(f"**Application Rate:** {application_rate:,.2f} kg/ha")

    with st.expander("Calculation Details"):
        st.write(f"Volume = {land_area_m2:,.2f} m² × {pile_height} m = {volume:,.2f} m³")
        st.write(f"Biomass Mass = {volume:,.2f} m³ × {density} kg/m³ = {biomass_mass:,.2f} kg")
        st.write(f"Biochar Yield = {biomass_mass:,.2f} kg × {yield_factor} = {biochar_yield:,.2f} kg")
        st.write(f"Application Rate = {biochar_yield:,.2f} kg ÷ {land_area_m2/10000:.2f} ha = {application_rate:,.2f} kg/ha")
