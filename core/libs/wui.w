import wuiGraphics
import raylib

class Widget():
    def new(.x=0.0, .y=0.0, .width=100.0, .height=100.0):

    def onKeyPress(int a):

    def update():

    def render():

class Label(Widget):
    Font font
    str lines = []
    def new(.text="", .fontSize=40, .align="center", .valign="center", .color=Color BLACK):

    def render():
        if .font.baseSize == 0:
            .font = LoadFontEx("assets/Roboto-Italic.ttf", .fontSize, 0, 250)
        
        lineBuffer = ''
        word = ''
        for c in .text:
            if c == ' ':
                if measureText(.font, lineBuffer+' '+word, .fontSize) > .width:
                    .lines += lineBuffer
                    lineBuffer = word
                else:
                    if lineBuffer == '':
                        lineBuffer = word
                    else:
                        lineBuffer += ' ' + word
                word = ''
            elif c == '\n':
                if measureText(.font, lineBuffer+' '+word, .fontSize) > .width:
                    .lines += lineBuffer
                    .lines += word
                else:
                    if lineBuffer == '':
                        .lines += word
                    else:
                        .lines += lineBuffer + ' ' + word
                lineBuffer = ''
                word = ''
            else:
                word += c
        if measureText(.font, lineBuffer+word, .fontSize) > .width:
            .lines += lineBuffer
            .lines += word
        else:
            .lines += lineBuffer + word
        
        dy = .y
        if .valign == "center":
            dy += (.height - .lines.len * .fontSize)/2
        elif .valign == "bottom":
            dy += .height - .lines.len * .fontSize

        dx = 0.0
        for line in .lines:
            textWidth = measureText(.font, line, .fontSize)
            if .align == "center":
                dx = .x + (.width - textWidth)/2
            elif .align == "left":
                dx = .x
            elif .align == "right":
                dx = .x + .width - textWidth
            drawText(.font, line, dx, dy, .fontSize, .color)
            dy += .fontSize
        .lines.len = 0

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

