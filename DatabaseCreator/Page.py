import tkinter as tk
from tkinter import ttk
import Draws as dr


class Book:
    # Static canvas variable
    canvas = None

    def __init__(self, root):
        # Create notebook
        self.notebook = ttk.Notebook(root)
        #self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create page list
        self.pages = []
        self.focused_page = None

        # Bind events
        def update_canvas():
            page_index = self.notebook.index(self.notebook.select())
            # Update static canvas
            Book.canvas = self.pages[page_index].canvas
            # Update focused page
            self.focused_page = self.pages[page_index]

        self.notebook.bind("<<NotebookTabChanged>>", lambda event: update_canvas())

    def new_page(self):
        # Create new page
        new_page = DrawPage(self.notebook)
        self.pages.append(new_page)
        self.notebook.add(new_page.frame, text="Page " + str(len(self.pages)))

        # Select it
        self.notebook.select(len(self.pages) - 1)

        # Update static canvas
        Book.canvas = new_page.canvas

        # Update focused page
        self.focused_page = self.pages[-1]

    def add_line(self, new_line):
        if self.focused_page.blackboard.mode != "Free":
            self.focused_page.blackboard.add_line(new_line)

    def get_last_formula(self):
        return self.focused_page.blackboard.get_last_formula()

    def set_mode(self, mode):
        self.focused_page.blackboard.mode = mode


class DrawPage:
    def __init__(self, root):
        # Draw frame
        self.frame = ttk.Frame(root)
        self.frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create global canvas and sub frame
        global_canvas = tk.Canvas(self.frame, background="gray")

        # Create scroll bars
        vertical_scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=global_canvas.yview)
        vertical_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        horizontal_scrollbar = ttk.Scrollbar(self.frame, orient="horizontal", command=global_canvas.xview)
        horizontal_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Pack canvas
        global_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure canvas
        global_canvas.configure(yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)
        global_canvas.bind("<Configure>", lambda event: global_canvas.configure(scrollregion=global_canvas.bbox("all")))

        # Create sub frame
        sub_frame = tk.Frame(global_canvas)

        # Create window in sub frame
        global_canvas.create_window((0, 0), window=sub_frame, anchor="nw", width=1920, height=1920)

        # Create draw canvases
        background_canvas = tk.Canvas(sub_frame, bg="gray", width=1920, height=1920)
        background_canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(background_canvas, bg="black", width=1440, height=1527)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Create page blackboard
        self.blackboard = dr.BlackBoard()
