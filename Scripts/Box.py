import numpy as np


class Box:
    def __init__(self, *args):

        if len(args) > 1:
            x1, y1, x2, y2 = args[0], args[1], args[2], args[3]
            self.center = np.array([0.5 * (x1 + x2), 0.5 * (y1 + y2)])
            self.width = x2 - x1
            self.height = y2 - y1

        else:
            self.center = args[0].center.copy()
            self.width = args[0].width
            self.height = args[0].height

    def is_intersecting(self, new_box):
        return (abs(self.center[0] - new_box.center[0]) * 2.0 < (self.width + new_box.width)) and (
                abs(self.center[1] - new_box.center[1]) * 2.0 < (self.height + new_box.height))

    def get_bounds(self):
        return self.center[0] - 0.5 * self.width, self.center[1] - 0.5 * self.height, \
               self.center[0] + 0.5 * self.width, self.center[1] + 0.5 * self.height

    def merge_box(self, new_box):
        # Recompute bounds
        x_min_self, y_min_self, x_max_self, y_max_self = self.get_bounds()
        x_min_new, y_min_new, x_max_new, y_max_new = new_box.get_bounds()

        x_min, x_max = min(x_min_self, x_min_new), max(x_max_self, x_max_new)
        y_min, y_max = min(y_min_self, y_min_new), max(y_max_self, y_max_new)

        self.center[0] = 0.5 * (x_min + x_max)
        self.center[1] = 0.5 * (y_min + y_max)
        self.width = x_max - x_min
        self.height = y_max - y_min

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
