import os
import uuid
from datetime import datetime


def generate_inquiry_id() -> str:
    """
    Generate a unique inquiry ID.
    Example: RFQ-20260724-104532-8A3F
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    random_code = uuid.uuid4().hex[:4].upper()
    return f"RFQ-{timestamp}-{random_code}"


def current_timestamp() -> str:
    """
    Return current timestamp formatted as string.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Check whether uploaded file has an allowed extension.
    """
    if "." not in filename:
        return False
    extension = os.path.splitext(filename)[1].lower()
    return extension in allowed_extensions


def create_upload_filename(filename: str) -> str:
    """
    Generate secure upload filename.
    Example: 4fd8d34c2d1b.step
    """
    extension = os.path.splitext(filename)[1].lower()
    return f"{uuid.uuid4().hex}{extension}"


def human_view_name(filename: str) -> str:
    """
    Convert filename to readable title.
    front.png -> Front View
    """
    name = os.path.splitext(os.path.basename(filename))[0]
    return f"{name.capitalize()} View"