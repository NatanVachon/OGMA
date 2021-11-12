from re import finditer
from Box import Box
from ExpressionTypes import *


class Group(Box):

    def __init__(self, *args):

        # Check if the only argument is a list
        if len(args) == 1 and isinstance(args[0], list):
            args = args[0]

        # Group initialization
        if len(args) > 1:
            self.chars = args      # List of characters in group
            self.pow = None       # Power expression

            # Type and box initialization
            self.type = args[0].get_type()
            group_box = Box(args[0])

            for i in range(1, len(args)):
                assert args[i].get_type() == self.type, "A group can only have one type."
                group_box.merge_box(args[i])

            super().__init__(group_box)

        else:
            self.chars = [args[0]]
            self.pow = None

            # Type initialization
            self.type = args[0].get_type()

            # Box initialization
            super().__init__(args[0])

    def append(self, char):
        # Append new char
        self.chars.append(char)

        # Update box
        super().merge_box(char)

    def __str__(self):
        s = ""
        for char in self.chars:
            s += str(char)

        if self.pow:
            s += "**("

            for char in self.pow.base:
                s += str(char)

            s += ")"

        return s


class Expression(Box):
    def __init__(self, formula_chars, variables):
        """ When an expression is created, a list of characters is given. Then we look for divisions. If a division
        is in the list, we create the widest division possible. Then we check if another division is still in the list
        and so on...
        When no more division is in the list, we convert every characters left in expression grouped by type."""

        # Copy argument
        chars = formula_chars.copy()

        # Class attributes
        self.base = []   # Character and fractions list
        self.pow = None  # Power expression

        # Initialize box
        group_box = Box(chars[0])
        for i in range(1, len(chars)):
            group_box.merge_box(chars[i])

        super().__init__(group_box)

        # Initialization
        preds = [char.prediction for char in chars]

        # Create fractions
        while '/' in preds:
            # Get every divide character sorted by length and get the widest
            divides = [char for char in chars if char.prediction == '/']
            divides.sort(key=lambda x: x.width)
            divide = divides[-1]

            # Create list with every other elements
            char_list = chars.copy()
            char_list.remove(divide)

            # Isolate characters above and below
            above, below = [], []
            for c in char_list:
                if c.right > divide.left and c.left < divide.right:
                    if c.y <= divide.y:
                        above.append(c)
                    else:
                        below.append(c)

            # If no list is empty, create fraction and add it to expression
            if len(above) > 0 and len(below) > 0:
                fraction = Fraction(Expression(above, variables), Expression(below, variables))
                self.base.append(fraction)
            # Else, act as only the non-empty one exists
            else:
                if len(below) == 0:
                    self.base += above
                else:
                    self.base += below

            # Remove elements in the new fraction
            for c in above + below:
                chars.remove(c)
            # Remove divide
            chars.remove(divide)

            # Update preds for the next loop
            preds = [char.prediction for char in chars]

        # Add each character left and sort them by x position
        self.base += chars
        self.base.sort(key=lambda e: e.x)

        # Split powers TODO multi powers
        output = []
        power_group = Group(self.base[0])
        power_list = []

        for i in range(1, len(self.base)):
            char = self.base[i]

            # New char is a power
            if is_power(power_group, char):
                power_list.append(char)

            else:
                # Check if the new char is in the power group or not
                if char.get_type() == power_group.type and power_group.type in [LETTER, DIGIT] and len(power_list) == 0:
                    power_group.append(char)

                else:
                    # Convert power list to expression
                    if len(power_list) > 0:
                        power_group.pow = Expression(power_list, variables)
                        power_list.clear()

                    if power_group.type == LETTER:
                        # Split letter group
                        output += split_letter_group(power_group, variables)
                    else:
                        # Add power group(s) to output list
                        output.append(power_group)

                    # Create new power group
                    power_group = Group(char)

        # Add the last power group
        if len(power_list) > 0:
            power_group.pow = Expression(power_list, variables)

        if power_group.type == LETTER:
            output += split_letter_group(power_group, variables)
        else:
            output.append(power_group)

        # Save output list
        self.base = output

    def __str__(self):
        out = str(self.base[0])
        p_group = self.base[0]

        for i in range(1, len(self.base)):
            group = self.base[i]
            if {p_group.type, group.type} in [{DIGIT, LETTER}, {DIGIT, FRACTION}, {LETTER, FRACTION}, {LETTER, LETTER}]:
                out += "*"

            out += str(group)

            p_group = group

        return out


