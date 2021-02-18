import tkinter as tk
import numpy as np
import numpy.linalg as lin

from Draws import Line
from Page import Book


class Brush:
    def __init__(self, canvas):
        # Canvas
        self.canvas = canvas

        # Graphics variables
        self.width = 10
        self.step = 0.3
        self.color = "white"  # "#FFDFC8"
        self.capstyle = tk.ROUND

        # Line variables
        self.line_list = [0] * 256  # TODO manage list overflow
        self.line_count = 0
        self.line_x_min, self.line_x_max = 0, 0
        self.line_y_min, self.line_y_max = 0, 0

        # State variables
        self.is_drawing = False
        self.last_point = np.zeros(2)

    def start_line(self, point):
        # Update focused canvas
        self.canvas = Book.canvas

        # Set first line point
        self.last_point[0] = point[0]
        self.last_point[1] = point[1]

        # Initialize boundary rectangle
        self.line_x_min = self.line_x_max = point[0]
        self.line_y_min = self.line_y_max = point[1]

        # Start drawing
        self.is_drawing = True

    def continue_line(self, point):
        point = np.array(point)

        # Check if we have to draw
        if not self.is_drawing or lin.norm(point - self.last_point) < self.width * self.step:
            return

        # Create line and store line ID in list
        self.line_list[self.line_count] = self.canvas.create_line(self.last_point[0],
                                                                  self.last_point[1],
                                                                  point[0], point[1],
                                                                  width=self.width,
                                                                  fill=self.color,
                                                                  capstyle=self.capstyle,
                                                                  smooth=True)
        self.line_count += 1

        # Check for min and max
        if point[0] - self.width / 2 < self.line_x_min:
            self.line_x_min = point[0] - self.width / 2
        if point[0] + self.width / 2 > self.line_x_max:
            self.line_x_max = point[0] + self.width / 2
        if point[1] - self.width / 2 < self.line_y_min:
            self.line_y_min = point[1] - self.width / 2
        if point[1] + self.width / 2 > self.line_y_max:
            self.line_y_max = point[1] + self.width / 2

        # Save last position
        self.last_point[0] = point[0]
        self.last_point[1] = point[1]

    def end_line(self):
        # Stop drawing
        self.is_drawing = False

        # Create line
        new_line = Line(self.line_list[:self.line_count],
                        self.line_x_min, self.line_y_min, self.line_x_max, self.line_y_max)

        # Reset line count
        self.line_count = 0

        # Check line sanity
        if new_line.is_valid:
            return new_line
        else:
            return None

    def open_settings(self, root):
        top = tk.Toplevel()
        top.transient(root)  # Brush window is always on top of main window
        top.title("Brush settings")

        # SETTINGS FRAME
        settings_frame = tk.Frame(top)
        settings_frame.pack(side=tk.TOP)

        # Width cursor
        width_frame = tk.Frame(settings_frame)
        width_frame.pack(side=tk.LEFT)
        tk.Label(width_frame, text="Width").pack(side=tk.TOP)
        scale_width = tk.Scale(width_frame, from_=5, to=20, orient=tk.HORIZONTAL)
        scale_width.set(self.width)
        scale_width.pack(side=tk.TOP)

        # Step cursor
        step_frame = tk.Frame(settings_frame)
        step_frame.pack(side=tk.LEFT)
        tk.Label(step_frame, text="Step").pack(side=tk.TOP)
        scale_step = tk.Scale(step_frame, from_=0.1, to=0.5, resolution=0.05, orient=tk.HORIZONTAL)
        scale_step.set(self.step)
        scale_step.pack(side=tk.TOP)

        # BUTTONS FRAME
        buttons_frame = tk.Frame(top)
        buttons_frame.pack(side=tk.BOTTOM)

        # Cancel button
        tk.Button(buttons_frame, text="Cancel", command=top.destroy).pack(side=tk.RIGHT)

        def ok_button():
            self.width = scale_width.get()
            self.step = scale_step.get()
            top.destroy()

        # Ok button
        tk.Button(buttons_frame, text="Ok", command=ok_button).pack(side=tk.RIGHT)
