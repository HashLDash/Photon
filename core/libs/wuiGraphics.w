native import raylib

def drawText(Font font, str text, float x, float y, int fontSize, Color color):
    for C:
        Vector2 pos
        pos.x = x
        pos.y = y
        raylib.DrawTextEx(font, text, pos, fontSize, 0.0, color)
    for Python:
        raylib.DrawTextEx(text.encode(), Vector2(x, y), fontSize, color)

def measureText(Font font, str text, int fontSize):
    for C:
        int width = raylib.MeasureTextEx(font, text, fontSize, 0).x
    for Python:
        int width = raylib.MeasureTextEx(font, text.encode(), fontSize, 0).x
    return width

def drawRoundedRectangle(float x, float y, float width, float height, float radius, Color color):
    segments = 10
    for C:
        Rectangle rec
        rec.x = x
        rec.y = y
        rec.width = width
        rec.height = height
    for Python:
        rec = raylib.Rectangle(x, y, width, height)
    raylib.DrawRectangleRounded(rec, radius, segments, color)

