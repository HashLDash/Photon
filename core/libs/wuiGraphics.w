native import raylib

class Color():
    def new(.r=0.0, .g=0.0, .b=0.0, .a=1.0):

    def toNative():
        for C:
            raylib.Color color = raylib.BLACK
            color.r = .r * 255.0
            color.g = .g * 255.0
            color.b = .b * 255.0
            color.a = .a * 255.0
        for Python:
            native import pyray
            pyray.Color color = pyray.Color(int(.r*255), int(.g*255), int(.b*255), int(.a*255))
        return color

def drawText(Font font, str text, float x, float y, int fontSize, Color color):
    for C:
        Vector2 pos
        pos.x = x
        pos.y = y
        raylib.DrawTextEx(font, text, pos, fontSize, 0.0, color.toNative())
    for Python:
        raylib.DrawTextEx(font, text.encode(), pyray.Vector2(x, y), fontSize, 0.0, color.toNative())

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
        rec = pyray.Rectangle(x, y, width, height)
    raylib.DrawRectangleRounded(rec, radius, segments, color.toNative())

def drawRectangle(float x, float y, float width, float height, Color color):
    for C:
        raylib.DrawRectangle(x, y, width, height, color.toNative())
    for Python:
        int xi = x
        int yi = y
        int widthi = width
        int heighti = height
        raylib.DrawRectangle(xi, yi, widthi, heighti, color.toNative())

def drawCircle(float x, float y, float radius, Color color):
    for C:
        raylib.DrawCircle(x, y, radius, color.toNative())
    for Python:
        raylib.DrawCircle(int(x), int(y), radius, color.toNative())
