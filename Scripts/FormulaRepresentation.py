from re import finditer


# Expression types
DIGIT = 0
LETTER = 1
MATH = 2
PARENTHESIS = 3


class Expression:
    def __init__(self, char):
        self.type = get_type(char)
        self.base = ""  # Expression string representation
        self.power = []  # Power expressions list

        self.add_char(char)

    def add_char(self, char):
        self.base += char
        pass


class Fraction:
    def __init__(self, num, den):
        self.num = num
        self.den = den


def get_python_rpz(formula, declared_variables):
    """ This function is used to get a python format equation from a graphical format. For instance:

                    2x² + 1
            f(x) =  ------  gives  f(x)=(2*x**(2)+1)/(3*x+2)
                    3x + 2

        For the moment, this handles no fraction.
    """

    # Sort declared variable by length because in the expression search we will look for larger expressions first
    declared_variables.sort(key=len, reverse=True)

    # Split formula in several expressions. An expression is a succession of non-separated characters of the same type
    # (digit, letter, math expression or parenthesis)

    # exp: Currently updated expression
    # base_expressions: List of expression in the main line of the formula
    # expressions: Currently updated list of expressions (can be base_expressions or a power of an expression)
    exp = Expression(formula.chars[0].prediction)
    base_expressions = [exp]
    expressions = base_expressions

    # power: Flag to know if we are updating a power expression or the base expression (useless but clearer)
    # power_box: Reference Box to check if the next added character is a power or not
    power = False  # Are we creating a power expression
    power_box = formula.chars[0]  # Base box reference when creating power expressions

    # Iterate through each character and add them in an expression
    for i in range(len(formula.chars) - 1):
        next_char = formula.chars[i + 1]

        # Handle powers
        if power:
            if not is_power(power_box, next_char):
                # Stop power mode
                power = False
                new_exp = Expression(next_char.prediction)
                exp = new_exp
                # Update power box because to know if a character is a power, we check its position relative to the
                # previous one
                power_box = next_char
                # Updated list of expressions is now the base expression
                base_expressions.append(exp)
                expressions = base_expressions
                continue

        else:
            if is_power(power_box, next_char):
                # Power begin
                power = True
                new_exp = Expression(next_char.prediction)
                exp.power = [new_exp]

                # Updated list of expressions is now a power expression
                expressions = exp.power
                exp = new_exp
                continue

            else:
                # Update power box because to know if a character is a power, we check its position relative to the
                # previous one
                power_box = formula.chars[i + 1]

        # Handle expressions
        # If the type is the same, add the next character to expression, else create a new expression
        if exp.type == DIGIT:
            if is_digit(next_char.prediction):
                exp.add_char(next_char.prediction)
            else:
                exp = Expression(next_char.prediction)
                expressions.append(exp)

        elif exp.type == LETTER:
            # Stop expression if the next character isn't a letter
            if is_letter(next_char.prediction):
                exp.add_char(next_char.prediction)
            else:
                # Create a new expression
                exp = Expression(next_char.prediction)
                expressions.append(exp)

        else:  # exp_type == MATH or exp_type == PARENTHESIS
            # Math symbols and parenthesis are alone in their expression
            exp = Expression(next_char.prediction)
            expressions.append(exp)

    # Split letter expressions by adding multiplications, for instance: 2acos becomes 2*a*cos
    # To do so, we look to the previously declared variables
    for exp in base_expressions:
        if exp.type == LETTER:
            exp.base = split_letter_expression(exp.base, declared_variables)

    # Add powers to the base strings
    for exp in base_expressions:
        if len(exp.power) > 0:
            power_str = ""
            for pow_exp in exp.power:
                power_str += pow_exp.base
            exp.base += "**(" + power_str + ')'

    # Add multiply between expressions
    python_string = base_expressions[0].base
    for i in range(1, len(base_expressions)):
        # Successions of DIGIT <-> LETTER, PARENTHESIS -> PARENTHESIS or LETTER -> LETTER have a multiplication between
        if {base_expressions[i - 1].type, base_expressions[i].type} == {DIGIT, LETTER} or \
                {base_expressions[i - 1].type, base_expressions[i].type} == {PARENTHESIS, PARENTHESIS} or \
                {base_expressions[i - 1].type, base_expressions[i].type} == {LETTER, LETTER}:
            # Add multiply between base expressions
            python_string += "*" + base_expressions[i].base
        else:
            python_string += base_expressions[i].base

    # TODO REMOVE LATER
    # We are looking for patterns like *1*...*1 with minimal number of characters in "..." to replace by (...)
    parenthesis = finditer(r"(\*1\*.{1," + str(len(python_string)) + r"}?\*1)", python_string)
    python_list = list(python_string)

    for par in parenthesis:
        python_list[par.start()] = ''
        python_list[par.start() + 1] = ''
        python_list[par.start() + 2] = '('
        python_list[par.start() + 4] = ''
        python_list[par.start() + 5] = ')'

    python_list = filter(lambda c: c != '', python_list)

    python_string = ""
    for char in python_list:
        python_string += char

    return python_string


def split_letter_expression(string, declared_variables):
    """ Split letter expressions by adding multiplications, for instance: 2acos becomes 2*a*cos.
        We use the list of previously declared variables to find them and surround them with parenthesis."""
    # Mark expression bounds
    bounds = []  # Contains blocked indexes

    # Iterate through each declared variable
    for var in declared_variables:
        # Look for each occurrence of this variable
        var_bounds = finditer(var, string)
        for var_bound in var_bounds:
            # Check if the found occurrence bounds aren't in previously found expression bounds
            if all([bound[0] >= var_bound.end() or bound[1] <= var_bound.start() for bound in bounds]):
                bounds.append([var_bound.start(), var_bound.end()])

    # Now lets create a list of min bounds and max bounds
    min_bounds, max_bounds = [bound[0] for bound in bounds], [bound[1] for bound in bounds]
    # Construct final string by adding * in both side of bounds
    final_string = string[0]

    for i in range(1, len(string)):
        if i in min_bounds:
            final_string += '*' + string[i]
        elif i in max_bounds and i != len(string) - 1:
            final_string += string[i] + '*'
        else:
            final_string += string[i]

    return final_string


# Character type checks
def is_digit(char):
    return ord('0') <= ord(char) <= ord('9')


def is_letter(char):
    return ord('A') <= ord(char) <= ord('Z')


def is_math_symbol(char):
    return char in ['-', '+', '/', '=']


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


def is_power(char, next_char):
    """ Checks if next_char is a power of char """
    return char.center[1] - 0.5 * char.height >= next_char.center[1] + 0.5 * next_char.height
