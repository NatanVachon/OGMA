import tkinter as tk

import Draws as dr
from Brush import Brush
from CustomQueues import Deque
from Interpreter import Interpreter


class App:
    # Method definitions
    def __init__(self):
        # Initialize window
        self.window = tk.Tk()
        # self.window.attributes('-zoomed', True)
        self.window.title("OGMA")

        # BUTTONS FRAME
        buttons_frame = tk.Frame(self.window)
        buttons_frame.pack(side=tk.TOP)
        # Brush button
        brush_button = tk.Button(buttons_frame, text="Brush")
        brush_button.pack(side=tk.LEFT)
        # Plot button
        plot_button = tk.Button(buttons_frame, text="Plot")
        plot_button.pack(side=tk.LEFT)

        # Create draw canvas
        self.canvas = tk.Canvas(self.window, bg="black")  # #20204E
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Initialize formulas list
        self.formulas = []

        # Initialize undo
        self.actions = Deque(10)
        self.window.bind_all("<Control-z>", lambda event: self.undo())

        # Initialize interpreter instance
        self.interpreter = Interpreter()
        # Initialize plot button callback
        plot_button.configure(command=self.interpreter.plot)
        # Initialize interpreter binds
        self.window.bind('e', lambda event: self.evaluate())
        self.window.bind('p', lambda event: self.interpreter.plot())

        # Initialize mode
        self.mode = "Free"
        # Initialize right click menu for mode selection
        self.right_click_menu = tk.Menu(self.canvas, tearoff=False)
        self.right_click_menu.add_command(label="Free", command=lambda: self.set_mode("Free"))
        self.right_click_menu.add_command(label="Eval", command=lambda: self.set_mode("Eval"))
        self.right_click_menu.add_command(label="Function", command=lambda: self.set_mode("Function"))
        # Initialize mode binds
        self.canvas.bind("<Button-3>", lambda event: self.right_click_menu.tk_popup(self.canvas.winfo_rootx() + event.x,
                                                                                    self.canvas.winfo_rooty() + event.y)
                         )

        # Initialize brush
        self.brush = Brush(self.canvas)
        # Initialize brush events
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.stay_draw)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw)
        # Initialize brush keyboard shortcuts
        self.window.bind('b', lambda event: self.brush.open_settings())
        # Initialize brush settings button
        brush_button.configure(command=self.brush.open_settings)

        # Initialize OCR module
        dr.set_canvas(self.canvas)

        # Debug
        self.debug_counter = 0

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

        # If we are in free mode don't create or use formulas
        if self.mode == "Free":
            return

        # Manage formulas
        if len(self.formulas) > 0 and self.formulas[-1].is_intersecting(new_line):
            last_formula = self.formulas[-1]

            # Check if our line intersects with the current formula
            last_formula.add_line(new_line)
        else:
            last_formula = dr.Formula(new_line, self.mode)
            self.formulas.append(last_formula)

    def evaluate(self):
        prediction = self.formulas[-1].get_prediction()

        output = self.interpreter.evaluate(prediction, self.mode)

        # Add result to entry text
        if output:
            prediction += output

    def update_display(self):
        for formula in self.formulas:
            formula.clean()

            # Check if formula is empty
            if len(formula.chars) == 0:

                self.formulas.remove(formula)
                del formula

    def set_mode(self, mode):
        self.mode = mode

    def undo(self):
        last_action = self.actions.get()
        if last_action:
            last_action.delete()
            del last_action

            # Update display
            self.update_display()


if __name__ == "__main__":
    App()
