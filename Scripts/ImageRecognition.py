import tensorflow as tf
from PIL import Image
import numpy as np
import numpy.linalg as lin
import pyscreenshot as ImageGrab

from Page import Book

# Capture parameters
CAPTURE_SIZE = 32
CAPTURE_MARGIN = 2

# Model declaration
default_model_path = "../Models/handwriting.model"


# Module initialization
def init(model_path=default_model_path):
    image_predict.ocr_model = tf.keras.models.load_model(model_path)


# Tests if char is a math symbol or not
def is_math_symbol(char):
    """ Returns a math symbol if the character is one, else return None """
    # One line characters
    if len(char.lines) == 1:
        # Check for -
        if char.lines[0].aspect_ratio < 0.33:
            return '-'

    # Two lines characters
    elif len(char.lines) == 2:
        # Check for +
        ratios = [line.aspect_ratio for line in char.lines]
        ref_length = max([line.width for line in char.lines])
        if min(ratios) < 0.33 and max(ratios) > 3.0 and lin.norm(char.lines[0].center - char.lines[1].center) / ref_length < 0.15:
            return '+'

    return None


# Predicts the given character
def predict(char):
    # Check if the character is a math symbol
    math_symbol = is_math_symbol(char)

    if math_symbol:
        return math_symbol

    # Grab image
    x_offset, y_offset = Book.canvas.winfo_rootx(), Book.canvas.winfo_rooty()
    x1, y1, x2, y2 = char.get_bounds()
    img = ImageGrab.grab(bbox=(x_offset + x1, y_offset + y1, x_offset + x2, y_offset + y2))

    # Predict character
    return image_predict(img)


# Use CNN to predict the character from image
# image_predict function has one static attribute: ocr_model
def image_predict(img):
    # Check not to raise error
    if not hasattr(image_predict, "ocr_model"):
        image_predict.ocr_model = tf.keras.models.load_model(default_model_path)

    # Get size and scale factor
    size_x, size_y = img.size
    scale_factor = (CAPTURE_SIZE - 2 * CAPTURE_MARGIN) / np.max(img.size)

    # Convert raw image to a squared one
    img = img.convert('L').resize((int(scale_factor * size_x), int(scale_factor * size_y)), Image.ANTIALIAS)

    # Map values to 0.0 -> 1.0
    img = np.array(img)
    img = img - np.min(img)
    img = img / np.max(img)

    # Square the image and add margin
    margin_img = np.zeros((CAPTURE_SIZE, CAPTURE_SIZE))
    offset_x, rest_x = (CAPTURE_SIZE - img.shape[0]) // 2, (CAPTURE_SIZE - img.shape[0]) % 2
    offset_y, rest_y = (CAPTURE_SIZE - img.shape[1]) // 2, (CAPTURE_SIZE - img.shape[1]) % 2
    margin_img[offset_x:CAPTURE_SIZE - offset_x - rest_x, offset_y:CAPTURE_SIZE - offset_y - rest_y] = img

    # Predict character
    prediction = image_predict.ocr_model.predict(margin_img[None, :, :])

    prediction = np.argmax(prediction)

    if prediction < 10:
        # The prediction is a digit
        return chr(ord('0') + prediction)
    else:
        # The prediction is a letter
        return chr(ord('A') + prediction - 10)


