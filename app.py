import streamlit as st
from PIL import Image
from shapely.geometry import Polygon
import re
from pyproj import Geod

# --- Static Lookup Tables ---
FEEDSTOCK_DATA = {
    "Rice husk": {"density": 96, "yield_factor": 0.25, "default_height": 0.2},
    "Wood chips": {"density": 208, "yield_factor": 0.30, "default_height": 0.3},
    "Maize stalks": {"density": 120, "yield_factor": 0.28, "default_height": 0.25},
    "Coconut shells": {"density": 230, "yield_factor": 0.35, "default_height": 0.3},
    "Sugarcane bagasse": {"density": 150, "yield_factor": 0.27, "default_height": 0.25},
    "Groundnut shells": {"density": 170, "yield_factor": 0.32, "default_height": 0.25},
    "Bamboo": {"density": 300, "yield_factor": 0.33, "default_height": 0.35},
    "Other": {"density": 180, "yield_factor": 0.28, "default_height": 0.25},  # General/average values
}

# Image source resolutions (defaults, hidden from UI)
IMAGE_SOURCE_RESOLUTIONS = {
    "Satellite": 10,      # meters per pixel
    "Low Drone (≈50m altitude)": 0.1,
    "High Drone (≈120m altitude)": 0.3,
}

# --- Functions ---
def calculate_area_from_polygon(coords):
    geod = Geod(ellps="WGS84")
    poly = Polygon(coords)
    lon, lat = poly.exterior.coords.xy
    area, _ = geod.polygon_area_perimeter(lon, lat)
    return abs(area)  # m²

def calculate_area_from_image(image, real_world_width_m):
    width_px, height_px = image.size
    meters_per_pixel = real_world_width_m / width_px
    area_m2 = (width_px * meters_per_pixel) * (height_px * meters_per_pixel)
    return area_m2

def calculate_from_resolution(image, resolution_m_per_px):
    width_px, height_px = image.size
    area_m2 = (width_px * resolution_m_per_px) * (height_px * resolution_m_per_px)
    return area_m2

# --- Streamlit UI ---
st.title("🌱 Biochar Estimation Tool")

# --- Feedstock Selection ---
feedstock_type = st.selectbox("Select Feedstock Type", list(FEEDSTOCK_DATA.keys()))
feedstock = FEEDSTOCK_DATA[feedstock_type]

# --- Area Input Method ---
area_input_method = st.radio(
    "Select Land Area Input Method",
    ["Direct entry (hectares)", "Polygon coordinates (lat/lon)", "Upload image (JPEG)"]
)

area_m2 = None

if area_input_method == "Direct entry (hectares)":
    area_ha = st.number_input("Enter land area (hectares)", min_value=0.0, step=0.1)
    area_m2 = area_ha * 10000

elif area_input_method == "Polygon coordinates (lat/lon)":
    coords_text = st.text_area(
        "Enter polygon coordinates (lat,lon per line)",
        "24.58,73.69\n24.58,73.70\n24.59,73.70\n24.59,73.69"
    )
    try:
        coords = [tuple(map(float, re.split(r"[ ,]+", line.strip()))) for line in coords_text.split("\n") if line.strip()]
        if len(coords) >= 3:
            area_m2 = calculate_area_from_polygon(coords)
            st.success(f"Polygon Area: {area_m2/10000:.2f} hectares")
        else:
            st.warning("Enter at least 3 coordinates for a valid polygon.")
    except Exception as e:
        st.error(f"Invalid coordinates: {e}")

elif area_input_method == "Upload image (JPEG)":
    uploaded_file = st.file_uploader("Upload a JPEG image", type=["jpg", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)

        source_type = st.radio(
            "Select Image Source",
            ["Satellite", "Low Drone (≈50m altitude)", "High Drone (≈120m altitude)", "Manual width entry"]
        )

        if source_type in IMAGE_SOURCE_RESOLUTIONS:
            resolution = IMAGE_SOURCE_RESOLUTIONS[source_type]
            area_m2 = calculate_from_resolution(image, resolution)
        else:
            real_world_width_m = st.number_input("Enter real-world width of the image (m)", min_value=1.0)
            if real_world_width_m > 0:
                area_m2 = calculate_area_from_image(image, real_world_width_m)

# --- Pile Height Input ---
pile_height = st.number_input(
    "Enter feedstock pile height (m)", 
    value=feedstock["default_height"], 
    min_value=0.1, 
    step=0.05
)

# --- Calculations ---
if area_m2:
    volume_m3 = area_m2 * pile_height
    biomass_mass = volume_m3 * feedstock["density"]
    biochar_yield = biomass_mass * feedstock["yield_factor"]
    application_rate = biochar_yield / (area_m2 / 10000)

    # --- Results ---
    st.subheader("📊 Results")
    st.write(f"**Biomass Mass:** {biomass_mass:,.2f} kg")
    st.write(f"**Biochar Yield:** {biochar_yield:,.2f} kg")
    st.write(f"**Application Rate:** {application_rate:,.2f} kg/ha")

    with st.expander("Calculation Details"):
        st.write(f"Area: {area_m2:.2f} m² ({area_m2/10000:.2f} ha)")
        st.write(f"Volume: {volume_m3:.2f} m³")
        st.write(f"Feedstock density: {feedstock['density']} kg/m³")
        st.write(f"Yield factor: {feedstock['yield_factor']}")
        st.write(f"Pile height: {pile_height} m")
else:
    st.info("Please complete the inputs to see results.")
