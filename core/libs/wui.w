import wuiGraphics
import raylib

class Widget():
    def new(.x=0, .y=0, .width=100, .height=100):

    def render():
        print()

class Label(Widget):
    def new(.text="", .fontSize=30, .color=Color BLACK):

    def render():
        drawText(.text, .x, .y, .fontSize, .color)

class App():
    def run(Widget widget):
        for C:
            InitWindow(800, 600, "Photon")
        for Python:
            title = "Photon"
            title = title.encode()
            InitWindow(800, 600, title)
        SetTargetFPS(60)
        while not WindowShouldClose():
            BeginDrawing()
            ClearBackground(WHITE)
            widget.render()
            EndDrawing()

