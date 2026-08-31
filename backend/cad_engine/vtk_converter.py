import vtk

from OCC.Extend.ShapeTesselator import ShapeTesselator


def shape_to_polydata(shape):

    """
    Converts an OCC TopoDS_Shape
    into vtkPolyData.
    """

    tess = ShapeTesselator(shape)

    tess.Compute(
        compute_edges=False,
        mesh_quality=1.0,
        parallel=True
    )

    vertices = tess.GetVerticesPosition()

    triangles = tess.GetTriangleIndices()

    points = vtk.vtkPoints()

    for i in range(0, len(vertices), 3):

        points.InsertNextPoint(
            vertices[i],
            vertices[i + 1],
            vertices[i + 2]
        )

    cells = vtk.vtkCellArray()

    for i in range(0, len(triangles), 3):

        triangle = vtk.vtkTriangle()

        triangle.GetPointIds().SetId(
            0,
            triangles[i]
        )

        triangle.GetPointIds().SetId(
            1,
            triangles[i + 1]
        )

        triangle.GetPointIds().SetId(
            2,
            triangles[i + 2]
        )

        cells.InsertNextCell(
            triangle
        )

    poly = vtk.vtkPolyData()

    poly.SetPoints(points)

    poly.SetPolys(cells)

    return poly