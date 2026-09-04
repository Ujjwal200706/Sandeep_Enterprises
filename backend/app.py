import os
import uuid
import tempfile
from typing import Dict, Optional

import gradio as gr

from flask import Flask, jsonify, request
from flask_cors import CORS

import config
from cad_engine.pipeline import CADPipeline
from inquiry_manager import InquiryManager
from email_service import EmailService
from supabase_service import SupabaseService
from utils import allowed_file


# =====================================================
# FLASK APP
# =====================================================

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


# =====================================================
# SERVICES
# =====================================================

cad_pipeline = CADPipeline()
inquiry_manager = InquiryManager()
email_service = EmailService()
supabase_service = SupabaseService()


# =====================================================
# HOME / HEALTH CHECK / DIAGNOSTICS
# =====================================================

@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "service": "Sandeep Enterprises RFQ & CAD API",
        "version": "2.0",
        "supabase_connected": supabase_service.is_configured(),
        "supabase_cad_bucket": config.SUPABASE_CAD_BUCKET,
        "supabase_product_images_bucket": config.SUPABASE_PRODUCT_IMAGES_BUCKET,
        "supabase_table": config.SUPABASE_CAD_TABLE
    })


@app.route("/supabase-status", methods=["GET"])
@app.route("/api/supabase-status", methods=["GET"])
def supabase_status():
    """
    Performs a real-time diagnostics check against Supabase storage buckets and database.
    """
    status = supabase_service.test_connection()
    status_code = 200 if (status.get("configured") and status.get("database_connected")) else 503
    return jsonify(status), status_code



# =====================================================
# HELPER FUNCTIONS
# =====================================================

def parse_or_generate_client_id(raw_id: Optional[str]) -> str:
    """
    Validates provided client_id as UUID, or generates a new valid UUID.
    """
    if raw_id:
        try:
            return str(uuid.UUID(raw_id.strip()))
        except ValueError:
            pass
    return str(uuid.uuid4())


def allowed_cad_file(filename: str) -> bool:
    return allowed_file(filename, config.ALLOWED_EXTENSIONS)


# =====================================================
# SUBMIT MANUFACTURING INQUIRY
# =====================================================

