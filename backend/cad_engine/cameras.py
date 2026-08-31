import numpy as np


VIEWS = {

    "front": (

        (0, 0, 1),

        (0, 1, 0)

    ),

    "back": (

        (0, 0, -1),

        (0, 1, 0)

    ),

    "left": (

        (-1, 0, 0),

        (0, 0, 1)

    ),

    "right": (

        (1, 0, 0),

        (0, 0, 1)

    ),

    "top": (

        (0, 1, 0),

        (0, 0, -1)

    ),

    "bottom": (

        (0, -1, 0),

        (0, 0, 1)

    )

}


def get_camera(view):

    return VIEWS[view]