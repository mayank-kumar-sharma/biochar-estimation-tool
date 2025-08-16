import streamlit as st
from shapely.geometry import Polygon
from PIL import Image

# ---- Feedstock Data ----
FEEDSTOCKS = {
    "Rice Husk": {"density": 96, "yield_factor": 0.35, "default_height": 1.0},
    "Wood Chips": {"density": 208, "yield_factor": 0.30, "default_height": 1.5},
    "Corn Cobs": {"density": 160, "yield_factor": 0.33, "default_height": 1.2},
    "Sugarcane Bagasse": {"density": 120, "yield_factor": 0.28, "default_height": 1.0},
    "Coconut Shell": {"density": 230, "yield_factor": 0.40, "default_height": 1.0},
    "Bamboo": {"density": 300, "yield_factor": 0.32, "default_height": 1.5},
}

# ---- Resolution mapping for sources ----
RESOLUTIONS = {
    "Rooftop": 0.05,   # 5 cm/pixel
    "Low Drone": 0.2,  # 20 cm/pixel
    "High Drone": 1.0, # 1 m/pixel
    "Satellite": 0.8  # 0.8/pixel
}

st.title("🌱 Biochar Estimation Tool")

# ---- Step 1: Feedstock selection ----
feedstock = st.selectbox("Select Feedstock Type", list(FEEDSTOCKS.keys()))
density = FEEDSTOCKS[feedstock]["density"]
yield_factor = FEEDSTOCKS[feedstock]["yield_factor"]
default_height = FEEDSTOCKS[feedstock]["default_height"]

# ---- Step 2: Land Area Input ----
st.header("Land Area Input")

area_method = st.radio(
    "Choose method to input land area:",
    ("Direct entry (hectares)", "Polygon coordinates", "Upload JPEG image")
)

area_m2 = 0
uploaded_img = None
resolution = None

if area_method == "Direct entry (hectares)":
    area_ha = st.number_input("Enter land area (hectares)", min_value=0.0, step=0.1)
    area_m2 = area_ha * 10000

elif area_method == "Polygon coordinates":
    coords_text = st.text_area(
        "Enter polygon coordinates as lat,lon pairs (one per line)"
    )
    if coords_text.strip():
        try:
            coords = []
            for line in coords_text.strip().split("\n"):
                lat, lon = map(float, line.split(","))
                coords.append((lon, lat))  # Shapely uses (x,y) = (lon,lat)
            polygon = Polygon(coords)
            area_m2 = polygon.area * (111000**2)  # rough conversion
        except Exception as e:
            st.error(f"Invalid coordinates format: {e}")

elif area_method == "Upload JPEG image":
    # First ask for source
    img_source = st.selectbox(
        "Select image source:",
        list(RESOLUTIONS.keys())
    )
    resolution = RESOLUTIONS[img_source]

    # Then allow image upload
    uploaded_img = st.file_uploader("Upload JPEG image", type=["jpg", "jpeg"])
    if uploaded_img:
        img = Image.open(uploaded_img)
        width, height = img.size
        area_m2 = (width * resolution) * (height * resolution)

# ---- Step 3: Pile height ----
pile_height = st.number_input(
    f"Enter pile height (m) [default: {default_height} m]",
    min_value=0.1,
    step=0.1,
    value=default_height,
)

# ---- Step 4: Calculations ----
if area_m2 > 0:
    volume_m3 = area_m2 * pile_height
    biomass_mass = volume_m3 * density
    biochar_yield = biomass_mass * yield_factor
    area_ha = area_m2 / 10000
    application_rate = biochar_yield / area_ha if area_ha > 0 else 0

    st.success("✅ Estimation Results")
    st.write(f"**Biochar Yield:** {biochar_yield:.2f} kg")
    st.write(f"**Land Area Covered:** {area_ha:.2f} hectares")
    st.write(f"**Application Rate:** {application_rate:.2f} kg/ha")

    with st.expander("Calculation Details"):
        st.write(f"Volume = Area × Height = {area_m2:.2f} m² × {pile_height} m = {volume_m3:.2f} m³")
        st.write(f"Biomass Mass = Volume × Density = {volume_m3:.2f} × {density} = {biomass_mass:.2f} kg")
        st.write(f"Biochar Yield = Biomass Mass × Yield Factor = {biomass_mass:.2f} × {yield_factor} = {biochar_yield:.2f} kg")
        st.write(f"Application Rate = {biochar_yield:.2f} ÷ {area_ha:.2f} ha = {application_rate:.2f} kg/ha")
