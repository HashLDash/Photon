import raylib

def drawText(str text, float x, float y, int fontSize, Color color):
    for C:
        DrawText(text, x, y, fontSize, color)
    for Python:
        DrawText(text.encode(), x, y, fontSize, color)

def measureText(str text, int fontSize):
    for C:
        int width = MeasureText(text, fontSize)
    for Python:
        int width = MeasureText(text.encode(), fontSize)
    return width
