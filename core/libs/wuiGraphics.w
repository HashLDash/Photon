import raylib

def drawText(Font font, str text, float x, float y, int fontSize, Color color):
    for C:
        Vector2 pos
        pos.x = x
        pos.y = y
        DrawTextEx(font, text, pos, fontSize, 0.0, color)
    for Python:
        DrawTextEx(text.encode(), Vector2(x, y), fontSize, color)

def measureText(Font font, str text, int fontSize):
    for C:
        int width = MeasureTextEx(font, text, fontSize, 0).x
    for Python:
        int width = MeasureTextEx(font, text.encode(), fontSize, 0).x
    return width
