import os
import tempfile
from typing import Optional, Dict, Any

from cad_engine.universal_loader import load_model
from cad_engine.mesh_converter import MeshConverter
from cad_engine.renderer import UniversalRenderer
from cad_engine.analyzer import ModelAnalyzer


class CADPipeline:

    def __init__(self):
        self.converter = MeshConverter()
        self.renderer = UniversalRenderer()

    def process(self, cad_file: str, output_folder: Optional[str] = None) -> Dict[str, Any]:
        """
        Loads CAD file, converts to mesh, runs analysis, and renders 6 view PNGs into output_folder.
        """
        # ------------------------
        # Load Model
        # ------------------------
        model, model_type = load_model(cad_file)

        # ------------------------
        # Convert
        # ------------------------
        mesh = self.converter.convert(
            model,
            model_type
        )

        # ------------------------
        # Analyze
        # ------------------------
        analysis = ModelAnalyzer(mesh).analyze()

        # ------------------------
        # Render
        # ------------------------
        if not output_folder:
            output_folder = tempfile.mkdtemp(prefix="cad_render_")

        os.makedirs(output_folder, exist_ok=True)

        self.renderer.render_views(
            mesh,
            output_folder
        )

        # Collect rendered view image file paths
        image_order = [
            "front.png",
            "back.png",
            "left.png",
            "right.png",
            "top.png",
            "bottom.png",
        ]

        rendered_files = []
        for image_name in image_order:
            image_path = os.path.join(output_folder, image_name)
            if os.path.exists(image_path):
                rendered_files.append(image_path)

        return {
            "analysis": analysis,
            "render_folder": output_folder,
            "rendered_files": rendered_files
        }