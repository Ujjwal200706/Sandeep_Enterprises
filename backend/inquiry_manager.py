from datetime import datetime
from typing import Optional, Dict, Any, List


class InquiryManager:
    """
    Manages in-memory manufacturing inquiries without storing JSON files on disk.
    """

    def __init__(self):
        pass

    # =====================================================
    # GENERATE INQUIRY ID
    # =====================================================

    @staticmethod
    def generate_inquiry_id() -> str:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"SE-RFQ-{timestamp}"

    # =====================================================
    # BUILD INQUIRY OBJECT
    # =====================================================

    def create_inquiry(
        self,
        customer: Dict[str, str],
        upload_type: str,
        requirement: str,
        client_id: Optional[str] = None,
        cad_url: Optional[str] = None,
        rendered_image_urls: Optional[Dict[str, Optional[str]]] = None,
        uploaded_image_urls: Optional[List[str]] = None,
        original_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Constructs an in-memory inquiry object for notifications and responses.
        No local file storage is used.
        """
        inquiry_id = self.generate_inquiry_id()

        inquiry = {
            "inquiry_id": inquiry_id,
            "client_id": client_id,
            "submitted_at": datetime.now().isoformat(),
            "customer": customer,
            "upload_type": upload_type,
            "requirement": requirement,
            "original_filename": original_filename,
            "cad_url": cad_url,
            "rendered_image_urls": rendered_image_urls or {},
            "uploaded_image_urls": uploaded_image_urls or []
        }

        return inquiry