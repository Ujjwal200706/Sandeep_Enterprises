"""
Model Analyzer

Returns

- Dimensions
- Center
- Bounding Box
- Volume
- Surface Area
"""

import numpy as np


class ModelAnalyzer:

    def __init__(self, mesh):

        self.mesh = mesh

    def dimensions(self):

        bounds = self.mesh.bounds

        x = bounds[1] - bounds[0]
        y = bounds[3] - bounds[2]
        z = bounds[5] - bounds[4]

        return {

            "length": round(float(x), 2),

            "width": round(float(y), 2),

            "height": round(float(z), 2)

        }

    def center(self):

        c = self.mesh.center

        return {

            "x": round(float(c[0]), 2),

            "y": round(float(c[1]), 2),

            "z": round(float(c[2]), 2)

        }

    def volume(self):

        try:

            return round(float(self.mesh.volume), 2)

        except:

            return None

    def area(self):

        try:

            return round(float(self.mesh.area), 2)

        except:

            return None

    def analyze(self):

        return {

            "dimensions": self.dimensions(),

            "center": self.center(),

            "volume": self.volume(),

            "surface_area": self.area()

        }