@app.route("/submit-inquiry", methods=["POST"])
def submit_inquiry():
    """
    Processes manufacturing inquiries with either CAD models or product images.
    - Uses temporary memory/directories during request execution.
    - Uploads CAD files & rendered view images to Supabase Storage.
    - Saves rendered image URLs into the `client_cad_data` Supabase database table.
    - Dispatches email notifications.
    - Leaves NO persistent files on local disk.
    """
    try:
        # ---------------------------------------------
        # CUSTOMER DETAILS & CLIENT ID
        # ---------------------------------------------
        customer = {
            "name": request.form.get("name", "").strip(),
            "company": request.form.get("company", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "city": request.form.get("city", "").strip(),
            "state": request.form.get("state", "").strip()
        }

        requirement = request.form.get("message", "").strip()
        upload_type = request.form.get("upload_type", "").upper()
        client_id = parse_or_generate_client_id(request.form.get("client_id"))

        # ---------------------------------------------
        # BASIC VALIDATION
        # ---------------------------------------------
        required_fields = ["name", "email", "phone"]
        for field in required_fields:
            if not customer[field]:
                return jsonify({
                    "success": False,
                    "message": f"{field.title()} is required."
                }), 400

        if upload_type not in ["CAD", "IMAGE"]:
            return jsonify({
                "success": False,
                "message": "Invalid upload type. Must be 'CAD' or 'IMAGE'."
            }), 400

        # ---------------------------------------------
        # ISOLATED TEMPORARY DIRECTORY FOR PROCESSING
        # ---------------------------------------------
        with tempfile.TemporaryDirectory(prefix="rfq_session_") as temp_dir:
            cad_url = None
            rendered_image_urls: Dict[str, Optional[str]] = {}
            uploaded_image_urls = []
            cad_record = None

            temp_cad_path = None
            temp_rendered_paths = []
            temp_uploaded_paths = []

            # =========================================
            # PROCESS CAD UPLOAD & RENDERING
            # =========================================
            if upload_type == "CAD":
                if "cad_file" not in request.files:
                    return jsonify({
                        "success": False,
                        "message": "Please upload a CAD file."
                    }), 400

                cad = request.files["cad_file"]
                if not cad or cad.filename == "":
                    return jsonify({
                        "success": False,
                        "message": "No CAD file selected."
                    }), 400

                if not allowed_cad_file(cad.filename):
                    return jsonify({
                        "success": False,
                        "message": "Unsupported CAD file format."
                    }), 400

                # Save CAD file temporarily for rendering
                ext = os.path.splitext(cad.filename)[1].lower()
                temp_cad_path = os.path.join(temp_dir, f"model_{uuid.uuid4().hex[:8]}{ext}")
                cad.save(temp_cad_path)

                # Render 6 views into temp render directory
                render_dir = os.path.join(temp_dir, "renders")
                render_result = cad_pipeline.process(temp_cad_path, output_folder=render_dir)
                temp_rendered_paths = render_result.get("rendered_files", [])

                # 1. Upload original CAD file to Supabase Storage
                try:
                    cad_url = supabase_service.upload_cad_file(
                        file_path=temp_cad_path,
                        original_filename=cad.filename,
                        client_id=client_id
                    )
                except Exception as e:
                    print(f"[WARNING] CAD file upload error: {e}")

                # 2. Upload 6 rendered images to Supabase Storage
                rendered_image_urls = supabase_service.upload_rendered_views(
                    rendered_images=temp_rendered_paths,
                    client_id=client_id
                )

                # 3. Save URLs into client_cad_data database table
                try:
                    cad_record = supabase_service.save_client_cad_data(
                        client_id=client_id,
                        image_urls=rendered_image_urls
                    )
                except Exception as e:
                    print(f"[WARNING] Database insert error: {e}")

            # =========================================
            # PROCESS PRODUCT IMAGES UPLOAD
            # =========================================
            else:
                uploaded_files = request.files.getlist("product_images")
                valid_files = [f for f in uploaded_files if f and f.filename != ""]

                if len(valid_files) == 0:
                    return jsonify({
                        "success": False,
                        "message": "Please upload at least one product image."
                    }), 400

                for img_file in valid_files:
                    ext = os.path.splitext(img_file.filename)[1].lower() or ".png"
                    img_path = os.path.join(temp_dir, f"img_{uuid.uuid4().hex[:8]}{ext}")
                    img_file.save(img_path)
                    temp_uploaded_paths.append(img_path)

                # Upload product images to Supabase Storage
                uploaded_image_urls = supabase_service.upload_product_images(
                    image_paths=temp_uploaded_paths,
                    client_id=client_id
                )

            # ---------------------------------------------
            # CREATE IN-MEMORY INQUIRY
            # ---------------------------------------------
            inquiry = inquiry_manager.create_inquiry(
                customer=customer,
                upload_type=upload_type,
                requirement=requirement,
                client_id=client_id,
                cad_url=cad_url,
                rendered_image_urls=rendered_image_urls,
                uploaded_image_urls=uploaded_image_urls,
                original_filename=request.files["cad_file"].filename if upload_type == "CAD" and "cad_file" in request.files else None
            )

            # ---------------------------------------------
            # DISPATCH EMAILS (ATTACHING TEMP FILES DURING REQUEST)
            # ---------------------------------------------
            try:
                email_service.send_inquiry(
                    inquiry=inquiry,
                    cad_file=temp_cad_path,
                    rendered_images=temp_rendered_paths,
                    uploaded_images=temp_uploaded_paths
                )
            except Exception as e:
                print(f"[WARNING] Email dispatch error: {e}")

            print(f"[SUCCESS] Inquiry {inquiry['inquiry_id']} processed for client_id {client_id}.")

            # ---------------------------------------------
            # SUCCESS RESPONSE
            # ---------------------------------------------
            return jsonify({
                "success": True,
                "message": "Inquiry submitted successfully.",
                "inquiry_id": inquiry["inquiry_id"],
                "client_id": client_id,
                "cad_url": cad_url,
                "image_urls": rendered_image_urls if upload_type == "CAD" else uploaded_image_urls,
                "cad_record": cad_record
            })

    except Exception as e:
        print(f"[ERROR] Exception in submit_inquiry: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =====================================================
# QUERY CAD DATA BY CLIENT ID
# =====================================================

@app.route("/client-cad-data/<client_id>", methods=["GET"])
def get_client_cad_data(client_id):
    """
    Retrieves stored CAD render images and URLs from Supabase table for a given client_id.
    """
    try:
        if not supabase_service.is_configured():
            return jsonify({
                "success": False,
                "message": "Supabase service is not configured."
            }), 503

        response = supabase_service.client.table(config.SUPABASE_CAD_TABLE)\
            .select("*")\
            .eq("client_id", str(client_id))\
            .order("created_at", desc=True)\
            .execute()

        return jsonify({
            "success": True,
            "client_id": client_id,
            "data": response.data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

with gr.Blocks() as demo:
    gr.Markdown("FLASK BACKEND ENGINE ACTIVE")
    gr.Markdown("Your flask api route is active......")

demo.launch(server_name=config.HOST, port=config.PORT, prevent_thread_lock=True)
    

# =====================================================
# START SERVER
# =====================================================

if __name__ == "__main__":
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
