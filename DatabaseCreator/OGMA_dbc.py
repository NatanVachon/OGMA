import tkinter as tk
import json
import os

from Brush import Brush
from CustomQueues import Deque
import Interpreter as ip
from Page import Book
import ImageRecognition as ir
import FormulaRepresentation as fr
import Teacher as tf


class App:
    # Method definitions
    def __init__(self):
        # UI
        # Initialize window
        self.window = tk.Tk()
        self.window.attributes('-zoomed', True)
        self.window.title("OGMA")

        # Create target formula
        self.teacher = tf.Teacher(self.window)
        self.window.bind('o', lambda event: self.save_round())

        # Create book of pages
        self.book = Book(self.window)
        self.new_page()

        # Initialize undo
        self.actions = Deque(30)
        self.window.bind("<Control-z>", lambda event: self.undo())

        # Initialize interpreter binds
        self.window.bind('e', lambda event: self.evaluate())
        self.window.bind('p', lambda event: ip.PlotWindow.toggle(self.window))
        self.window.bind('v', lambda event: ip.toggle_variable_window(self.window))

        # Initialize right click menu for mode selection
        self.right_click_menu = tk.Menu(self.window, tearoff=False)
        self.right_click_menu.add_command(label="Free", command=lambda: self.set_mode("Free"))
        self.right_click_menu.add_command(label="Eval", command=lambda: self.set_mode("Eval"))
        self.right_click_menu.add_command(label="Declare", command=lambda: self.set_mode("Declare"))
        self.right_click_menu.add_command(label="Solve", command=lambda: self.set_mode("Solve"))

        # BRUSH
        # Initialize brush
        self.brush = Brush(Book.canvas)

        # Initialize brush keyboard shortcuts
        self.window.bind('b', lambda event: self.brush.open_settings(self.window))

        # Initialize OCR module
        ir.init()

        # Start application
        self.window.mainloop()

    def start_draw(self, event):
        # Start line
        self.brush.start_line([event.x, event.y])

    def stay_draw(self, event):
        # Draw line
        self.brush.continue_line([event.x, event.y])

    def end_draw(self, event):
        # Finish line
        new_line = self.brush.end_line()

        # Check line sanity
        if not new_line:
            return

        # Save line to undo later
        self.actions.put(new_line)

        # Add line to blackboard
        self.book.add_line(new_line)

    def evaluate(self):
        last_formula = self.book.get_last_formula()
        python_string = fr.get_python_rpz(last_formula, ip.get_variable_names())

        ip.evaluate(python_string, last_formula.mode)

    def set_mode(self, mode):
        self.book.set_mode(mode)

    def undo(self):
        last_action = self.actions.get()
        if last_action:
            last_action.delete()

    def new_page(self):
        self.book.new_page()
        # Bind callbacks to the new canvas
        # Draw binds
        Book.canvas.bind("<Button-1>", self.start_draw)
        Book.canvas.bind("<B1-Motion>", self.stay_draw)
        Book.canvas.bind("<ButtonRelease-1>", self.end_draw)
        # Mode binds
        Book.canvas.bind("<Button-3>", lambda event: self.right_click_menu.tk_popup(Book.canvas.winfo_rootx() + event.x,
                                                                                    Book.canvas.winfo_rooty() + event.y)
                         )

    def save_round(self):
        # Get drawn formula
        saved_formula = self.book.focused_page.blackboard.formulas[-1]

        # Convert it to JSON
        formula_json = {"brush": self.brush.to_json(), "displayed_formula": self.teacher.displayed_formula,
                        "drawn_formula": saved_formula.to_json()}

        # Save it
        file_index = len([name for name in os.listdir("database")])
        with open("database/Round{}.json".format(file_index), "w") as f:
            json.dump(formula_json, f, indent=4, sort_keys=True)

        # Move to next round
        if self.teacher.display_index == len(self.teacher.formulas) - 1:
            self.window.destroy()
        else:
            self.teacher.next_formula()

        # Erase every stroke
        last_action = self.actions.get()

        while last_action is not None:
            last_action.delete()
            last_action = self.actions.get()


if __name__ == "__main__":
    App()
