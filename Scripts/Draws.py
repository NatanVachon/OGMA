import tkinter as tk

from Box import Box
import ImageRecognition as ir
from Page import Book
import FormulaRepresentation as fr
import Interpreter as ip
from ExpressionTypes import *


class Line(Box):
    def __init__(self, line_ids, x1, y1, x2, y2):
        # Super class init
        super().__init__(x1, y1, x2, y2)

        # Check line sanity
        self.is_valid = (self.width != 0) and (self.height != 0)

        # Compute aspect ratio
        if self.is_valid:
            self.aspect_ratio = self.height / self.width
        else:
            self.aspect_ratio = None

        # Save line IDs
        self.line_ids = line_ids

        # Initialize delete callback
        self.delete_callback = lambda: None

    def delete(self):
        # Delete lines
        for line_id in self.line_ids:
            Book.canvas.delete(line_id)

        # Line not valid anymore
        self.is_valid = False

        # Call delete callback
        self.delete_callback()


class Character(Box):
    def __init__(self, line):
        # Initialize class instance
        super().__init__(line)
        self.lines = [line]
        self.prediction = ir.predict(self)

    def add_line(self, new_line):
        # Add new line to line list
        self.lines.append(new_line)

        # Recompute bounds
        self.merge_box(new_line)

        # Update prediction
        self.predict()

    def predict(self):
        self.prediction = ir.predict(self)

    def absorb(self, char):
        for line in char.lines:
            self.lines.append(line)
            char.lines.remove(line)

    def clean(self):
        for line in self.lines:
            if not line.is_valid:
                self.lines.remove(line)
                del line

    def get_type(self):
        if is_digit(self.prediction):
            return DIGIT
        elif is_letter(self.prediction):
            return LETTER
        elif is_math_symbol(self.prediction):
            return MATH
        elif is_parenthesis(self.prediction):
            return PARENTHESIS
        else:
            raise AttributeError("Character " + self.prediction + " doesnt exists")

    def __str__(self):
        return self.prediction


class Formula(Box):
    def __init__(self, line, mode):
        # Initialize class instance
        super().__init__(line)

        # Initialize characters list
        self.chars = []

        # Initialize mode
        self.mode = mode

        # Initialize rectangle
        self.rectangle = Book.canvas.create_rectangle(0, 0, 0, 0, outline="green")

        # Initialize entry
        self.entry_text = tk.StringVar()
        self.entry = tk.Entry(Book.canvas, textvariable=self.entry_text, font="Calibri 20")
        self.entry.place(height=30)
        self.entry.bind("<Return>", lambda event: self.update_prediction())

        # Add first line
        self.add_line(line)

    def add_line(self, new_line):  # TODO Not clean
        if len(self.chars) == 0 or not self.chars[-1].is_intersecting(new_line):
            # Create new character in formula
            last_char = Character(new_line)
            self.chars.append(last_char)
        else:
            # Add new line to last character
            last_char = self.chars[-1]
            last_char.add_line(new_line)

        # Run confusion avoidance check
        self.avoid_confusion()

        # Recompute bounds and add extra space
        x_min = min(self.center[0] - 0.5 * self.width, last_char.center[0] - 0.75 * last_char.width)
        x_max = max(self.center[0] + 0.5 * self.width, last_char.center[0] + 2.0 * last_char.width)
        y_min = min(self.center[1] - 0.5 * self.height, last_char.center[1] - 1.5 * last_char.height)
        y_max = max(self.center[1] + 0.5 * self.height, last_char.center[1] + 1.5 * last_char.height)

        # Update box parameters
        self.center = [0.5 * (x_min + x_max), 0.5 * (y_min + y_max)]
        self.width = x_max - x_min
        self.height = y_max - y_min

        # Update rectangles
        Book.canvas.coords(self.rectangle, x_min, y_min, x_max, y_max)

        # Update entry
        #self.entry.place(x=self.center[0] - 0.5 * self.width, y=self.center[1] + 0.6 * self.height)
        #self.entry_text.set(fr.get_python_rpz(self, ip.get_variable_names()))  TODO REMOOOOOOOVE

        _ = fr.get_python_rpz(self)

    def avoid_confusion(self):
        # If length is lower than two, no confusion is avoidable
        if len(self.chars) < 2:
            return

        # Get two last characters
        char, p_char = self.chars[-1], self.chars[-2]

        # Check if the last two characters are -- and are more or less on the same vertical axis,
        # make it a =
        if char.prediction == '-' and p_char.prediction == '-':
            if abs(char.width - p_char.width) / min(char.width, p_char.width) < 0.4:
                p_char.absorb(char)
                p_char.prediction = '='
                self.chars.remove(char)

        # Check if the last two characters are a letter and 0 (not possible) to avoid 0 and O confusion
        elif char.prediction == '0' and is_letter(p_char.prediction):
            char.prediction = 'O'

        # Check if the last two characters are a letter and 5 (not possible) to avoid 5 and S confusion
        elif char.prediction == '5' and is_letter(p_char.prediction):
            char.prediction = 'S'

    def __str__(self):
        prediction = ""
        for char in self.chars:
            prediction += char.prediction
        return prediction

    def clean(self):
        # Delete empty characters
        for char in self.chars:
            char.clean()
            if len(char.lines) == 0:
                self.chars.remove(char)
                del char

        # If formula is empty, delete rectangle
        if len(self.chars) == 0:
            Book.canvas.delete(self.rectangle)
            self.entry.destroy()

    def update_prediction(self):
        # Check that the character number is correct
        new_prediction = self.entry_text.get()
        if len(new_prediction) == len(self.chars):
            # Length is correct
            for i in range(len(self.chars)):
                self.chars[i].prediction = new_prediction[i]
        else:
            # Length isn't correct
            self.entry_text.set(self.get_prediction())

        # Stop focusing entry
        Book.canvas.focus_set()


class BlackBoard:
    def __init__(self):
        self.formulas = []
        self.mode = "Free"  # Blackboard mode corresponds to the mode given to the next created formulas

    def add_line(self, new_line):
        # TODO currently: only the last formula

        # If the new line intersects an existing formula, add the new line to this formula
        if len(self.formulas) > 0 and self.formulas[-1].is_intersecting(new_line):
            last_formula = self.formulas[-1]
            last_formula.add_line(new_line)
        else:
            last_formula = Formula(new_line, self.mode)
            self.formulas.append(last_formula)

        # Assign line delete callback to formula.clean
        new_line.delete_callback = lambda: self.clean_formula(last_formula)

    def clean_formula(self, formula):
        formula.clean()
        if len(formula.chars) == 0:
            self.formulas.remove(formula)

    def get_last_formula(self):
        # TODO currently: only the last formula

        if len(self.formulas) > 0:
            return self.formulas[-1]
        else:
            return None