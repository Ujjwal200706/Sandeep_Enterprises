import os
import uuid
import mimetypes
from typing import Dict, List, Optional, Union, Any

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

import config


class SupabaseService:
    """
    Manages all storage and database interactions with Supabase:
    - Uploading CAD files to `cad-files` Supabase Storage bucket
    - Uploading 6-view rendered images to `cad-files` Supabase Storage bucket
    - Uploading customer product photos to `product-images` Supabase Storage bucket
    - Saving CAD render URLs to `client_cad_data` table
    """

    def __init__(self):
        self.url = config.SUPABASE_URL
        self.key = config.SUPABASE_KEY
        self.cad_bucket = config.SUPABASE_CAD_BUCKET
        self.product_images_bucket = config.SUPABASE_PRODUCT_IMAGES_BUCKET
        self.table_name = config.SUPABASE_CAD_TABLE
        self.client: Optional[Client] = None

        if self.url and self.key and create_client:
            try:
                self.client = create_client(self.url, self.key)
                print(
                    f"[INFO] Supabase client initialized successfully.\n"
                    f"       URL: {self.url}\n"
                    f"       CAD Bucket: {self.cad_bucket}\n"
                    f"       Product Images Bucket: {self.product_images_bucket}\n"
                    f"       Table: {self.table_name}"
                )
            except Exception as e:
                print(f"[WARNING] Failed to initialize Supabase client: {e}")
        else:
            print(
                "[WARNING] Supabase credentials not fully configured. "
                "Set SUPABASE_URL and SUPABASE_KEY in environment or .env"
            )

    def is_configured(self) -> bool:
        """Check if Supabase client is ready for operations."""
        return self.client is not None

    def upload_file(
        self,
        destination_path: str,
        file_path_or_bytes: Union[str, bytes],
        content_type: Optional[str] = None,
        bucket_name: Optional[str] = None
    ) -> str:
        """
        Uploads a file or bytes to a Supabase Storage bucket and returns its public URL.
        """
        target_bucket = bucket_name or self.cad_bucket

        if not self.is_configured():
            print(f"[SUPABASE MOCK] upload_file {destination_path} to {target_bucket} (Supabase not configured)")
            return f"https://mock-storage.supabase.co/{target_bucket}/{destination_path}"

        try:
            if isinstance(file_path_or_bytes, str):
                if not os.path.exists(file_path_or_bytes):
                    raise FileNotFoundError(f"File not found: {file_path_or_bytes}")
                with open(file_path_or_bytes, "rb") as f:
                    file_data = f.read()
                if not content_type:
                    content_type = mimetypes.guess_type(file_path_or_bytes)[0] or "application/octet-stream"
            else:
                file_data = file_path_or_bytes
                if not content_type:
                    content_type = "application/octet-stream"

            file_options = {
                "content-type": content_type,
                "upsert": "true"
            }

            # Perform the upload
            self.client.storage.from_(target_bucket).upload(
                path=destination_path,
                file=file_data,
                file_options=file_options
            )

            # Get public URL
            public_url = self.client.storage.from_(target_bucket).get_public_url(destination_path)
            return public_url

        except Exception as e:
            print(f"[ERROR] Supabase Storage upload error in '{target_bucket}' for '{destination_path}': {e}")
            raise e

    def upload_cad_file(
        self,
        file_path: str,
        original_filename: str,
        client_id: str
    ) -> str:
        """
        Uploads the original CAD model file to the `cad-files` Supabase Storage bucket.
        """
        ext = os.path.splitext(original_filename)[1].lower()
        unique_file = f"{uuid.uuid4().hex}{ext}"
        destination_path = f"{client_id}/cad/{unique_file}"
        content_type = mimetypes.guess_type(original_filename)[0] or "application/octet-stream"

        return self.upload_file(
            destination_path=destination_path,
            file_path_or_bytes=file_path,
            content_type=content_type,
            bucket_name=self.cad_bucket
        )

    def upload_rendered_views(
        self,
        rendered_images: Union[List[str], Dict[str, str]],
        client_id: str
    ) -> Dict[str, Optional[str]]:
        """
        Uploads the 6 camera view PNGs (front, back, left, right, top, bottom)
        to the `cad-files` Supabase Storage bucket and returns a dictionary of
        public URLs mapped to `image_1_url` through `image_6_url`.

        Mapping:
        1 -> front
        2 -> back
        3 -> left
        4 -> right
        5 -> top
        6 -> bottom
        """
        view_names = ["front", "back", "left", "right", "top", "bottom"]
        urls_by_view: Dict[str, Optional[str]] = {}

        # Normalize input to a dict mapping view name -> file path
        if isinstance(rendered_images, list):
            path_map = {}
            for path in rendered_images:
                base = os.path.basename(path).lower()
                for view in view_names:
                    if view in base:
                        path_map[view] = path
                        break
            # If not matched by name, map by index
            if not path_map and rendered_images:
                for idx, path in enumerate(rendered_images):
                    if idx < len(view_names):
                        path_map[view_names[idx]] = path
        else:
            path_map = rendered_images

        # Upload each view image
        for idx, view in enumerate(view_names, start=1):
            image_key = f"image_{idx}_url"
            file_path = path_map.get(view)

            if file_path and os.path.exists(file_path):
                dest_path = f"{client_id}/renders/{view}.png"
                try:
                    uploaded_url = self.upload_file(
                        destination_path=dest_path,
                        file_path_or_bytes=file_path,
                        content_type="image/png",
                        bucket_name=self.cad_bucket
                    )
                    urls_by_view[image_key] = uploaded_url
                except Exception as e:
                    print(f"[ERROR] Failed to upload render view {view}: {e}")
                    urls_by_view[image_key] = None
            else:
                urls_by_view[image_key] = None

        return urls_by_view

    def upload_product_images(
        self,
        image_paths: List[str],
        client_id: str
    ) -> List[str]:
        """
        Uploads customer product photos to the `product-images` Supabase Storage bucket
        and returns the public URLs.
        """
        uploaded_urls = []
        for idx, img_path in enumerate(image_paths, start=1):
            if not os.path.exists(img_path):
                continue
            ext = os.path.splitext(img_path)[1].lower() or ".png"
            dest_path = f"{client_id}/products/image_{idx}_{uuid.uuid4().hex[:6]}{ext}"
            content_type = mimetypes.guess_type(img_path)[0] or "image/png"
            try:
                url = self.upload_file(
                    destination_path=dest_path,
                    file_path_or_bytes=img_path,
                    content_type=content_type,
                    bucket_name=self.product_images_bucket
                )
                uploaded_urls.append(url)
            except Exception as e:
                print(f"[ERROR] Failed to upload product image {img_path} to '{self.product_images_bucket}': {e}")

        return uploaded_urls

    def save_client_cad_data(
        self,
        client_id: str,
        image_urls: Dict[str, Optional[str]]
    ) -> dict:
        """
        Inserts a record into the `client_cad_data` Supabase table.
        Table Schema:
          id uuid default gen_random_uuid() primary key,
          client_id uuid not null,
          image_1_url text,
          image_2_url text,
          image_3_url text,
          image_4_url text,
          image_5_url text,
          image_6_url text,
          created_at timestamp with time zone default timezone('utc'::text, now()) not null
        """
        record = {
            "client_id": str(client_id),
            "image_1_url": image_urls.get("image_1_url"),
            "image_2_url": image_urls.get("image_2_url"),
            "image_3_url": image_urls.get("image_3_url"),
            "image_4_url": image_urls.get("image_4_url"),
            "image_5_url": image_urls.get("image_5_url"),
            "image_6_url": image_urls.get("image_6_url"),
        }

        if not self.is_configured():
            print(f"[SUPABASE MOCK] Insert into {self.table_name}: {record}")
            record["id"] = str(uuid.uuid4())
            return record

        try:
            response = self.client.table(self.table_name).insert(record).execute()
            if response.data and len(response.data) > 0:
                print(f"[SUCCESS] Saved CAD render data to '{self.table_name}' with ID: {response.data[0].get('id')}")
                return response.data[0]
            return record
        except Exception as e:
            print(f"[ERROR] Failed to insert record into Supabase table '{self.table_name}': {e}")
            raise e

    def test_connection(self) -> Dict[str, Any]:
        """
        Tests connectivity to Supabase URL, storage buckets, and database table.
        Returns a diagnostic status dictionary.
        """
        status: Dict[str, Any] = {
            "configured": self.is_configured(),
            "url": self.url or "Not Set",
            "cad_bucket": self.cad_bucket,
            "product_images_bucket": self.product_images_bucket,
            "table": self.table_name,
            "database_connected": False,
            "cad_bucket_accessible": False,
            "product_images_bucket_accessible": False,
            "errors": [],
            "tips": []
        }

        if not self.is_configured():
            status["errors"].append("Supabase client is not initialized. Check SUPABASE_URL and SUPABASE_KEY.")
            return status

        # 1. Test database table query
        try:
            res = self.client.table(self.table_name).select("*").limit(1).execute()
            status["database_connected"] = True
        except Exception as e:
            err_msg = str(e)
            status["errors"].append(f"Database table '{self.table_name}' error: {err_msg}")
            if "row-level security" in err_msg.lower() or "42501" in err_msg:
                status["tips"].append(
                    f"Table '{self.table_name}' RLS policy blocks access. Use SUPABASE_SERVICE_ROLE_KEY or add a SELECT policy."
                )

        # 2. Test CAD bucket
        try:
            test_path = f"_health_check_{uuid.uuid4().hex[:6]}.txt"
            self.client.storage.from_(self.cad_bucket).upload(
                path=test_path,
                file=b"health_check",
                file_options={"content-type": "text/plain", "upsert": "true"}
            )
            # Remove test file
            self.client.storage.from_(self.cad_bucket).remove([test_path])
            status["cad_bucket_accessible"] = True
        except Exception as e:
            err_msg = str(e)
            status["errors"].append(f"CAD bucket '{self.cad_bucket}' error: {err_msg}")
            if "row-level security" in err_msg.lower() or "403" in err_msg:
                status["tips"].append(
                    f"Bucket '{self.cad_bucket}' requires SUPABASE_SERVICE_ROLE_KEY or an INSERT policy for anon role."
                )
            elif "not found" in err_msg.lower() or "404" in err_msg:
                status["tips"].append(
                    f"Bucket '{self.cad_bucket}' does not exist in your Supabase project. Please create it in Supabase Storage."
                )

        # 3. Test Product Images bucket
        try:
            test_path = f"_health_check_{uuid.uuid4().hex[:6]}.txt"
            self.client.storage.from_(self.product_images_bucket).upload(
                path=test_path,
                file=b"health_check",
                file_options={"content-type": "text/plain", "upsert": "true"}
            )
            # Remove test file
            self.client.storage.from_(self.product_images_bucket).remove([test_path])
            status["product_images_bucket_accessible"] = True
        except Exception as e:
            err_msg = str(e)
            status["errors"].append(f"Product Images bucket '{self.product_images_bucket}' error: {err_msg}")
            if "row-level security" in err_msg.lower() or "403" in err_msg:
                status["tips"].append(
                    f"Bucket '{self.product_images_bucket}' requires SUPABASE_SERVICE_ROLE_KEY or an INSERT policy for anon role."
                )
            elif "not found" in err_msg.lower() or "404" in err_msg:
                status["tips"].append(
                    f"Bucket '{self.product_images_bucket}' does not exist in your Supabase project. Please create it in Supabase Storage."
                )

        return status
