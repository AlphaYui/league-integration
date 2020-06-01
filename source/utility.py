# This file contains some basic utility functions to simplify code in other modules.

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