import tkinter as tk

from Brush import Brush
from CustomQueues import Deque
import Interpreter as ip
from Page import Book
import ImageRecognition as ir
import FormulaRepresentation as fr


class App:
    # Method definitions
    def __init__(self):
        # UI
        # Initialize window
        self.window = tk.Tk()
        self.window.attributes('-zoomed', True)
        self.window.title("OGMA")

        # Buttons frame
        buttons_frame = tk.Frame(self.window)
        buttons_frame.pack(side=tk.TOP)
        # Brush button
        brush_button = tk.Button(buttons_frame, text="Brush")
        brush_button.pack(side=tk.LEFT)
        # Plot button
        plot_button = tk.Button(buttons_frame, text="Plot")
        plot_button.pack(side=tk.LEFT)
        # New page button
        new_page_button = tk.Button(buttons_frame, text="New page")
        new_page_button.pack(side=tk.LEFT)

        # Create book of pages
        self.book = Book(self.window)
        self.new_page()
        # Assign new page button callback
        new_page_button.configure(command=self.new_page)

        # Initialize undo
        self.actions = Deque(10)
        self.window.bind("<Control-z>", lambda event: self.undo())

        # Initialize plot button callback
        plot_button.configure(command=lambda: ip.PlotWindow.toggle(self.window))

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

        # Initialize brush settings button
        brush_button.configure(command=lambda: self.brush.open_settings(self.window))

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


if __name__ == "__main__":
    App()
