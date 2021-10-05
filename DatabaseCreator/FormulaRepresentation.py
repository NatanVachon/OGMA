from re import finditer
from Box import Box


# Expression types
DIGIT = 0
LETTER = 1
MATH = 2
PARENTHESIS = 3

# Stringable means a string conversion is possible


class Expression:
    def __init__(self, char):
        self.type = get_type(char)
        self.base = []  # Strigable elements list
        self.power = []  # Power strigable elements list

        self.add_char(char)

    def add_char(self, char):
        self.base += char
        pass

    def __str__(self):
        out = ""
        for s in self.base:
            out += str(s)
        out += "**("
        for s in self.power:
            out += str(s)
        out += ")"
        return out


class Fraction(Box):
    def __init__(self, num, den):
        self.num = num  # Num expression
        self.den = den  # Den expression

        # Compute bounds
        x1, y1, x2, y2 = num[0].get_bounds()
        for box in num + den:
            box_x1, box_y1, box_x2, box_y2 = box.get_bounds()
            x1 = min(x1, box_x1)
            y1 = min(y1, box_y1)
            x2 = max(x2, box_x2)
            y2 = max(y2, box_y2)
        super().__init__(x1, y1, x2, y2)

    def __str__(self):
        # Split powers
        self.num = split_power(self.num)
        self.den = split_power(self.den)

        out = "("
        for s in self.num:
            out += str(s)
        out += ")/("
        for s in self.den:
            out += str(s)
        out += ")"
        return out


def split_letter_expression(string, declared_variables):
    """ Split letter expressions by adding multiplications, for instance: abcos becomes a*b*cos.
        We use the list of previously declared variables to find them and surround them with multiplications."""
    # Mark expression bounds
    bounds = []  # Contains blocked indexes

    # Iterate through each declared variable
    for var in declared_variables:
        # Look for each occurrence of this variable. Start bound is inclusive and end bound is exclusive
        var_bounds = finditer(var, string)
        for var_bound in var_bounds:
            # Check if the found occurrence bounds aren't in previously found expression bounds
            if all([bound[0] >= var_bound.end() or bound[1] <= var_bound.start() for bound in bounds]):
                bounds.append([var_bound.start(), var_bound.end()])

    # Now lets create a list of bounds without duplicates
    bounds = list(set([bound[0] for bound in bounds]) | set([bound[1] for bound in bounds]))
    # Construct final string by adding * in both side of bounds
    final_string = string[0]

    for i in range(1, len(string)):
        if i in bounds:
            final_string += '*' + string[i]
        else:
            final_string += string[i]

    return final_string


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
                if o_char.center[1] < char.center[1] and o_char.center[0] - 0.5 * o_char.width >= char.center[0] - 0.5 * char.width and \
                        o_char.center[0] + 0.5 * o_char.width <= char.center[0] + 0.5 * char.width:

                    # Compute distance to the next '-' to search the closest
                    if char.center[1] - o_char.center[1] < min_distance:
                        min_distance = char.center[1] - o_char.center[1]
                        closest = o_char

            # If the closest character over is a digit or a letter, this character is a division
            if closest and get_type(closest.prediction) in [DIGIT, LETTER]:
                formula.chars[i].prediction = '/'

    return formula


def get_python_rpz(formula, declared_variables):
    # For each horizontal line, check if it is a division or not
    formula = classify_horizontal_lines(formula)

    # Remove every power from expressions
    s_list = clean_power(formula.chars)

    # Create divisions
    s_list = split_divide(s_list)

    # Add powers to expressions
    s_list = split_power(s_list)

    python_string = ""
    for s in s_list:
        python_string += str(s)

    # Add implicit multiplications fo the final string
    python_string = split_multiply(python_string, declared_variables)

    # TODO REMOVE LATER
    # We are looking for patterns like *1*...*1 with minimal number of characters in "..." to replace by (...)
    parenthesis = finditer(r"(\*1\*.{1," + str(len(python_string)) + r"}?\*1)", python_string)
    python_list = list(python_string)

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


