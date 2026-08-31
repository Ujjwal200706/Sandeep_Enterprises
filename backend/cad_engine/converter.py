from OCC.Core.BRepMesh import (
    BRepMesh_IncrementalMesh
)



def convert_to_mesh(
        shape,
        quality=0.1
):


    if shape is None:

        raise Exception(
            "Invalid CAD shape"
        )


    mesh = BRepMesh_IncrementalMesh(
        shape,
        quality
    )


    mesh.Perform()


    return shape