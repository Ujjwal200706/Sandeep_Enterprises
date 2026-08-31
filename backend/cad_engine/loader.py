import os

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IGESControl import IGESControl_Reader
from OCC.Core.BRepTools import breptools_Read
from OCC.Core.BRep import BRep_Builder

from OCC.Core.IFSelect import IFSelect_RetDone


def load_cad_file(file_path):

    if not os.path.exists(file_path):
        raise Exception(
            "CAD file does not exist"
        )


    extension = (
        os.path.splitext(file_path)[1]
        .lower()
    )


    # -----------------------------
    # STEP / STP
    # -----------------------------

    if extension in [
        ".step",
        ".stp"
    ]:

        reader = STEPControl_Reader()


        status = reader.ReadFile(
            file_path
        )


        if status != IFSelect_RetDone:

            raise Exception(
                "STEP loading failed"
            )


        reader.TransferRoots()


        shape = reader.OneShape()


        return shape



    # -----------------------------
    # IGES
    # -----------------------------

    elif extension in [
        ".iges",
        ".igs"
    ]:


        reader = IGESControl_Reader()


        status = reader.ReadFile(
            file_path
        )


        if status != IFSelect_RetDone:

            raise Exception(
                "IGES loading failed"
            )


        reader.TransferRoots()


        shape = reader.OneShape()


        return shape



    # -----------------------------
    # BREP
    # -----------------------------

    elif extension == ".brep":


        builder = BRep_Builder()

        shape = None


        breptools_Read(
            shape,
            file_path,
            builder
        )


        return shape



    else:

        raise Exception(
            f"Unsupported CAD format: {extension}"
        )