# This file contains some basic utility functions to simplify code in other modules.

import urllib.request
from PIL import Image
import io

# Tries to convert a value to a string but returns the unchanged input silently on failure.
# Used to convert values that might already be a string.
# input: Value to be converted
def toStr(input):
    try:
        return str(input)
    except:
        return input

# Tries to convert a value to a string but returns None on failure.
# input: Value to be converted
def tryToStr(input):
    try:
        return str(input)
    except:
        return None

# Tries to convert a value to an int but returns the unchanged input silently on failure.
# Used to convert values that might already be an int.
# input: Value to be converted
def toInt(input):
    try:
        return int(input)
    except:
        return input

# Tries to convert a value to an int but returns None on failure.
# input: Value to be converted
def tryToInt(input):
    try:
        return int(input)
    except:
        return None

# Downloads an image from the given URL, scales it and returns it as byte array.
# url: URL from which to download the image
# size: The size the image should be scaled to as an int-tuple
def downloadImage(url, size = None):
    # Opens image from URL
    with urllib.request.urlopen(url) as imgFile:
        img = Image.open(imgFile)

        # Scales the image
        if size is not None:
            img.thumbnail(size)

        # Converts the scaled image to a byte array
        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format='PNG')
        imgByteArr = imgByteArr.getvalue()

        return imgByteArr