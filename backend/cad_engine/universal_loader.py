"""
Universal CAD Loader
Supports

STEP
STP
IGES
IGS
BREP
STL
OBJ
PLY
OFF
GLTF
GLB
3MF
"""

import os

from cad_engine.cad_loader import load_cad_model
from cad_engine.mesh_loader import load_mesh_model


CAD_EXTENSIONS = {
    ".step",
    ".stp",
    ".iges",
    ".igs",
    ".brep"
}


MESH_EXTENSIONS = {
    ".stl",
    ".obj",
    ".ply",
    ".off",
    ".gltf",
    ".glb",
    ".3mf"
}


def load_model(file_path):

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            file_path
        )


    extension = os.path.splitext(
        file_path
    )[1].lower()


    # -------------------------

    # CAD FILES

    # -------------------------

    if extension in CAD_EXTENSIONS:

        model = load_cad_model(
            file_path
        )

        return model, "CAD"


    # -------------------------

    # MESH FILES

    # -------------------------

    elif extension in MESH_EXTENSIONS:

        model = load_mesh_model(
            file_path
        )

        return model, "MESH"


    else:

        raise Exception(
            f"Unsupported file format : {extension}"
        )