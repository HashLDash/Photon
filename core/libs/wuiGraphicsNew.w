native import raylib

class Color():
    def new(.r=255, .g=255, .b=255, .a=255):

def drawText(Font font, str text, float x, float y, int fontSize, Color color):
    for C:
        Vector2 pos
        pos.x = x
        pos.y = y
        raylib.Color rayColor = BLACK
        rayColor.r = color.r
        rayColor.g = color.g
        rayColor.b = color.b
        rayColor.a = color.a
        raylib.DrawTextEx(font, text, pos, fontSize, 0.0, rayColor)
    for Python:
        raylib.DrawTextEx(font, text.encode(), pyray.Vector2(x, y), fontSize, 0.0, color)

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
        raylib.Color rayColor = BLACK
        rayColor.r = color.r
        rayColor.g = color.g
        rayColor.b = color.b
        rayColor.a = color.a
        raylib.DrawRectangleRounded(rec, radius, segments, rayColor)
    for Python:
        rec = pyray.Rectangle(x, y, width, height)
        raylib.DrawRectangleRounded(rec, radius, segments, color)

def drawRectangle(float x, float y, float width, float height, Color color):
    for C:
        raylib.Color rayColor = raylib.BLACK
        rayColor.r = color.r
        rayColor.g = color.g
        rayColor.b = color.b
        rayColor.a = color.a
        raylib.DrawRectangle(x, y, width, height, rayColor)
    for Python:
        int xi = x
        int yi = y
        int widthi = width
        int heighti = height
        raylib.DrawRectangle(xi, yi, widthi, heighti, color)

def drawCircle(float x, float y, float radius, Color color):
    for C:
        raylib.Color rayColor = BLACK
        rayColor.r = color.r
        rayColor.g = color.g
        rayColor.b = color.b
        rayColor.a = color.a
        raylib.DrawCircle(x, y, radius, rayColor)
    for Python:
        raylib.DrawCircle(int(x), int(y), radius, color)
