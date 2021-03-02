import numpy as np


class Box:
    def __init__(self, x1, y1, x2, y2):
        self.center = np.array([0.5 * (x1 + x2), 0.5 * (y1 + y2)])
        self.width = x2 - x1
        self.height = y2 - y1

    def is_intersecting(self, new_box):
        return (abs(self.center[0] - new_box.center[0]) * 2.0 < (self.width + new_box.width)) and (
                abs(self.center[1] - new_box.center[1]) * 2.0 < (self.height + new_box.height))

    def get_bounds(self):
        return self.center[0] - 0.5 * self.width, self.center[1] - 0.5 * self.height, \
               self.center[0] + 0.5 * self.width, self.center[1] + 0.5 * self.height

    @property
    def left(self):
        return self.center[0] - 0.5 * self.width

    @property
    def right(self):
        return self.center[0] + 0.5 * self.width

    @property
    def top(self):
        return self.center[1] - 0.5 * self.height

    @property
    def bottom(self):
        return self.center[1] + 0.5 * self.height

    @property
    def x(self):
        return self.center[0]

    @property
    def y(self):
        return self.center[1]