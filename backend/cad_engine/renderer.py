import os
import pyvista as pv


class UniversalRenderer:

    def __init__(self):
        pass

    def render_views(self, mesh, output_folder):

        os.makedirs(output_folder, exist_ok=True)  # ensure output folder exists for rendered images

        center = mesh.center
        bounds = mesh.bounds

        dx = bounds[1] - bounds[0]
        dy = bounds[3] - bounds[2]
        dz = bounds[5] - bounds[4]

        distance = max(dx, dy, dz) * 3

        views = {
            "front":  ((0, -distance, 0), (0, 0, 1)),
            "back":   ((0,  distance, 0), (0, 0, 1)),
            "left":   ((-distance, 0, 0), (0, 0, 1)),
            "right":  (( distance, 0, 0), (0, 0, 1)),
            "top":    ((0, 0, distance), (0, 1, 0)),
            "bottom": ((0, 0, -distance), (0, 1, 0)),
        }

        for name, (offset, up) in views.items():

            print(f"Rendering {name}")

            plotter = pv.Plotter(
                off_screen=True,
                window_size=(1800, 1800)
            )

            plotter.set_background("white")

            plotter.add_mesh(
                mesh,
                color="lightgray",
                smooth_shading=True,
                show_edges=False
            )

            camera_position = (
                center[0] + offset[0],
                center[1] + offset[1],
                center[2] + offset[2],
            )

            plotter.camera_position = [
                camera_position,
                center,
                up,
            ]

            plotter.camera.parallel_projection = True

            # Render first
            plotter.render()

            # Reset to fit the entire model
            plotter.reset_camera()

            # Zoom out slightly (1.0 = no zoom)
            plotter.camera.Zoom(0.8)

            filename = os.path.join(
                output_folder,
                f"{name}.png"
            )

            plotter.screenshot(filename)  # save rendered view image to disk

            plotter.close()

            print(f"Saved -> {filename}")