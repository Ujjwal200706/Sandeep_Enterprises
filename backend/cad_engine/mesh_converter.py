"""
Universal Mesh Converter

Converts all supported models into a PyVista PolyData
"""

import pyvista as pv
import tempfile
import os
import cadquery as cq


class MeshConverter:

    def __init__(self):
        pass

    # -----------------------------------------
    # CAD → Mesh
    # -----------------------------------------

    def cad_to_mesh(self, workplane):

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".stl",
            delete=False
        )

        temp_path = temp_file.name

        temp_file.close()

        cq.exporters.export(
            workplane,
            temp_path
        )  # export CAD to a temporary STL file for mesh conversion

        mesh = pv.read(temp_path)

        os.remove(temp_path)  # remove the temporary STL file after conversion

        return mesh

    # -----------------------------------------
    # Mesh → Mesh
    # -----------------------------------------

    def mesh_to_mesh(self, mesh):

        return mesh

    # -----------------------------------------
    # Universal
    # -----------------------------------------

    def convert(
        self,
        model,
        model_type
    ):

        if model_type == "CAD":

            return self.cad_to_mesh(model)

        elif model_type == "MESH":

            return self.mesh_to_mesh(model)

        else:

            raise Exception(
                "Unknown model type."
            )