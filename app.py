import streamlit as st
from PIL import Image
import io

# -------------------------
# Static Data
# -------------------------
FEEDSTOCK_TYPES = {
    "Rice Husk": {"density": 96, "yield_factor": 0.25, "default_height": 1.2},
    "Wood Chips": {"density": 208, "yield_factor": 0.3, "default_height": 1.0},
    "Corn Cobs": {"density": 190, "yield_factor": 0.28, "default_height": 1.0},
    "Sugarcane Bagasse": {"density": 144, "yield_factor": 0.23, "default_height": 1.1},
    "Coconut Shells": {"density": 225, "yield_factor": 0.33, "default_height": 1.0},
    "Bamboo": {"density": 180, "yield_factor": 0.26, "default_height": 1.3},
    "Groundnut Shells": {"density": 130, "yield_factor": 0.22, "default_height": 1.2}
}

DEFAULT_RESOLUTION_M_PER_PIXEL = 10  # meters per pixel for JPEGs

# -------------------------
# Helper Functions
# -------------------------
def calculate_area_from_image(image, real_world_width_m):
    width_px, height_px = image.size
    resolution = real_world_width_m / width_px  # meters per pixel
    area_m2 = (width_px * resolution) * (height_px * resolution)
    return area_m2

def calculate_biomass_mass(area_m2, height_m, density):
    volume_m3 = area_m2 * height_m
    mass_kg = volume_m3 * density
    return mass_kg

def calculate_biochar_yield(biomass_mass_kg, yield_factor):
    return biomass_mass_kg * yield_factor

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Biochar Yield Estimator", layout="centered")
st.title("🌱 Biochar Yield Estimation Tool")

st.markdown("---")
st.header("1. Select Feedstock Type")
feedstock = st.selectbox("Choose feedstock type:", list(FEEDSTOCK_TYPES.keys()))

st.markdown("---")
st.header("2. Provide Land Area")
area_option = st.radio("How do you want to provide land area?", ["Manual Entry", "Upload JPEG Image"])

area_m2 = None

if area_option == "Manual Entry":
    area_unit = st.radio("Unit of land area:", ["Square meters (m²)", "Hectares (ha)"])
    area_input = st.number_input("Enter land area:", min_value=0.0, format="%.2f")
    if area_unit == "Hectares (ha)":
        area_m2 = area_input * 10000
    else:
        area_m2 = area_input

elif area_option == "Upload JPEG Image":
    uploaded_file = st.file_uploader("Upload JPEG image of land:", type=["jpg", "jpeg"])
    real_width = st.number_input("Enter real-world width of image (in meters):", min_value=0.0, format="%.2f")
    if uploaded_file and real_width > 0:
        image = Image.open(uploaded_file)
        area_m2 = calculate_area_from_image(image, real_width)
        st.success(f"Estimated area from image: {area_m2:.2f} m²")

# -------------------------
# Pile Height
# -------------------------
st.markdown("---")
st.header("3. Provide Pile Height")
default_height = FEEDSTOCK_TYPES[feedstock]["default_height"]

use_custom_height = st.checkbox("Do you want to enter custom pile height?")
if use_custom_height:
    height_m = st.number_input("Enter pile height (in meters):", min_value=0.0, format="%.2f")
else:
    height_m = default_height
    st.info(f"Using default height for {feedstock}: {height_m} meters")

# -------------------------
# Final Calculation
# -------------------------
st.markdown("---")
if area_m2 and height_m:
    density = FEEDSTOCK_TYPES[feedstock]["density"]
    yield_factor = FEEDSTOCK_TYPES[feedstock]["yield_factor"]

    biomass_mass_kg = calculate_biomass_mass(area_m2, height_m, density)
    biochar_yield_kg = calculate_biochar_yield(biomass_mass_kg, yield_factor)
    application_rate = biochar_yield_kg / (area_m2 / 10000)  # kg per hectare

    st.header("4. Results")
    st.success(f"Estimated Biomass Input: **{biomass_mass_kg:.2f} kg**")
    st.success(f"Estimated Biochar Yield: **{biochar_yield_kg:.2f} kg**")
    st.success(f"Application Rate: **{application_rate:.2f} kg/ha**")

else:
    st.warning("Please provide both land area and pile height to compute results.")
