import matplotlib
import tkinter as tk
import json

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class Teacher:
    def __init__(self, root):
        # Create plot variables
        self.f = Figure()
        self.ax = self.f.add_subplot(111)

        # Create frame and canvas
        self.frame = tk.Frame(root)
        self.frame.pack(side=tk.TOP)

        self.canvas = FigureCanvasTkAgg(self.f, self.frame)
        self.canvas.get_tk_widget().config(width=1920, height=440)
        self.canvas.get_tk_widget().pack()

        # Formulas initialization
        self.displayed_formula = ""
        with open("formulas.json", "r") as f:
            json_string = json.load(f)
            self.formulas = json_string["list"]

        self.display_index = 0
        self.display_formula(0)

    def display_formula(self, index):
        self.displayed_formula = self.formulas[index]

        self.ax.clear()
        self.ax.set_axis_off()
        self.ax.text(0.1, 0.5, '$' + self.displayed_formula + '$', fontsize=32)

        self.f.canvas.draw()
        self.f.canvas.flush_events()

    def next_formula(self):
        self.display_index += 1
        self.display_formula(self.display_index)
