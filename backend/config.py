import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# ==============================
# Project Paths
# ==============================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ==============================
# Supabase Configuration
# ==============================

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()

SUPABASE_KEY = os.environ.get(
    "SUPABASE_SERVICE_ROLE_KEY",
    os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_ANON_KEY", ""))
).strip()

# Supabase Storage bucket for CAD models and rendered 6-camera views
SUPABASE_CAD_BUCKET = os.environ.get(
    "SUPABASE_CAD_BUCKET",
    os.environ.get("SUPABASE_BUCKET", "cad-files")
).strip()

# Supabase Storage bucket for customer product images
SUPABASE_PRODUCT_IMAGES_BUCKET = os.environ.get(
    "SUPABASE_PRODUCT_IMAGES_BUCKET",
    "product-images"
).strip()

# Supabase database table name for CAD renders
SUPABASE_CAD_TABLE = os.environ.get("SUPABASE_CAD_TABLE", "client_cad_data").strip()



# ==============================
# Flask Configuration
# ==============================

HOST = os.environ.get("HOST", "0.0.0.0")

PORT = int(os.environ.get("PORT", 5000))

DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")


# ==============================
# Allowed CAD Files
# ==============================

ALLOWED_EXTENSIONS = {
    ".stp",
    ".step",
    ".stl",
    ".iges",
    ".igs",
    ".obj",
    ".brep",
    ".fcstd",
    ".ply",
    ".off",
    ".gltf",
    ".glb",
    ".3mf"
}


# ==============================
# Render Settings
# ==============================

IMAGE_WIDTH = 1200

IMAGE_HEIGHT = 1200

IMAGE_FORMAT = "PNG"

CAMERA_VIEWS = [
    "front",
    "back",
    "left",
    "right",
    "top",
    "bottom"
]


# ==============================
# EMAIL CONFIGURATION
# ==============================

SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")

SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "ujjwal3901@gmail.com")

SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "cmyfilphxmleytaa")

RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "shweta181278@gmail.com")

EMAIL_SUBJECT = "New Manufacturing Inquiry"