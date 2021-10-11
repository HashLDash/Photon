import raylib

def drawText(str text, float x, float y, int fontSize, Color color):
    DrawText(text, x, y, fontSize, color)

def measureText(str text, int fontSize):
    int width = MeasureText(text, fontSize)
    return width