def split_multiply(string, declared_variables):
    output = ""
    prev_char, prev_type = string[0], get_type(string[0])

    # Letter expression split variables, used to split letter expressions
    begin = 0
    is_letter_exp = False

    # Handle first char
    if prev_type == LETTER:
        is_letter_exp = True
    else:
        output += prev_char

    for i in range(1, len(string)):
        char, current_type = string[i], get_type(string[i])

        if is_letter_exp and current_type != LETTER:
            output += split_letter_expression(string[begin:i], declared_variables)
            is_letter_exp = False

        # Add multiply separation
        if (prev_char == ')' and char == '(') or {prev_type, current_type} == {DIGIT, LETTER}:
            output += '*'

        # Look for letter successions
        if not is_letter_exp:
            if current_type == LETTER:
                begin = i
                is_letter_exp = True
            else:
                output += char

        prev_char, prev_type = char, current_type

    # Split last letter expression if necessary
    if is_letter_exp:
        output += split_letter_expression(string[begin:], declared_variables)

    return output


def clean_power(s_list):
    for s in s_list:
        if type(s) is Fraction:
            s.num = clean_power(s.num)
            s.den = clean_power(s.den)
        else:
            s.pow.clear()

    return s_list


def split_power(s_list):
    if len(s_list) == 0:
        return []

    # Sort stringables from left to right
    s_list.sort(key=lambda u: u.x)

    power_box = s_list[0]

    output_list = []

    # TODO Currently supports one degree of power
    for i in range(1, len(s_list)):
        s = s_list[i]
        # TODO Dont try to put powers on math symbols

        if type(s) is Fraction:
            s.num = split_power(s.num)
            s.den = split_power(s.den)

            # Check if the fraction is in the power
            if is_power(power_box, s):
                power_box.pow.append(s)
            else:
                output_list.append(power_box)
                power_box = s
        else:
            # If power box is a fraction, just add it to the list and continue
            if type(power_box) is Fraction:
                output_list.append(power_box)
                power_box = s
                continue

            # s is a char
            if not is_math_symbol(power_box.prediction) and is_power(power_box, s):
                power_box.pow.append(s)
            else:
                output_list.append(power_box)
                power_box = s

    output_list.append(power_box)
    return output_list


def split_divide(s_list):
    # Get every divide character sorted by length
    divides = [char for char in s_list if char.prediction == '/']
    divides.sort(key=lambda c: c.width)

    # Create base stringable list
    s_list = [char for char in s_list if char.prediction != '/']

    # Create fractions
    for divide in divides:
        # Elements in the numerator are elements between this divide and the next above
        # Elements in the denominator are elements between this divide and the next below
        top_lim, bot_lim = 0, float('inf')
        # Check for each divide if one is above and below the current one
        for o_divide in divides:
            if o_divide == divide:
                continue
            if o_divide.left <= divide.left and o_divide.right >= divide.right:
                # On the same x box
                if o_divide.y < divide.y and divide.y - o_divide.y < top_lim:
                    # Other divide is above and closer
                    top_lim = divide.y - o_divide.y
                elif o_divide.y > divide.y and o_divide.y - divide.y < bot_lim:
                    # Other divide is below and closer
                    bot_lim = o_divide.y - divide.y

        # Isolate stringables above and below
        above, below = [], []
        for stringable in s_list:
            if stringable.left >= divide.left and stringable.right <= divide.right:
                if stringable.y < divide.y:
                    above.append(stringable)
                else:
                    below.append(stringable)

        # Create fraction
        fraction = Fraction(above, below)

        # Replace stringables by the new fraction
        s_list.insert(s_list.index(above[0]), fraction)
        for s in above + below:
            s_list.remove(s)

    # Return stringable list
    return s_list


# Character type checks
def is_digit(char):
    return ord('0') <= ord(char) <= ord('9')


def is_letter(char):
    return ord('A') <= ord(char) <= ord('Z')


def is_math_symbol(char):
    return char in ['-', '+', '/', '*', '=']


def is_parenthesis(char):
    return char in ['(', ')']


def get_type(char):
    """ Returns the type of char. Can be DIGIT, LETTER, MATH or PARENTHESIS """
    if is_digit(char):
        return DIGIT
    elif is_letter(char):
        return LETTER
    elif is_math_symbol(char):
        return MATH
    elif is_parenthesis(char):
        return PARENTHESIS
    else:
        raise AttributeError("Character " + char + " doesnt exists")


def is_power(power_box, next_char):
    """ Checks if next_char is a power of char """
    return power_box.top >= next_char.bottom
