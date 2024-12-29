native import raylib
for Python:
    native import pyray

class Color():
    def new(.r=0.0, .g=0.0, .b=0.0, .a=255.0):

    def toNative():
        for JavaScript:
            raylib.Color color = raylib.Color(.r, .g, .b, .a)
        for C:
            raylib.Color color = raylib.BLACK
            color.r = .r
            color.g = .g
            color.b = .b
            color.a = .a
        for Python:
            pyray.Color color = pyray.Color(int(.r), int(.g), int(.b), int(.a))
        return color

def drawText(Font font, str text, float x, float y, int fontSize, Color color):
    for JavaScript:
        raylib.DrawTextEx(font, text.encode(), raylib.Vector2(x, y), fontSize, 0.0, color.toNative())
    for C:
        Vector2 pos
        pos.x = x
        pos.y = y
        raylib.DrawTextEx(font, text, pos, fontSize, 0.0, color.toNative())
    for Python:
        raylib.DrawTextEx(font, text.encode(), pyray.Vector2(x, y), fontSize, 0.0, color.toNative())

def measureText(Font font, str text, int fontSize):
    for JavaScript:
        int width = raylib.MeasureTextEx(font, text, fontSize, 0).x
    for C:
        int width = raylib.MeasureTextEx(font, text, fontSize, 0).x
    for Python:
        int width = raylib.MeasureTextEx(font, text.encode(), fontSize, 0).x
    return width

def drawRoundedRectangle(float x, float y, float width, float height, float radius, Color color):
    segments = 10
    for JavaScript:
        rec = raylib.Rectangle(x, y, width, height)
    for C:
        Rectangle rec
        rec.x = x
        rec.y = y
        rec.width = width
        rec.height = height
    for Python:
        rec = pyray.Rectangle(x, y, width, height)
    raylib.DrawRectangleRounded(rec, radius, segments, color.toNative())

def drawRectangle(float x, float y, float width, float height, Color color):
    for JavaScript:
        raylib.DrawRectangle(x, y, width, height, color.toNative())
    for C:
        raylib.DrawRectangle(x, y, width, height, color.toNative())
    for Python:
        int xi = x
        int yi = y
        int widthi = width
        int heighti = height
        raylib.DrawRectangle(xi, yi, widthi, heighti, color.toNative())

def drawCircle(float x, float y, float radius, Color color):
    for JavaScript:
        raylib.DrawCircle(x, y, radius, color.toNative())
    for C:
        raylib.DrawCircle(x, y, radius, color.toNative())
    for Python:
        raylib.DrawCircle(int(x), int(y), radius, color.toNative())
