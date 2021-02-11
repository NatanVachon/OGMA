from ImageRecognition import OCR
import numpy as np
import tkinter as tk


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

    def delete(self):
        # Delete lines
        for line_id in self.line_ids:
            Formula.canvas.delete(line_id)
        # Line not valid anymore
        self.is_valid = False

    def __del__(self):
        print("Line deleted")


class Character(Box):
    # Static members
    ocr = OCR()

    def __init__(self, line):
        # Initialize class instance
        bounds = line.get_bounds()
        super().__init__(bounds[0], bounds[1], bounds[2], bounds[3])
        self.lines = []
        self.prediction = ""

        # Add first line
        self.add_line(line)

    def add_line(self, new_line):
        # Add new line to line list
        self.lines.append(new_line)

        # Recompute bounds
        x_min = min(self.center[0] - 0.5 * self.width, new_line.center[0] - 0.5 * new_line.width)
        x_max = max(self.center[0] + 0.5 * self.width, new_line.center[0] + 0.5 * new_line.width)
        y_min = min(self.center[1] - 0.5 * self.height, new_line.center[1] - 0.5 * new_line.height)
        y_max = max(self.center[1] + 0.5 * self.height, new_line.center[1] + 0.5 * new_line.height)

        self.center = [0.5 * (x_min + x_max), 0.5 * (y_min + y_max)]
        self.width = x_max - x_min
        self.height = y_max - y_min

        # Update prediction
        self.predict()

    def predict(self):
        self.prediction = Character.ocr.predict(self)

    def clean(self):
        for line in self.lines:
            if not line.is_valid:
                self.lines.remove(line)
                del line

    def __del__(self):
        print("Char deleted")


class Formula(Box):
    # Static members
    canvas = None

    def __init__(self, line, mode):
        # Initialize class instance
        bounds = line.get_bounds()
        super().__init__(bounds[0], bounds[1], bounds[2], bounds[3])
        self.chars = []

        # Initialize mode
        self.mode = mode

        # Initialize rectangle
        self.rectangle = Formula.canvas.create_rectangle(0, 0, 0, 0, outline="green")

        # Initialize entry
        self.entry_text = tk.StringVar()
        self.entry = tk.Entry(Formula.canvas, textvariable=self.entry_text, font="Calibri 20")
        self.entry.place(height=30)
        self.entry.bind("<Return>", self.update_prediction)

        # Add first line
        self.add_line(line)

    def add_line(self, new_line):
        if len(self.chars) == 0:
            # Create new character in formula
            last_char = Character(new_line)
            self.chars.append(last_char)
        elif not self.chars[-1].is_intersecting(new_line):
            # Create new character in formula
            last_char = Character(new_line)
            # Check if the two last characters are -- to make it a = #TODO Not clean
            if last_char.prediction == '-' and self.chars[-1].prediction == '-':
                self.chars[-1].add_line(new_line)
                self.chars[-1].prediction = '='
            # Check if the new character is a 0 and the last one was a letter (not possible): used to avoid 0 and O
            # confusion #TODO Not clean
            elif last_char.prediction == '0' and is_letter(self.chars[-1].prediction):
                last_char.prediction = 'O'
                self.chars.append(last_char)
            # Nominal case: just add the new character
            else:
                self.chars.append(last_char)
        else:
            last_char = self.chars[-1]
            # Check if new line intersects last character
            last_char.add_line(new_line)

        # Recompute bounds and add extra space
        x_min = min(self.center[0] - 0.5 * self.width, last_char.center[0] - 0.7 * last_char.width)
        x_max = max(self.center[0] + 0.5 * self.width, last_char.center[0] + 2.0 * last_char.width)
        y_min = min(self.center[1] - 0.5 * self.height, last_char.center[1] - 0.7 * last_char.height)
        y_max = max(self.center[1] + 0.5 * self.height, last_char.center[1] + 0.7 * last_char.height)

        # Update rectangle
        Formula.canvas.coords(self.rectangle, x_min, y_min, x_max, y_max)

        self.center = [0.5 * (x_min + x_max), 0.5 * (y_min + y_max)]
        self.width = x_max - x_min
        self.height = y_max - y_min

        # Update entry
        self.entry.place(x=self.center[0] - 0.5 * self.width, y=self.center[1] + 0.6 * self.height)
        self.entry_text.set(self.get_prediction())

    def get_prediction(self):
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
            Formula.canvas.delete(self.rectangle)
            self.entry.destroy()

    def update_prediction(self, event):
        print("Update prediction")
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
        Formula.canvas.focus_set()

    def __del__(self):
        print("Formula deleted")


# OCR module initialization
def set_canvas(canvas):
    OCR.canvas = canvas
    Formula.canvas = canvas


def is_letter(char):
    return ord('A') <= ord(char) <= ord("Z")