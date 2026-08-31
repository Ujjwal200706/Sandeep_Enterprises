import pyvista as pv


def load_mesh_model(file_path):

    mesh = pv.read(
        file_path
    )

    return mesh