class Fraction(Box):
    def __init__(self, num, den):
        self.num = num  # Num expression
        self.den = den  # Den expression

        # Compute bounds
        x1, y1, x2, y2 = num.get_bounds()
        super().__init__(x1, y1, x2, y2)
        self.merge_box(den)

    def split_power(self):
        self.num.split_power()
        self.den.split_power()

    def split_multiply(self, declared_variables):
        self.num.split_multiply()
        self.den.split_multiply()

    def get_type(self):
        return FRACTION

    def __str__(self):
        return "(" + str(self.num) + ")/(" + str(self.den) + ")"


def split_letter_group(group, variables):
    """ Returns a list of split groups """
    print("Vars: {} Group: {}".format(variables, str(group)))
    # Make special case for singletons
    if len(group.chars) == 1:
        return [group]

    # Construct group string TODO Powers cut groups
    string = ""
    for char in group.chars:
        string += str(char)

    # Split group
    groups = []
    bounds = []
    for var in variables:
        var_bounds = finditer(var, string)
        for var_bound in var_bounds:
            if all([bound[0] >= var_bound.end() or bound[1] <= var_bound.start() for bound in bounds]):
                bounds.append([var_bound.start(), var_bound.end()])

                new_group = Group(group.chars[var_bound.start():var_bound.end()])
                if var_bound.end() == len(group.chars):
                    new_group.pow = group.pow
                groups.append(new_group)

    # Construct left groups
    begin = 0
    grouping = all([0 < bound[0] or 0 >= bound[1] for bound in bounds])

    for i in range(1, len(group.chars)):
        if grouping:
            if not all([i < bound[0] or i >= bound[1] for bound in bounds]):
                # Found a left group end
                print("Left group found: {}".format(string[begin:i]))
                new_group = Group(group.chars[begin:i])

                if i == len(group.chars):
                    new_group.pow = group.pow

                groups.append(new_group)

                # Not grouping anymore
                grouping = False
        else:
            if all([i < bound[0] or i >= bound[1] for bound in bounds]):
                # Found a left group start
                begin = i
                grouping = True

    # Check if we need to add the last group
    if grouping:
        print("Left group found: {}".format(string[begin:]))
        new_group = Group(group.chars[begin:])
        new_group.pow = group.pow
        groups.append(new_group)

    # Sort list by position
    groups.sort(key=lambda e: e.x)

    return groups


def classify_horizontal_lines(formula):
    """ This function checks if a '-' character is a minus or a divide """

    for i in range(len(formula.chars)):
        char = formula.chars[i]
        if char.prediction == '-':
            # Search the closest character over the horizontal line
            min_distance, closest = float('inf'), None
            for o_char in formula.chars:
                if o_char == char:
                    continue
                if o_char.y < char.y and o_char.right >= char.left and o_char.left <= char.right:

                    # Compute distance to the next '-' to search the closest
                    if char.top - o_char.bottom < min_distance:
                        min_distance = char.top - o_char.bottom
                        closest = o_char

            # If the closest character over is a digit or a letter, this character is a division
            if closest and closest.get_type() in [DIGIT, LETTER]:
                formula.chars[i].prediction = '/'

    return formula


def get_python_rpz(formula, variables):
    """ Translates a Formula object into a python executable string """
    formula = classify_horizontal_lines(formula)
    exp = Expression(formula.chars, variables)
    python_string = parenthesis_fix(str(exp))
    print(python_string)
    return python_string


def parenthesis_fix(raw_string):
    """ We are looking for patterns like *1*...*1 with minimal number of characters in "..." to replace by (...) """
    parenthesis = finditer(r"(\*1\*.{1," + str(len(raw_string)) + r"}?\*1)", raw_string)
    python_list = list(raw_string)

    for par in parenthesis:
        python_list[par.start()] = ''
        python_list[par.start() + 1] = ''
        python_list[par.start() + 2] = '('
        python_list[par.end() - 2] = ''
        python_list[par.end() - 1] = ')'

    python_list = [c for c in python_list if c != '']

    python_string = ""
    for char in python_list:
        python_string += char

    return python_string


def is_power(power_box, next_char):
    """ Checks if next_char is a power of char """
    return power_box.top >= next_char.bottom
