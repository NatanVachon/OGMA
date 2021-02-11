import tkinter as tk


class DrawPage(tk.Frame):
    def __init__(self, **kw):
        # Call frame constructor
        super().__init__(**kw)

        # Set a grey background
        self.configure(background="grey")

        # Create the canvas
        self.canvas = tk.Canvas()
