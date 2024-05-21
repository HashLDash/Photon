import wuiGraphics
native import raylib

Color WHITE = raylib.WHITE

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
    def new(.text="", .fontSize=40, .align="center", .valign="center", Color .color=raylib.BLACK):

    def render():
        for C:
            if .font.baseSize == 0:
                .font = raylib.LoadFontEx("assets/Roboto-Italic.ttf", .fontSize, 0, 250)
        for Python:
            fontName = "assets/Roboto-Italic.ttf"
            .font = raylib.LoadFontEx(fontName.encode(), .fontSize, raylib.ffi.new("int *", 0), 250)
        
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
            textWidth = wuiGraphics.measureText(.font, line, .fontSize)
            if .align == "center":
                dx = .x + (.width - textWidth)/2
            elif .align == "left":
                dx = .x
            elif .align == "right":
                dx = .x + .width - textWidth
            wuiGraphics.drawText(.font, line, dx, dy, .fontSize, .color)
            dy += .fontSize
        for C:
            .lines.len = 0
        for Python:
            .lines = []
    
class Button(Label):
    def new(func .onPress=pass, func .onRelease=pass, .radius=0.5, Color .buttonColor=raylib.BLUE):

    def render():
        int posX = raylib.GetMouseX()
        int posY = raylib.GetMouseY()
        if posX > .x and posX < .x + .width and posY > .y and posY < .y + .height:
            if raylib.IsMouseButtonPressed(MOUSE_LEFT_BUTTON):
                .onPress()
            elif raylib.IsMouseButtonReleased(MOUSE_LEFT_BUTTON):
                .onRelease()
        wuiGraphics.drawRoundedRectangle(.x, .y, .width, .height, .radius, .buttonColor)
        super.render()

class Layout(Widget):
    def new(Widget[] .children=[]):

    def update():
        for child in .children:
            child.update()

    def render():
        for child in .children:
            child.render()

    def addWidget(Widget widget):
        .children.append(widget)

    def removeWidget(Widget widget):
        .children.remove(widget)

class Box(Layout):
    def new(.orientation='vertical'):

    def render():
        dx = .x
        dy = .y
        if .children.len > 0:
            if .orientation == 'vertical':
                wHeight = .height / .children.len
                for child in .children:
                    child.x = dx
                    child.y = dy
                    child.width = .width
                    child.height = wHeight
                    child.render()
                    dy += wHeight
            else:
                wWidth = .width / .children.len
                for child in .children:
                    child.x = dx
                    child.y = dy
                    child.width = wWidth
                    child.height = .height
                    child.render()
                    dx += wWidth

class App():
    def new(Color .background=raylib.WHITE, .fps=60, .width=800, .height=600, .title="Photon"):

    def run(Widget widget):
        for C:
            raylib.InitWindow(.width, .height, .title)
        for Python:
            raylib.InitWindow(.width, .height, .title.encode())
        raylib.SetTargetFPS(.fps)
        while not raylib.WindowShouldClose():
            raylib.BeginDrawing()
            raylib.ClearBackground(.background)
            widget.update()
            widget.render()
            raylib.EndDrawing()

