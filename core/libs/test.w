native import raylib
import wuiGraphics

def pass():
    print("Apertou!!")

class Widget():
    def new(.x=0.0, .y=0.0, .width=100.0, .height=100.0):

    def onKeyPress(int a):

    def update():

    def render():

class Label(Widget):
    Font font
    str[] lines = []
    def new(.text="", .fontSize=40, .align="center", .valign="center", Color .color= raylib.BLACK):

    def render():
        if .font.baseSize == 0:
            .font = raylib.LoadFontEx("assets/Roboto-Italic.ttf", .fontSize, 0, 250)
        
        lineBuffer = ''
        word = ''
        .lines = []
        for c in .text:
            if c == ' ':
                if wuiGraphics.measureText(.font, lineBuffer+' '+word, .fontSize) > .width:
                    .lines.append(lineBuffer)
                    lineBuffer = word
                else:
                    if lineBuffer == '':
                        lineBuffer = word
                    else:
                        lineBuffer += ' ' + word
                word = ''
            elif c == '\n':
                if wuiGraphics.measureText(.font, lineBuffer+' '+word, .fontSize) > .width:
                    .lines.append(lineBuffer)
                    .lines.append(word)
                else:
                    if lineBuffer == '':
                        .lines.append(word)
                    else:
                        .lines.append(lineBuffer + ' ' + word)
                lineBuffer = ''
                word = ''
            else:
                word += c
        if wuiGraphics.measureText(.font, lineBuffer+word, .fontSize) > .width:
            .lines.append(lineBuffer)
            .lines.append(word)
        else:
            .lines.append(lineBuffer + word)
        
        dy = .y
        if .valign == "center":
            dy += (.height - .lines.len * .fontSize)/2
        elif .valign == "bottom":
            dy += .height - .lines.len * .fontSize

        dx = 0.0
        for line in .lines:
            int textWidth = wuiGraphics.measureText(.font, line, .fontSize)
            if .align == "center":
                dx = .x + (.width - textWidth)/2
            elif .align == "left":
                dx = .x
            elif .align == "right":
                dx = .x + .width - textWidth
            wuiGraphics.drawText(.font, line, dx, dy, .fontSize, .color)
            dy += .fontSize
        .lines.len = 0

class Layout(Widget):
    def new(Widget[] .children=[]):

    def render():
        for child in .children:
            child.render()

    def addWidget(Widget widget):
        .children.append(widget)

    def removeWidget(Widget widget):
        .children.remove(widget)

class Button(Label):
    def new(.radius=0.5, Color .buttonColor=raylib.BLUE, func .onPress=pass):

    def render():
        int posX = raylib.GetMouseX()
        int posY = raylib.GetMouseY()
        if posX > .x and posX < .x + .width and posY > .y and posY < .y + .height:
            if raylib.IsMouseButtonPressed(raylib.MOUSE_LEFT_BUTTON):
                .onPress()
        wuiGraphics.drawRoundedRectangle(.x, .y, .width, .height, .radius, .buttonColor)

class App():
    def run(Widget widget):
        InitWindow(800, 600, "Photon")
        SetTargetFPS(60)
        while not WindowShouldClose():
            BeginDrawing()
            ClearBackground(raylib.WHITE)
            widget.render()
            EndDrawing()
