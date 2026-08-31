"""
CAD Loader

Supported

STEP
STP
IGES
IGS
BREP
"""

import os
import cadquery as cq

from OCP.STEPControl import STEPControl_Reader
from OCP.IGESControl import IGESControl_Reader
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.IFSelect import IFSelect_RetDone
from OCP.TopoDS import TopoDS_Shape


def validate_file(file_path):

    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    extension = os.path.splitext(file_path)[1].lower()

    supported = [
        ".step",
        ".stp",
        ".iges",
        ".igs",
        ".brep"
    ]

    if extension not in supported:

        raise Exception(
            f"{extension} not supported."
        )

    return extension


def load_step(file_path):

    return cq.importers.importStep(file_path)


def load_iges(file_path):

    reader = IGESControl_Reader()

    status = reader.ReadFile(file_path)

    if status != IFSelect_RetDone:

        raise Exception(
            "Unable to read IGES file."
        )

    reader.TransferRoots()

    shape = reader.OneShape()

    return shape


def load_brep(file_path):

    builder = BRep_Builder()

    shape = TopoDS_Shape()

    ok = BRepTools.Read_s(
        shape,
        file_path,
        builder
    )

    if not ok:

        raise Exception(
            "Unable to read BREP."
        )

    return shape


def load_cad_model(file_path):

    extension = validate_file(file_path)

    if extension in [

        ".step",
        ".stp"

    ]:

        return load_step(file_path)


    elif extension in [

        ".iges",
        ".igs"

    ]:

        return load_iges(file_path)


    elif extension == ".brep":

        return load_brep(file_path)


    raise Exception("Unsupported CAD file.")