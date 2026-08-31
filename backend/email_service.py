import os
import smtplib
import mimetypes
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List, Dict, Any

import config


class EmailService:

    def __init__(self):
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.sender_email = config.SENDER_EMAIL
        self.sender_password = config.SENDER_PASSWORD
        self.receiver_email = config.RECEIVER_EMAIL

        self.template_folder = os.path.join(
            config.BASE_DIR,
            "templates"
        )

    def is_configured(self) -> bool:
        return bool(self.sender_email and self.sender_password and self.receiver_email)

    # =====================================================
    # SMTP CONNECTION
    # =====================================================

    def _connect(self):
        if not self.is_configured():
            raise ValueError(
                "SMTP configuration is incomplete. "
                "Set SENDER_EMAIL, SENDER_PASSWORD, and RECEIVER_EMAIL environment variables."
            )

        server = smtplib.SMTP(
            self.smtp_server,
            self.smtp_port
        )
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(
            self.sender_email,
            self.sender_password
        )
        return server

    # =====================================================
    # LOAD HTML TEMPLATE
    # =====================================================

    def _load_template(self, filename: str) -> str:
        path = os.path.join(
            self.template_folder,
            filename
        )
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # =====================================================
    # REPLACE TEMPLATE VARIABLES
    # =====================================================

    def _render_template(
        self,
        filename: str,
        inquiry: Dict[str, Any]
    ) -> str:
        html = self._load_template(filename)
        customer = inquiry.get("customer", {})

        replacements = {
            "{{INQUIRY_ID}}": str(inquiry.get("inquiry_id", "")),
            "{{CLIENT_ID}}": str(inquiry.get("client_id", "")),
            "{{NAME}}": str(customer.get("name", "")),
            "{{COMPANY}}": str(customer.get("company", "")),
            "{{EMAIL}}": str(customer.get("email", "")),
            "{{PHONE}}": str(customer.get("phone", "")),
            "{{CITY}}": str(customer.get("city", "")),
            "{{STATE}}": str(customer.get("state", "")),
            "{{UPLOAD_TYPE}}": str(inquiry.get("upload_type", "")),
            "{{REQUIREMENT}}": str(inquiry.get("requirement", ""))
        }

        for key, value in replacements.items():
            html = html.replace(key, value)

        return html

    # =====================================================
    # CREATE EMAIL
    # =====================================================

    def _create_message(
        self,
        recipient: str,
        subject: str,
        reply_to: str
    ) -> MIMEMultipart:
        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = recipient
        message["Subject"] = subject
        message["Reply-To"] = reply_to
        return message

    # =====================================================
    # ATTACH SINGLE FILE
    # =====================================================

    def _attach_file(
        self,
        message: MIMEMultipart,
        filepath: Optional[str]
    ):
        if not filepath or not os.path.exists(filepath):
            return

        content_type, _ = mimetypes.guess_type(filepath)
        if content_type is None:
            content_type = "application/octet-stream"

        maintype, subtype = content_type.split("/", 1)

        with open(filepath, "rb") as file:
            attachment = MIMEBase(maintype, subtype)
            attachment.set_payload(file.read())

        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(filepath)}"'
        )
        message.attach(attachment)

    # =====================================================
    # ATTACH MULTIPLE FILES
    # =====================================================

    def _attach_multiple(
        self,
        message: MIMEMultipart,
        files: Optional[List[str]]
    ):
        if not files:
            return

        for file in files:
            self._attach_file(message, file)

    # =====================================================
    # ATTACH ALL INQUIRY FILES
    # =====================================================

    def _attach_inquiry_files(
        self,
        message: MIMEMultipart,
        cad_file: Optional[str] = None,
        rendered_images: Optional[List[str]] = None,
        uploaded_images: Optional[List[str]] = None
    ):
        self._attach_file(message, cad_file)
        self._attach_multiple(message, rendered_images)
        self._attach_multiple(message, uploaded_images)

    # =====================================================
    # SEND EMAIL TO SANDEEP ENTERPRISES
    # =====================================================

    def send_manufacturer_email(
        self,
        inquiry: Dict[str, Any],
        cad_file: Optional[str] = None,
        rendered_images: Optional[List[str]] = None,
        uploaded_images: Optional[List[str]] = None
    ):
        if not self.is_configured():
            print("[INFO] SMTP not configured. Skipping manufacturer email.")
            return

        html = self._render_template(
            "manufacturer_email.html",
            inquiry
        )

        customer_email = inquiry.get("customer", {}).get("email", "")

        message = self._create_message(
            recipient=self.receiver_email,
            subject=f"New Manufacturing Inquiry | {inquiry['inquiry_id']}",
            reply_to=customer_email or self.receiver_email
        )

        message.attach(
            MIMEText(html, "html", "utf-8")
        )

        self._attach_inquiry_files(
            message,
            cad_file=cad_file,
            rendered_images=rendered_images,
            uploaded_images=uploaded_images
        )

        server = self._connect()
        try:
            server.sendmail(
                self.sender_email,
                self.receiver_email,
                message.as_string()
            )
        finally:
            server.quit()

    # =====================================================
    # SEND CONFIRMATION EMAIL TO CUSTOMER
    # =====================================================

    def send_customer_email(
        self,
        inquiry: Dict[str, Any],
        cad_file: Optional[str] = None,
        rendered_images: Optional[List[str]] = None,
        uploaded_images: Optional[List[str]] = None
    ):
        customer_email = inquiry.get("customer", {}).get("email")
        if not customer_email or not self.is_configured():
            return

        html = self._render_template(
            "customer_email.html",
            inquiry
        )

        message = self._create_message(
            recipient=customer_email,
            subject=f"Inquiry Received | {inquiry['inquiry_id']}",
            reply_to=self.receiver_email
        )

        message.attach(
            MIMEText(html, "html", "utf-8")
        )

        self._attach_inquiry_files(
            message,
            cad_file=cad_file,
            rendered_images=rendered_images,
            uploaded_images=uploaded_images
        )

        server = self._connect()
        try:
            server.sendmail(
                self.sender_email,
                customer_email,
                message.as_string()
            )
        finally:
            server.quit()

    # =====================================================
    # MASTER FUNCTION
    # =====================================================

    def send_inquiry(
        self,
        inquiry: Dict[str, Any],
        cad_file: Optional[str] = None,
        rendered_images: Optional[List[str]] = None,
        uploaded_images: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sends both manufacturer notification and customer acknowledgement.
        """
        try:
            self.send_manufacturer_email(
                inquiry=inquiry,
                cad_file=cad_file,
                rendered_images=rendered_images,
                uploaded_images=uploaded_images
            )

            self.send_customer_email(
                inquiry=inquiry,
                cad_file=cad_file,
                rendered_images=rendered_images,
                uploaded_images=uploaded_images
            )

            return {
                "success": True,
                "message": "Emails sent successfully."
            }
        except Exception as e:
            print(f"[WARNING] Email sending failed: {e}")
            return {
                "success": False,
                "message": str(e)
            }