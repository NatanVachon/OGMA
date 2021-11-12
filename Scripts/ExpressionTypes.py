FRACTION = 0
DIGIT = 1
LETTER = 2
MATH = 3
PARENTHESIS = 4


# Character type checks
def is_digit(char):
    return ord('0') <= ord(char) <= ord('9')


def is_letter(char):
    return ord('A') <= ord(char) <= ord('Z')


def is_math_symbol(char):
    return char in ['-', '+', '/', '*', '=']


def is_parenthesis(char):
    return char in ['(', ')']
