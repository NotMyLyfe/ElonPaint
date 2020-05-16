'''ElonMuskPaint.py
By Gordon Lin
Simple photo editting software based on Elon Musk, contains pens, pencil, markers, erasers, polygon and line, eyedropper, paintbucket, text, smudge, copy and paste, mutliple backgrounds, undo and redo, save and load, and stickers'''

# Importing necessary libraries
from pygame import *
from random import *
from math import *
from queue import Queue
import multiprocessing
import os
import urllib.request
from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.colorchooser import askcolor
from ctypes import c_bool
import csv
import json

font.init() # Intialize fonts

# Opens and reads config.json file
with open(os.path.dirname(os.path.realpath(__file__)) + '\\source\\config.json', "r") as readFile:
    config = json.load(readFile)

# Checks if config file requests to use default config or request to check for new tweets on startup
if config['useDefaults'] or config['config']['checkTweetsOnStart']:
    try: # attempts to download tweets from Dropbox, after being uploaded from remote server to Dropbox using Tweepy API
        urllib.request.urlretrieve("https://dl.dropboxusercontent.com//s/wrqxrdbr0p2idc8/tweets.csv?dl=0", os.path.dirname(os.path.realpath(__file__)) + "\\source\\tweets.csv")
    except:
        pass

tweets = [] # list full of tweets from Elon Musk

# Opens file containing tweets, and reads and imports data from tweets.csv file into tweets list
with open(os.path.dirname(os.path.realpath(__file__)) + '\\source\\tweets.csv', "r", encoding = 'utf-8') as File:
    for i in csv.reader(File):
        for j in i:
            tweets.append(j)

root = Tk() # Starts tkinter interpreter

# Gets the width and height of the computer screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

root.withdraw() # Quits tkinter interpreter

iconImage = image.load(os.path.dirname(os.path.realpath(__file__)) + '\\source\\imgs\\icon.png') # loads image of window icon

stickerImages = [] # list of image of stickers

# gets all the images in the stickers directory and appends them into stickerImages
for (dirpath, dirnames, filenames) in os.walk(os.path.dirname(os.path.realpath(__file__)) + "\\source\\imgs\\stickers"):
    filenames.sort()
    for i in filenames:
        stickerImages.append(image.load(os.path.dirname(os.path.realpath(__file__)) + '\\source\\imgs\\stickers\\' + i))
    break

fonts = [] # list of fonts

# gets all the fonts in the fonts directory and appends the name and font into the fonts list
for (dirpath, dirnames, filenames) in os.walk(os.path.dirname(os.path.realpath(__file__)) + "\\source\\fonts"):
    filenames.sort()
    for i in filenames:
        tempFont = i[:i.rfind(".ttf")]
        fonts.append([font.Font(os.path.dirname(os.path.realpath(__file__)) + '\\source\\fonts\\' + i, 64), tempFont])
    break

backgroundImages = [] # list of background images

# gets all the images in the backgroundImgs directory and appends them into backgroundImages
for (dirpath, dirnames, filenames) in os.walk(os.path.dirname(os.path.realpath(__file__)) + "\\source\\imgs\\backgroundImgs"):
    filenames.sort()
    for i in filenames:
        backgroundImages.append(image.load(os.path.dirname(os.path.realpath(__file__)) + '\\source\\imgs\\backgroundImgs\\' + i))
    break

# checks if the config file askes to use default settings and to set it to 100 (as default), else set it to desired amount by user
if config['useDefaults']:
    maxToolSize = 100
else:
    maxToolSize = config['config']['maxToolSize']

# main canvas screen importing values shared across the other processes
def mainScreen(toolbarOption, backgroundImageOption, toolSizeVal, colours, stickerOption, fillPolygon, fontSelection, copyOption, clearCanvas, ableToUndoRedo, undoRedoValue, saveLoadOption, stickerRotation, flipSticker, mousePosVal):
    # gets global lists and variables
    global iconImage
    global backgroundImages
    global maxToolSize

    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (screen_width//2 - 640, screen_height//2-485) # sets the position of window to slightly above the centre of the screen ontop of the toolbar
    screen = display.set_mode((1280, 720)) # surface of the canvas and screen
    # name and icon of the window
    display.set_caption("Elon Musk Paint 1.0")
    display.set_icon(iconImage)

    fullBackground = Surface((1280, 720)) # surface of background image

    startingPos = [0, 0] # starting position for polygon/line and copy/paste tools
    lastMousePos = [] # last known mouse position

    blankBackground = False # if the background is blank, or importing image and background image is unknown

    running = True # if pygame window is running
    canvasSurface = Surface((1280, 720)) # copy of the screen

    undoRedo = [] # list of surfaces for undo and redo
    undoRedoPos = -1 # position for undo redo in the undoredo list

    stickerTool = False # if stickerTool was/is being used

    while running:
        # variables for if the mouse was just pressed down or just released
        justPressed = False 
        justReleased = False
        justPressedRight = False

        for e in event.get():
            if e.type == QUIT: # quits the process upon being quit
                running = False
            if e.type == MOUSEBUTTONDOWN:
                if e.button == 1:
                    justPressed = True
                if e.button == 3:
                    justPressedRight = True
                if e.button == 4 and toolSizeVal.value < maxToolSize and not ((toolbarOption.value == 6 or toolbarOption.value == 7)and fillPolygon.value): # checks if the toolSize is within in the maxToolSize limits, and that circles or rectangles are not being overriden with fill
                    toolSizeVal.value += 1 # increases size of toolSize
                if e.button == 5 and toolSizeVal.value > 1 and not ((toolbarOption.value == 6 or toolbarOption.value == 7)and fillPolygon.value): # checks if the toolSize is greater than 1 and that circles or rectangles are not being overriden with fill
                    toolSizeVal.value -= 1 # decreases size of toolSize
            if e.type == MOUSEBUTTONUP and e.button == 1:
                justReleased = True
            if e.type == KEYDOWN:
                if key.get_pressed()[K_LCTRL]:
                    if key.get_pressed()[K_z] and ableToUndoRedo[0]: # if l ctrl + z was just pressed and that it's able to undo
                        undoRedoValue.value = 1 # sets undoRedoValue to undo value (1)
                    elif key.get_pressed()[K_y] and ableToUndoRedo[1]: # if l ctrl + y was just pressed and that it's able to redo
                        undoRedoValue.value = 2 # sets undoRedoValue to redo value (2)

        mousePos = mouse.get_pos() # get mouse position
        movement = mouse.get_rel() # get if mouse is moved
        clicked = mouse.get_pressed() # get if mouse is clicked

        # stores mousePos to multiprocessing.Array to communicate among processes
        mousePosVal[0] = mousePos[0]
        mousePosVal[1] = mousePos[1]

        if clearCanvas.value: # checks if program is asked to clear the canvas screen
            if  len (backgroundImages) > backgroundImageOption.value >= 0: # checks if the backgroundImageOption is within the limits of the backgroundImages list
                fullBackground.blit(backgroundImages[backgroundImageOption.value], (0, 0)) # sets fullBackground to the selected backgroundImage
                screen.blit(fullBackground, (0, 0))
                blankBackground = False # background is not blank is has an image in the background so sets false
            else: # is beyond the limits of the backgroundImages list
                screen.fill((255, 255, 255))
                blankBackground = True # bakcground option is invalid in backgroundImgs list and sets blackBackground to true
            clearCanvas.value = False # resets clearCanvas
            undoRedo = undoRedo[:undoRedoPos+1] # removes all the redo options
            # adds copy of the screen to undoRedo
            undoRedo.append([screen.copy(), backgroundImageOption.value])
            undoRedoPos += 1

        if saveLoadOption.value > 0:
            if saveLoadOption.value == 1: # if save option is selected (1)
                try: # attempts to ask user for save name of file and attempts to save
                    saveName = asksaveasfilename(initialfile='Untitled.png', filetypes=[("Picture files", "*.png *.jpg *.bmp"), ("All Files", "*.*")])
                    image.save(screen.copy(), saveName)
                except:
                    pass
            elif saveLoadOption.value == 2: # if load option is selected (2)
                try: # attempts to ask user for a file to load
                    openName = askopenfilename(filetypes=[("Picture files", "*.png *.jpg *.bmp"), ("All Files", "*.*")])
                    newImage = image.load(openName)
                    if newImage.get_width() == 1280 and newImage.get_height() == 720: # if image is the proper size of the canvas and can be placed onto the screen
                        screen.blit(newImage, (0, 0))
                        undoRedo = undoRedo[:undoRedoPos+1] # removes all the redo options
                        undoRedoPos+=1
                        undoRedo.append([screen.copy(), -1]) # adds copy of the screen plus the value for blank screen
                        blankBackground = True # background option is unknown and set to blank
                except:
                    pass
            saveLoadOption.value = 0 # resets value of saveLoadOption

        toolSize = toolSizeVal.value # gets the size of the tool from the multiprocessing value
        toolOption = toolbarOption.value # gets the option of the tool fron the multiprocessing value

        if stickerTool and not toolOption == 16: # if stickerTool is True, but sticker value (16) is not selected for toolOption
            stickerTool = False # resets back to False
            stickerRotation.value = 0 # resets back to 0
            # resets screen back to normal
            canvasSurface = undoRedo[undoRedoPos][0]
            screen.blit(canvasSurface, (0, 0))

        if clicked[0]: # if left click is pressed
            if toolOption == 0: # if marker option (0) is selected in toolOption
                draw.line(screen, colours, mousePos, lastMousePos, toolSize)
            elif toolOption == 1: # if eraser option (1) is selected in toolOption
                try:
                    if not blankBackground:
                        eraserRect = [mousePos[0] - toolSize, mousePos[1] - toolSize, toolSize * 2, toolSize * 2] # gets topLeft position of eraser and size
                        dif = [0, 0] # get distance from x at 0 and y at 0 if eraserRect[0] is negative or eraserRect[1] is negative
                        # checks if the eraser circle goes beyond the boundaries of the canvas
                        if eraserRect[0] < 0:
                            dif[0] = eraserRect[0]
                            eraserRect[0] = 0
                        if eraserRect[0] + eraserRect[2] > 1280:
                            eraserRect[2] -= eraserRect[0] + toolSize * 2 - 1280
                        if eraserRect[1] < 0:
                            dif[1] = eraserRect[1]
                            eraserRect[1] = 0
                        if eraserRect[1] + eraserRect[3] > 720:
                            eraserRect[3] -= eraserRect[1] + toolSize * 2 - 720
                        
                        eraser = fullBackground.subsurface(eraserRect).convert_alpha() # gets the region available to eraser
                        draw.circle(eraser, (255, 255, 255, 0), (toolSize + dif[0], toolSize + dif[1]), toolSize * 2,toolSize) # clears a circle around the circle for eraser in order to make a circular erase tool
                        screen.blit(eraser, (eraserRect[0], eraserRect[1]))

                        lastPos = [i for i in lastMousePos] # last position of eraser
                        circleDist = ((mousePos[0] - lastPos[0]) ** 2 + (mousePos[1] - lastPos[1]) ** 2) ** 0.5 # distance from last position of eraser
                        while circleDist > toolSize:
                            if circleDist / toolSize < 2: # checks if last position of eraser is tangent to the eraser circle at mousePos
                                eraserRect = [(lastPos[0] + mousePos[0]) // 2 - toolSize, (lastPos[1] + mousePos[1]) // 2 - toolSize, toolSize*2, toolSize*2] # gets midway point of last position and current position as topLeft of eraser and eraser size
                                dif = [0, 0] # get distance from x at 0 and y at 0 if eraserRect[0] is negative or eraserRect[1] is negative
                                # checks if the eraser circle goes beyond the boundaries of the canvas
                                if eraserRect[0] < 0:
                                    dif[0] = eraserRect[0]
                                    eraserRect[0] = 0
                                if eraserRect[0] + eraserRect[2] > 1280:
                                    eraserRect[2] -= eraserRect[0] + toolSize * 2 - 1280
                                if eraserRect[1] < 0:
                                    dif[1] = eraserRect[1]
                                    eraserRect[1] = 0
                                if eraserRect[1] + eraserRect[3] > 720:
                                    eraserRect[3] -= eraserRect[1] + toolSize * 2 - 720
                                eraser = fullBackground.subsurface(eraserRect).convert_alpha() # gets the region available to eraser
                                draw.circle(eraser, (255, 255, 255, 0), (toolSize + dif[0], toolSize + dif[1]), toolSize * 2, toolSize) # clears a circle around the circle for eraser in order to make a circular erase tool
                                screen.blit(eraser, (eraserRect[0], eraserRect[1]))
                                break
                            else:
                                ang = atan2(mousePos[1] - lastPos[1], mousePos[0] - lastPos[0]) # finds angle between last eraser position and current position
                                # gets next position of eraser
                                lastPos[0] += cos(ang) * toolSize
                                lastPos[1] += sin(ang) * toolSize
                                eraserRect = [int(lastPos[0]) - toolSize, int(lastPos[1]) - toolSize, toolSize*2, toolSize*2] # gets midway point of last position and current position as topLeft of eraser and eraser size
                                dif = [0, 0] # get distance from x at 0 and y at 0 if eraserRect[0] is negative or eraserRect[1] is negative
                                # checks if the eraser circle goes beyond the boundaries of the canvas
                                if eraserRect[0] < 0:
                                    dif[0] = eraserRect[0]
                                    eraserRect[0] = 0
                                if eraserRect[0] + eraserRect[2] > 1280:
                                    eraserRect[2] -= eraserRect[0] + toolSize * 2 - 1280
                                if eraserRect[1] < 0:
                                    dif[1] = eraserRect[1]
                                    eraserRect[1] = 0
                                if eraserRect[1] + eraserRect[3] > 720:
                                    eraserRect[3] -= eraserRect[1] + toolSize * 2 - 720
                                eraser = fullBackground.subsurface(eraserRect).convert_alpha() # gets the region available to eraser
                                draw.circle(eraser, (255, 255, 255, 0), (toolSize + dif[0], toolSize + dif[1]), toolSize * 2, toolSize) # clears a circle around the circle for eraser in order to make a circular erase tool
                                screen.blit(eraser, (eraserRect[0], eraserRect[1]))
                                circleDist = ((mousePos[0] - lastPos[0]) ** 2 + (mousePos[1] - lastPos[1]) ** 2) ** 0.5 # finds distance from last eraser position to current mouse position
                    else:
                        draw.circle(screen, (255, 255, 255), mousePos, toolSize)
                        lastPos = [i for i in lastMousePos] # last position of eraser
                        circleDist = ((mousePos[0] - lastPos[0]) ** 2 + (mousePos[1] - lastPos[1]) ** 2) ** 0.5 # distance from current position to last position
                        while circleDist > toolSize:
                            if circleDist / toolSize < 2: # checks if last position of eraser is tangent to the eraser circle at mousePos
                                draw.circle(screen, (255, 255, 255), (int(lastPos[0] + mousePos[0]) // 2, int(lastPos[1] + mousePos[1]) // 2),toolSize) # draws a circle midway between the last eraser position and mouse position
                                break
                            else:
                                ang = atan2(mousePos[1] - lastPos[1], mousePos[0] - lastPos[0]) # finds angle between last eraser position and current position
                                # gets next position of eraser
                                lastPos[0] += cos(ang) * toolSize
                                lastPos[1] += sin(ang) * toolSize
                                draw.circle(screen, (255, 255 ,255), (int(lastPos[0]), int(lastPos[1])), toolSize)
                                circleDist = ((mousePos[0] - lastPos[0]) ** 2 + (mousePos[1] - lastPos[1]) ** 2) ** 0.5 # distance from current position to last position
                except:
                    pass
            elif toolOption == 2: # if pen option (2) is selected in toolOption
                draw.circle(screen, colours, mousePos, toolSize)

                lastPos = [i for i in lastMousePos] # last position of pen
                circleDist = ((mousePos[0] - lastPos[0])**2 + (mousePos[1] - lastPos[1])**2)**0.5 # distance from current position to last position
                while circleDist > toolSize:
                    if circleDist/toolSize < 2: # check if last position of pen is tangent to the pen circle at mouse Pos
                        draw.circle(screen, colours, (int(lastPos[0] + mousePos[0])//2, int(lastPos[1] + mousePos[1])//2), toolSize) # draws a circle midway between the last pen position and mouse position
                        break
                    else:
                        ang = atan2(mousePos[1] - lastPos[1], mousePos[0] - lastPos[0]) # find angle between last pen position and current position
                        # gets next position of pen
                        lastPos[0] += cos(ang) * toolSize
                        lastPos[1] += sin(ang) * toolSize
                        draw.circle(screen, colours, (int(lastPos[0]), int(lastPos[1])), toolSize)
                        circleDist = ((mousePos[0] - lastPos[0]) ** 2 + (mousePos[1] - lastPos[1]) ** 2) ** 0.5 # distance from current position to last position
            elif toolOption == 3: # if pencil option (3) is selected in toolOption
                pencilShading = [colours[0], colours[1], colours[2], randint(50, 200)] # gets the colour + random opacity
                pencil = Surface((toolSize*2, toolSize*2), SRCALPHA) # new surface of pencil
                draw.circle(pencil, pencilShading, (toolSize, toolSize), toolSize)
                screen.blit(pencil, (mousePos[0] - toolSize, mousePos[1] - toolSize))

                lastPos = [i for i in lastMousePos] # last position of pencil
                circleDist = ((mousePos[0] - lastPos[0]) ** 2 + (mousePos[1] - lastPos[1]) ** 2) ** 0.5 # distance from current position to last position
                while circleDist > toolSize:
                    if circleDist / toolSize < 2: # checks if last position is tangent to the pencil circle at mouse pos
                        pencilShading = [colours[0], colours[1], colours[2], randint(100, 200)] # gets the colour + random opacity
                        pencil = Surface((toolSize * 2, toolSize * 2), SRCALPHA) # new surface of pencil
                        draw.circle(pencil, pencilShading, (toolSize, toolSize), toolSize)
                        screen.blit(pencil, ((lastPos[0] + mousePos[0])//2 - toolSize, (lastPos[1] + mousePos[1])//2 - toolSize)) # blitted midway between last position and mouse position
                        break
                    else:
                        ang = atan2(mousePos[1] - lastPos[1], mousePos[0] - lastPos[0]) # find angle between last pen position and current position
                        # gets next position of pencil
                        lastPos[0] += cos(ang) * toolSize
                        lastPos[1] += sin(ang) * toolSize

                        pencilShading = [colours[0], colours[1], colours[2], randint(100, 200)]# gets the colour + random opacity
                        pencil = Surface((toolSize * 2, toolSize * 2), SRCALPHA) # new surface of pencil
                        draw.circle(pencil, pencilShading, (toolSize, toolSize), toolSize)
                        screen.blit(pencil, (lastPos[0] - toolSize, lastPos[1] - toolSize))
                        circleDist = ((mousePos[0] - lastPos[0]) ** 2 + (mousePos[1] - lastPos[1]) ** 2) ** 0.5 # distance from current position to last position
            elif toolOption == 4: # if spray option (4) is selected in toolOption
                sprayColour = [colours[0], colours[1], colours[2], randint(0, 255)] # gets colours + random opacity
                try:
                    spraySize = randint(1, toolSize//2) # gets random spray size
                    spray = Surface((spraySize, spraySize), SRCALPHA) # spray surface
                    draw.circle(spray, sprayColour, (spraySize//2, spraySize//2), spraySize//2)
                    sprayDist = toolSize - spraySize
                    sprayX = randint(mousePos[0] - sprayDist, mousePos[0] + sprayDist)
                    sprayY = randint(mousePos[1] - sprayDist, mousePos[1] + sprayDist)
                    screen.blit(spray, (sprayX, sprayY)) # draws a random circle at a random ceratin distance from mouse pos
                except:
                    pass
            elif toolOption == 5: # if straight line option (5) is selected in toolOption
                if justPressed:
                    # store a copy of the starting position of the line as well the screen
                    startingPos = mousePos 
                    canvasSurface = screen.copy()
                else:
                    screen.blit(canvasSurface, (0, 0))
                    if key.get_pressed()[K_LSHIFT]: # 45 degree straight lines
                        ang = atan2(mousePos[1] - startingPos[1], mousePos[0] - startingPos[0]) # finds angle
                        percentage = ang/pi # finds the percentage of the angle

                        # connects line to closest 45 degree angle
                        if 0.625 >= abs(percentage) >= 0.375:
                            draw.line(screen, colours, startingPos, (startingPos[0], mousePos[1]), toolSize)
                        elif 0.75 >= abs(percentage) >= 0.25:
                            if mousePos[0] > startingPos[0]:
                                draw.line(screen, colours, startingPos, (startingPos[0] + abs(mousePos[1] - startingPos[1]), mousePos[1]), toolSize)
                            else:
                                draw.line(screen, colours, startingPos, (startingPos[0] - abs(mousePos[1] - startingPos[1]), mousePos[1]), toolSize)
                        elif 0.875 >= abs(percentage) >= 0.125:
                            if mousePos[1] > startingPos[1]:
                                draw.line(screen, colours, startingPos, (mousePos[0], startingPos[1] + abs(mousePos[0] - startingPos[0])), toolSize)
                            else:
                                draw.line(screen, colours, startingPos, (mousePos[0], startingPos[1] - abs(mousePos[0] - startingPos[0])), toolSize)
                        else:
                            draw.line(screen, colours, startingPos, (mousePos[0], startingPos[1]), toolSize)
                    else:
                        draw.line(screen, colours, startingPos, mousePos, toolSize)
            elif toolOption == 6: # if rectangle option (6) is selected in toolOption
                if fillPolygon.value: # if user selected to fill polygons, overrides toolSize
                    toolSize = 0 
                if justPressed:
                    # stores starting position and starting screen
                    startingPos = mousePos
                    canvasSurface = screen.copy()
                else:
                    screen.blit(canvasSurface, (0, 0))
                    length = mousePos[0] - startingPos[0]
                    if key.get_pressed()[K_LSHIFT]:
                        if key.get_pressed()[K_LCTRL]: # creates square centred around the starting position
                            length = abs(length)
                            if toolSize > 1: # fills in the corners of the square
                                draw.rect(screen, colours, (int(startingPos[0] - length - toolSize/2 + 1), int(startingPos[1] - length - toolSize/2 + 1), toolSize, toolSize))
                                draw.rect(screen, colours, (int(startingPos[0] - length - toolSize/2 + 1), int(startingPos[1] + length - toolSize/2), toolSize, toolSize))
                                draw.rect(screen, colours, (int(startingPos[0] + length - toolSize/2), int(startingPos[1] - length - toolSize/2 + 1), toolSize, toolSize))
                                draw.rect(screen, colours, (int(startingPos[0] + length - toolSize/2), int(startingPos[1] + length - toolSize/2), toolSize, toolSize))
                            draw.rect(screen, colours, (startingPos[0] - length, startingPos[1] - length, length * 2, length * 2), toolSize)
                        else:
                            # creates a square
                            if (mousePos[0] >= startingPos[0] and mousePos[1] >= startingPos[1]) or (mousePos[0] <= startingPos[0] and mousePos[1] <= startingPos[1]): # draws only on quadrants 2, 4 around the starting position
                                if toolSize > 1: # fills in the corners of the square
                                    draw.rect(screen, colours, (int(startingPos[0] - toolSize/2 + 1), int(startingPos[1] - toolSize/2 + 1), toolSize, toolSize))
                                    draw.rect(screen, colours, (int(startingPos[0] - toolSize/2 + 1), int(startingPos[1] + length - toolSize/2), toolSize, toolSize))
                                    draw.rect(screen, colours, (int(startingPos[0] + length - toolSize/2), int(startingPos[1] - toolSize/2 + 1), toolSize, toolSize))
                                    draw.rect(screen, colours, (int(startingPos[0] + length - toolSize/2), int(startingPos[1] + length - toolSize/2), toolSize, toolSize))
                                draw.rect(screen, colours, (startingPos[0], startingPos[1], length, length), toolSize)
                            elif mousePos[1] > startingPos[1]: # draws on quadrant 3 around the starting position
                                if toolSize > 1: # fills in the corners of the square
                                    draw.rect(screen, colours, (int(mousePos[0] - toolSize/2 + 1), int(startingPos[1] - toolSize/2 + 1), toolSize, toolSize))
                                    draw.rect(screen, colours, (int(mousePos[0] - toolSize/2 + 1), int(startingPos[1] + abs(length) - toolSize/2), toolSize, toolSize))
                                    draw.rect(screen, colours, (int(mousePos[0] + abs(length) - toolSize/2), int(startingPos[1] - toolSize/2 + 1), toolSize, toolSize))
                                    draw.rect(screen, colours, (int(mousePos[0] + abs(length) - toolSize/2), int(startingPos[1] + abs(length) - toolSize/2), toolSize, toolSize))
                                draw.rect(screen, colours, (mousePos[0], startingPos[1], abs(length), abs(length)), toolSize)
                            else: # draws on quadriant 1 around the starting position
                                if toolSize > 1: # fills in the corners of the square
                                    draw.rect(screen, colours, (int(startingPos[0] - toolSize/2 + 1), int(startingPos[1] - toolSize/2), toolSize, toolSize))
                                    draw.rect(screen, colours, (int(startingPos[0] - toolSize/2 + 1), int(startingPos[1] - abs(length) - toolSize/2 + 1), toolSize, toolSize))
                                    draw.rect(screen, colours, (int(startingPos[0] + abs(length) - toolSize/2), int(startingPos[1] - toolSize/2), toolSize, toolSize))
                                    draw.rect(screen, colours, (int(startingPos[0] + abs(length) - toolSize/2), int(startingPos[1] - abs(length) - toolSize/2 + 1), toolSize, toolSize))
                                draw.rect(screen, colours, (startingPos[0], startingPos[1] - abs(length), length, abs(length)), toolSize)
                    else:
                        if toolSize > 1: # fills in the corners of the rectangle
                            draw.rect(screen, colours, (int(startingPos[0] - toolSize/2 + 1), int(startingPos[1] - toolSize/2 + 1), toolSize, toolSize))
                            draw.rect(screen, colours, (int(startingPos[0] - toolSize/2 + 1), int(mousePos[1] - toolSize/2), toolSize, toolSize))
                            draw.rect(screen, colours, (int(startingPos[0] + length - toolSize/2), int(startingPos[1] - toolSize/2 + 1), toolSize, toolSize))
                            draw.rect(screen, colours, (int(startingPos[0] + length - toolSize/2), int(mousePos[1] - toolSize/2), toolSize, toolSize))
                        draw.rect(screen, colours, (startingPos[0], startingPos[1], length, mousePos[1] - startingPos[1]), toolSize)
            elif toolOption == 7: # if ellipse option (7) is selected in toolOption
                if fillPolygon.value: # checks if fillPolygon has been selected by user and overrides toolSize
                    toolSize = 0
                if justPressed:
                    # stores starting position and starting screen at just pressed
                    startingPos = mousePos
                    canvasSurface = screen.copy()
                else:
                    screen.blit(canvasSurface, (0, 0))
                    try:
                        eclipseWidth = toolSize
                        if abs(startingPos[0] - mousePos[0]) // 2 <= toolSize: # sees if the width of the circle is beyond the limit of the circle and overrides the width with fill
                            eclipseWidth = 0
                        if key.get_pressed()[K_LSHIFT]:
                            if key.get_pressed()[K_LCTRL]: # draws a circle centred on the starting position
                                draw.circle(screen, colours, startingPos, abs(startingPos[0] - mousePos[0]), eclipseWidth)
                            else:
                                if (mousePos[0] > startingPos[0] and mousePos[1] > startingPos[1]) or (mousePos[0] < startingPos[0] and mousePos[1] < startingPos[1]): # draws on quadrant 2, 4 around the starting position 
                                    draw.circle(screen, colours, (startingPos[0] + (mousePos[0] - startingPos[0]) // 2, startingPos[1] + (mousePos[0] - startingPos[0]) // 2), abs(startingPos[0] - mousePos[0]) // 2, eclipseWidth)
                                else: # draws on quadrant 1 and 3 around the starting position
                                    draw.circle(screen, colours, (startingPos[0] + (mousePos[0] - startingPos[0]) // 2, startingPos[1] - (mousePos[0] - startingPos[0]) // 2), abs(startingPos[0] - mousePos[0]) // 2, eclipseWidth)
                        else:
                            if min(abs(mousePos[0] - startingPos[0]), abs(mousePos[1]- startingPos[1]))/2 < eclipseWidth: # sees if the width is beyond the ellipse limits and overrides to fill
                                eclipseWidth = 0
                            ellipseRect = Rect(mousePos[0], mousePos[1], startingPos[0] - mousePos[0], startingPos[1] - mousePos[1]) # rectangle of the ellipse
                            ellipseRect.normalize()
                            draw.ellipse(screen, colours, ellipseRect, eclipseWidth)
                    except:
                        pass
            elif toolOption == 8: # if eye dropper option (8) was selected in toolOption
                # gets colour and changes each value individually in colours (can't change all at once due to limitations with multiprocessing.Array)
                newColour = screen.get_at(mousePos)
                colours[0] = newColour[0]
                colours[1] = newColour[1]
                colours[2] = newColour[2]
            elif toolOption == 9 and justPressed: # if paint bucket option (9) was selected in toolOption
                pixelArray = PixelArray(screen) # creates a pixelArray of screen
                checkColour = pixelArray[mousePos] # gets the colour of the mousePos
                if not checkColour == screen.map_rgb(colours): # compares if the colour being replacing is equal to the replacing colour
                    # implements flood-fill algorithim
                    pixelQueue = Queue()
                    pixelQueue.put((mousePos[0], mousePos[1]))
                    screen.set_at(mousePos, colours)
                    while not pixelQueue.empty():
                        # checks surroundings if colour is the same as the colour being replacing and replacing with the replacing colour
                        storedPosition = pixelQueue.get()
                        if storedPosition[0] < 1279 and pixelArray[storedPosition[0] + 1, storedPosition[1]] == checkColour:
                            pixelQueue.put((storedPosition[0] + 1, storedPosition[1]))
                            screen.set_at((storedPosition[0] + 1, storedPosition[1]), colours)
                        if storedPosition[0] > 0 and pixelArray[storedPosition[0] - 1, storedPosition[1]] == checkColour:
                            pixelQueue.put((storedPosition[0] - 1, storedPosition[1]))
                            screen.set_at((storedPosition[0] - 1, storedPosition[1]), colours)
                        if storedPosition[1] < 719 and pixelArray[storedPosition[0], storedPosition[1] + 1] == checkColour:
                            pixelQueue.put((storedPosition[0], storedPosition[1] + 1))
                            screen.set_at((storedPosition[0], storedPosition[1] + 1), colours)
                        if storedPosition[1] > 0 and pixelArray[storedPosition[0], storedPosition[1] - 1] == checkColour:
                            pixelQueue.put((storedPosition[0], storedPosition[1] - 1))
                            screen.set_at((storedPosition[0], storedPosition[1] - 1), colours)
                del pixelArray # deletes pixelArray to unlock screen
            elif toolOption == 10 and justPressed: # if text (10) is selected in toolOption and just clicked left click
                while True:
                    try: # goes through and chooses a random tweet and see if it's possible to render to text (some limitation with emojis causes issues)
                        randomTweet = fonts[fontSelection.value][0].render(choice(tweets), True, colours)
                        if not toolSize == 64:
                            randomTweet = transform.scale(randomTweet, (int(randomTweet.get_width() * toolSize/64), int(randomTweet.get_height() * toolSize/64)))
                        screen.blit(randomTweet, (mousePos[0] - randomTweet.get_width()//2, mousePos[1] - randomTweet.get_height()//2))
                        break
                    except:
                        pass
            elif toolOption == 11: # if smudge (11) is selected in toolOption
                canvasSurface = screen.copy() # gets a copy of the surface
                smudgeRect = [mousePos[0] - toolSize, mousePos[1] - toolSize, toolSize * 2, toolSize * 2] # makes a rect of the area getting combined

                # finds and checks if the smudgeRect goes beyond the boundaries of the canvas and corrects smudgeRect to be within limits
                dif = [0, 0] # the difference between the x axis and y axis and the values of the smudgeRect that go beyond those axis
                if smudgeRect[0] < 0:
                    dif[0] = smudgeRect[0]
                    smudgeRect[0] = 0
                if smudgeRect[0] + smudgeRect[2] > 1280:
                    smudgeRect[2] -= smudgeRect[0] + toolSize * 2 - 1280
                if smudgeRect[1] < 0:
                    dif[1] = smudgeRect[1]
                    smudgeRect[1] = 0
                if smudgeRect[1] + smudgeRect[3] > 720:
                    smudgeRect[3] -= smudgeRect[1] + toolSize * 2 - 720
                smudge = canvasSurface.subsurface(smudgeRect) # gets region of the surface
                averageColour = transform.average_color(smudge) # retrieves the average of the region of the surface
                
                draw.circle(screen, averageColour, mousePos, toolSize)

                lastPos = [i for i in lastMousePos] # gets the last known position of the smudge
                circleDist = ((mousePos[0] - lastPos[0])**2 + (mousePos[1] - lastPos[1])**2)**0.5 # finds the distance between last known position with current position
                while circleDist > toolSize:
                    if circleDist/toolSize < 2: # see if last smudge is tangent to the current smudge position
                        smudgeRect = [(lastPos[0] + mousePos[0]) // 2 - toolSize, (lastPos[1] + mousePos[1]) // 2 - toolSize, toolSize*2, toolSize*2] # makes a rect of the area getting combined
                        # finds and checks if the smudgeRect goes beyond the boundaries of the canvas and corrects smudgeRect to be whithin limits
                        dif = [0, 0] # the difference between the x axis and y axis and the values of the smudgeRect that go beyond those axis
                        if smudgeRect[0] < 0:
                            dif[0] = smudgeRect[0]
                            smudgeRect[0] = 0
                        if smudgeRect[0] + smudgeRect[2] > 1280:
                            smudgeRect[2] -= smudgeRect[0] + toolSize * 2 - 1280
                        if smudgeRect[1] < 0:
                            dif[1] = smudgeRect[1]
                            smudgeRect[1] = 0
                        if smudgeRect[1] + smudgeRect[3] > 720:
                            smudgeRect[3] -= smudgeRect[1] + toolSize * 2 - 720
                        smudge = canvasSurface.subsurface(smudgeRect) # gets region of the surface
                        averageColour = transform.average_color(smudge) # retrieves the average of the region of the surface

                        draw.circle(screen, averageColour, (int(lastPos[0] + mousePos[0])//2, int(lastPos[1] + mousePos[1])//2), toolSize) # draws it at the midpoint of the last known position and current position
                        break
                    else:
                        ang = atan2(mousePos[1] - lastPos[1], mousePos[0] - lastPos[0]) # find angle between last known position and current position
                        # get next position of the smudge
                        lastPos[0] += cos(ang) * toolSize
                        lastPos[1] += sin(ang) * toolSize

                        smudgeRect = [int(lastPos[0]) - toolSize, int(lastPos[1]) - toolSize, toolSize*2, toolSize*2] # makes a rect of the area getting combined
                        # finds and checks if the smudgeRect goes beyond the boundaries of the canvas and corrects smudgeRect to be whithin limits
                        dif = [0, 0] # the difference between the x axis and y axis and the values of the smudgeRect that go beyond those axis
                        if smudgeRect[0] < 0:
                            dif[0] = smudgeRect[0]
                            smudgeRect[0] = 0
                        if smudgeRect[0] + smudgeRect[2] > 1280:
                            smudgeRect[2] -= smudgeRect[0] + toolSize * 2 - 1280
                        if smudgeRect[1] < 0:
                            dif[1] = smudgeRect[1]
                            smudgeRect[1] = 0
                        if smudgeRect[1] + smudgeRect[3] > 720:
                            smudgeRect[3] -= smudgeRect[1] + toolSize * 2 - 720
                        smudge = canvasSurface.subsurface(smudgeRect) # gets region of the surface
                        averageColour = transform.average_color(smudge) # retrieves the average of the region of the surface

                        draw.circle(screen, averageColour, (int(lastPos[0]), int(lastPos[1])), toolSize)
                        circleDist = ((mousePos[0] - lastPos[0]) ** 2 + (mousePos[1] - lastPos[1]) ** 2) ** 0.5 # finds the distance between last known position with current position
        
        if toolOption == 12: # if copy and paste option (12) is selected in toolOption
            if copyOption.value: # see if user is requesting to copy a region of screen
                if clicked[0]:
                    if justPressed:
                        # stores position of starting position and starting screen
                        startingPos = mousePos
                        canvasSurface = screen.copy()
                    else:
                        screen.blit(canvasSurface, (0, 0))
                        draw.rect(screen, 0, (startingPos[0], startingPos[1], mousePos[0] - startingPos[0], mousePos[1] - startingPos[1]), 1) # draws a rectangle for guide
                if justReleased:
                    screen.blit(canvasSurface, (0, 0))
                    copyRect = Rect(startingPos[0], startingPos[1], mousePos[0] - startingPos[0], mousePos[1] - startingPos[1]) # gets region desired
                    copyRect.normalize()
                    copySurface = canvasSurface.subsurface(copyRect) # copies region of screen desired
                    copyOption.value = False # resets copy to false
            elif not copyOption.value and justPressed: # if not copying (so pasting)
                screen.blit(copySurface, (mousePos[0] - copySurface.get_width()//2, mousePos[1] - copySurface.get_height()//2))

        if justPressedRight:
            if toolOption == 1: # see if right click is pressed with eraser (1)
                # clear the whole canvas
                clearCanvas.value = True
                undoRedo = undoRedo[:undoRedoPos+1]
                undoRedo.append([screen.copy(), backgroundImageOption.value])
                undoRedoPos += 1
            elif toolOption == 9: # see if right click is pressed with paintbucket (9)
                # fill the whole canvas
                screen.fill(colours)
                undoRedo = undoRedo[:undoRedoPos+1]
                undoRedo.append([screen.copy(), backgroundImageOption.value])
                undoRedoPos += 1
        
        if toolOption == 16: # if sticker (16) is selected by toolOption
            canvasSurface = undoRedo[undoRedoPos][0] # gets the most recent copy of the screen and constantly update
            screen.blit(canvasSurface, (0, 0))
            # gets selected sticker and transforms (flips, rotates, scales) to user's desire
            sticker = stickerImages[stickerOption.value]
            sticker = transform.scale(sticker, (int(sticker.get_width() * toolSize/25), int(sticker.get_height() * toolSize/25)))
            sticker = transform.flip(sticker, flipSticker.value, False)
            sticker = transform.rotate(sticker, stickerRotation.value)
            screen.blit(sticker, (mousePos[0] - sticker.get_width()//2, mousePos[1] - sticker.get_height()//2))
            stickerTool = True
            if clicked[2] and not movement[0] == 0: # if right click is being held down while moving left and right, increases or decreases rotation
                stickerRotation.value -= movement[0]/4
            # see if rotation is beyond limits and 'overflow' or 'underflow'
            if stickerRotation.value > 180:
                stickerRotation.value = stickerRotation.value - 180 * 2
            elif stickerRotation.value < -180:
                stickerRotation.value = stickerRotation.value + 180 * 2 

        # see if mouse was just released while some selected tools were selected to add updated screens to undoRedo
        if justReleased and (7 >= toolOption >= 0 or 11 >= toolOption >= 9 or (toolOption == 12 and not copyOption.value) or toolOption == 13 or toolOption == 16):
            undoRedo = undoRedo[:undoRedoPos+1]
            undoRedo.append([screen.copy(), backgroundImageOption.value])
            undoRedoPos += 1
            
        if undoRedoValue.value > 0: # see if toolbar called for undo redo
            if undoRedoValue.value == 1: # if undo (1) was called
                undoRedoPos -= 1 # move undoRedo position back 1
            else: # else if redo (2) was called
                undoRedoPos +=  1 # move undoRedo position forward 1
            if backgroundImageOption.value != undoRedo[undoRedoPos][1]: # reassigns the backgroundImage value if undos/redos to a previous canvas where backgroundImage was different
                backgroundImageOption.value = undoRedo[undoRedoPos][1]
                if len(backgroundImages) > backgroundImageOption.value >= 0: # checks if the backgroundImage is a valid value, sets to blankBackground if invalid
                    blankBackground = False
                else:
                    blankBackground = True
            screen.blit(undoRedo[undoRedoPos][0], (0, 0)) # blits current position
            undoRedoValue.value = 0 # resets

        ableToUndoRedo[0] = undoRedoPos > 0 # boolean seeing if undo is possible
        ableToUndoRedo[1] = len(undoRedo) - 1 > undoRedoPos # boolean seeing if redo is possible

        lastMousePos = mousePos # stores last known mouse position

        display.flip()

# toolbar screen containing all synced variables between processes
def toolbarScreen(toolbarOption, toolSizeVal, colours, fillPolygon, fontSelection, copyOption, clearCanvas, backgroundImageOption, ableToUndoRedo, undoRedoValue, saveLoadOption, stickerRotation, flipSticker, mousePosVal):
    # gets global list and variables
    global iconImage
    global config
    global maxToolSize
    global fonts
    global backgroundImages

    optionTextFont = font.Font(os.path.dirname(os.path.realpath(__file__)) + '\\source\\fonts\\Cairo.ttf', 16) # font for text in toolbar

    toolbarImgs = [] # images for toolbar

    # imports all images from toolbar folder into toolbarImgs
    for (dirpath, dirnames, filenames) in os.walk(os.path.dirname(os.path.realpath(__file__)) + "\\source\\imgs\\toolbar"):
        newFileNames = [int(i[:-4]) for i in filenames]
        newFileNames.sort()
        for i in newFileNames:
            toolbarImgs.append(image.load(os.path.dirname(os.path.realpath(__file__)) + '\\source\\imgs\\toolbar\\' + str(i) + '.png'))
        break

    optionRect = [] # dimensions for all the options in toolbar
    for i in range(0, 16):
        optionRect.append(Rect((i // 2) * 80 + 20, (i % 2) * 100 + 20, 60, 60))

    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (screen_width//2 - 640, screen_height//2+285) # positions toolbar centred in the screen, below the canvas
    screen = display.set_mode((1280, 200))
    display.set_caption("Toolbar Menu")
    display.set_icon(iconImage)

    running = True

    # background for extra options menu area
    extraOptionMenu = Surface((600, 160), SRCALPHA)
    draw.rect(extraOptionMenu, (255, 255, 255, 122), (0, 0, 600, 160))

    randomizeColours = False # bool for randomizing colours

    while running:
        # bool for if mouse was just clicked
        click = False
        for e in event.get():
            if e.type == QUIT:
                running = False
            if e.type == MOUSEBUTTONDOWN:
                click = True

        clicked = mouse.get_pressed()
        mousePos = mouse.get_pos()
    
        screen.blit(toolbarImgs[16], (0, 0))
        
        screen.blit(extraOptionMenu, (660, 20))

        # shows all the options for tools in each rectangle, and recolours based on if hovering over or selected
        for i in range(len(optionRect)):
            screen.blit(toolbarImgs[i], (optionRect[i][0] + 3, optionRect[i][1] + 3))
            if optionRect[i].collidepoint(mousePos) and not toolbarOption.value == i and clicked[0] and click:
                toolbarOption.value = i
                randomizeColours = False
            elif optionRect[i].collidepoint(mousePos):
                c = (255, 0, 0)
            else:
                c = (255, 255, 255)
            if toolbarOption.value == i:
                c = (0, 255, 0)
            draw.rect(screen, c, optionRect[i], 1)

        # shows mouse position of canvas on bottom right
        mousePosText = optionTextFont.render('Mouse Position: (%d, %d)' % (mousePosVal[0], mousePosVal[1]), True, (0, 0, 0))
        screen.blit(mousePosText, (1260 - mousePosText.get_width(), 190 - mousePosText.get_height()//2))

        if randomizeColours:
            colours[0] = randint(0, 255)
            colours[1] = randint(0, 255)
            colours[2] = randint(0, 255)

        if 7 >= toolbarOption.value >= 0: # if option selected are marker, eraser, pen, pencil, spray can, straight line, rectangle, or ellipse
            # tool size slider
            toolSizeRect = Rect(690, 60, 250, 20)
            draw.rect(screen, (255, 255, 255), toolSizeRect)
            draw.circle(screen, (255, 255, 255), (690, 70), 10)
            draw.circle(screen, (255, 255, 255), (940, 70), 10)
            
            # changing tool size on slider
            if (toolbarOption.value == 6 or toolbarOption.value == 7) and fillPolygon.value:
                draw.circle(screen, (122, 122, 122), (690 + int(250 * ((toolSizeVal.value - 1) / maxToolSize)), 70), 10)
            else:
                draw.circle(screen, (0, 0, 0), (690 + int(250 * ((toolSizeVal.value - 1) / maxToolSize)), 70), 10)
            if toolSizeRect.collidepoint(mousePos) and clicked[0] and not (toolbarOption.value >= 6 and fillPolygon.value):
                toolSizeVal.value = int((mousePos[0] - 690)/250 * maxToolSize) + 1
            
            # tool size text
            sizeOptionText = optionTextFont.render('Size:', True, (0, 0, 0))
            screen.blit(sizeOptionText, (680, 30))
            sizeValueText = optionTextFont.render(str(toolSizeVal.value), True, (0, 0, 0))
            screen.blit(sizeValueText, (960, 70 - sizeValueText.get_height()//2))

            if not toolbarOption.value == 1: # for all tools mentioned except eraser
                # allow randomizing colours which displays all the randomize colours (warning if you suffer from epilepsy)
                randomizeColoursText = optionTextFont.render('Randomize Colours:', True, (0, 0, 0))
                screen.blit(randomizeColoursText, (1080, 30))
                randomizeColoursRect = Rect(1080, 60, 100, 20)
                if randomizeColours:
                    draw.rect(screen, colours, randomizeColoursRect)
                else:
                    draw.rect(screen, (0, 0, 0), randomizeColoursRect)
                if randomizeColoursRect.collidepoint(mousePos) and click:
                    randomizeColours = not randomizeColours

                # selecting a custom colour
                selectColourText = optionTextFont.render('Select Colour:', True, (0, 0, 0))
                screen.blit(selectColourText, (680, 110))
                selectColourRect = Rect(680, 140, 100, 20)
                if randomizeColours:
                    draw.rect(screen, (122, 122, 122), selectColourRect)
                else:
                    draw.rect(screen, colours, selectColourRect)
                    if selectColourRect.collidepoint(mousePos) and click:
                        try:
                            newColour = askcolor()
                            colours[0] = int(newColour[0][0])
                            colours[1] = int(newColour[0][1])
                            colours[2] = int(newColour[0][2])
                        except:
                            pass
            
            if toolbarOption.value == 6 or toolbarOption.value == 7: # if tool selected is rectangle or ellipse
                # option to fill in polygons
                fillText = optionTextFont.render('Fill:', True, (0, 0, 0))
                screen.blit(fillText, (800, 110))
                fillRect = Rect(800, 140, 100, 20)
                if fillPolygon.value:
                    draw.rect(screen, (255, 255, 255), fillRect)
                else:
                    draw.rect(screen, 0, fillRect)
                if fillRect.collidepoint(mousePos) and click:
                    fillPolygon.value = not fillPolygon.value
        elif toolbarOption.value == 8: # eyedropper tool
            # displays selected colour
            colourSelectText = optionTextFont.render('Colour Selected:', True, (0, 0, 0))
            screen.blit(colourSelectText, (680, 30))
            draw.rect(screen, colours, (680, 60, 100, 20))
        elif toolbarOption.value == 9: # paintbucket tool
            # select a colour
            selectColourText = optionTextFont.render('Select Colour:', True, (0, 0, 0))
            screen.blit(selectColourText, (680, 30))
            selectColourRect = Rect(680, 60, 100, 20)
            if not randomizeColours:
                draw.rect(screen, colours, selectColourRect)
                if selectColourRect.collidepoint(mousePos) and click:
                    try:
                        newColour = askcolor()
                        colours[0] = int(newColour[0][0])
                        colours[1] = int(newColour[0][1])
                        colours[2] = int(newColour[0][2])
                    except:
                        pass
            else:
                draw.rect(screen, (122, 122, 122), selectColourRect)
            
            # create a rippling effect with randomized colours
            fillRandomColoursText = optionTextFont.render('Ripple Effect:', True, (0, 0, 0))
            screen.blit(fillRandomColoursText, (800, 30))
            fillRandomColoursRect = Rect(800, 60, 100, 20)
            if not randomizeColours:
                draw.rect(screen, 0, fillRandomColoursRect)
            else:
                draw.rect(screen, colours, fillRandomColoursRect)
            if fillRandomColoursRect.collidepoint(mousePos) and click:
                randomizeColours = not randomizeColours

            # get only a single random colour 
            aRandomColourText = optionTextFont.render('Get a Random Colour:', True, (0, 0, 0))
            screen.blit(aRandomColourText, (920, 30))
            aRandomColourRect = Rect(920, 60, 100, 20)
            if not randomizeColours:
                draw.rect(screen, 0, aRandomColourRect)
                if aRandomColourRect.collidepoint(mousePos) and click:
                    colours[0] = randint(0, 255)
                    colours[1] = randint(0, 255)
                    colours[2] = randint(0, 255)
            else:
                draw.rect(screen, (122, 122, 122), aRandomColourRect)
        elif toolbarOption.value == 10: # text tool
            # select text size
            toolSizeRect = Rect(690, 60, 250, 20)
            draw.rect(screen, (255, 255, 255), toolSizeRect)
            draw.circle(screen, (255, 255, 255), (690, 70), 10)
            draw.circle(screen, (255, 255, 255), (940, 70), 10)
            draw.circle(screen, 0, (690 + int(250 * ((toolSizeVal.value - 1) / maxToolSize)), 70), 10)
            if toolSizeRect.collidepoint(mousePos) and clicked[0]:
                toolSizeVal.value = int((mousePos[0] - 690)/250 * maxToolSize) + 1
            sizeOptionText = optionTextFont.render('Size:', True, (0, 0, 0))
            screen.blit(sizeOptionText, (680, 30))
            
            # show text size in text
            sizeValueText = optionTextFont.render(str(toolSizeVal.value), True, (0, 0, 0))
            screen.blit(sizeValueText, (960, 70 - sizeValueText.get_height()//2))
            
            # get a random colour
            randomizeColoursText = optionTextFont.render('Randomize Colour:', True, (0, 0, 0))
            screen.blit(randomizeColoursText, (800, 110))
            randomizeColoursRect = Rect(800, 140, 100, 20)
            if randomizeColours:
                draw.rect(screen, colours, randomizeColoursRect)
            else:
                draw.rect(screen, (0, 0, 0), randomizeColoursRect)
            if randomizeColoursRect.collidepoint(mousePos) and click:
                randomizeColours = not randomizeColours

            # select a custom colour
            selectColourText = optionTextFont.render('Select Colour:', True, (0, 0, 0))
            screen.blit(selectColourText, (680, 110))
            selectColourRect = Rect(680, 140, 100, 20)
            if randomizeColours:
                draw.rect(screen, (122, 122, 122), selectColourRect)
            else:
                draw.rect(screen, colours, selectColourRect)
                if selectColourRect.collidepoint(mousePos) and click:
                    try:
                        newColour = askcolor()
                        colours[0] = int(newColour[0][0])
                        colours[1] = int(newColour[0][1])
                        colours[2] = int(newColour[0][2])
                    except:
                        pass
            
            # select a custom font
            fontSelectText = optionTextFont.render('Select Font:', True, (0, 0, 0))
            screen.blit(fontSelectText, (1040, 30))
            for i in range(len(fonts)):
                fontSelectionRect = Rect(1040, 60 + 22 * i, 180, 20)
                if not i == fontSelection.value:
                    draw.rect(screen, (255, 255, 255), fontSelectionRect)
                    fontName = fonts[i][0].render(fonts[i][1], True, (0, 0, 0))
                    fontName = transform.scale(fontName, (int(fontName.get_width() * 1/4), int(fontName.get_height() * 1/4)))
                    screen.blit(fontName, (1050, 70 + 22 * i - fontName.get_height()//2))
                    if fontSelectionRect.collidepoint(mousePos) and click:
                        fontSelection.value = i
                else:
                    draw.rect(screen, 0, fontSelectionRect)
                    fontName = fonts[i][0].render(fonts[i][1], True, (255, 255, 255))
                    fontName = transform.scale(fontName, (int(fontName.get_width() * 1/4), int(fontName.get_height() * 1/4)))
                    screen.blit(fontName, (1050, 70 + 22 * i - fontName.get_height()//2))
        elif toolbarOption.value == 11: # blurring tool
            # tool size selector
            toolSizeRect = Rect(690, 60, 250, 20)
            draw.rect(screen, (255, 255, 255), toolSizeRect)
            draw.circle(screen, (255, 255, 255), (690, 70), 10)
            draw.circle(screen, (255, 255, 255), (940, 70), 10)
            draw.circle(screen, 0, (690 + int(250 * ((toolSizeVal.value - 1) / maxToolSize)), 70), 10)
            if toolSizeRect.collidepoint(mousePos) and clicked[0]:
                toolSizeVal.value = int((mousePos[0] - 690)/250 * maxToolSize) + 1
            sizeOptionText = optionTextFont.render('Size:', True, (0, 0, 0))
            screen.blit(sizeOptionText, (680, 30))
            
            # tool size text
            sizeValueText = optionTextFont.render(str(toolSizeVal.value), True, (0, 0, 0))
            screen.blit(sizeValueText, (960, 70 - sizeValueText.get_height()//2))
        elif toolbarOption.value == 12: # copy and past tool
            # copy button to copy a selected region
            copyText = optionTextFont.render('Copy:', True, (0, 0, 0))
            screen.blit(copyText, (680, 30))
            copyRect = Rect(680, 60, 100, 20)
            if copyOption.value:
                draw.rect(screen, (255, 255, 255), copyRect)
            else:
                draw.rect(screen, 0, copyRect)
                if copyRect.collidepoint(mousePos) and click:
                    copyOption.value = True
        elif toolbarOption.value == 13: # background select
            # gets all the backgrounds and displays them, clicking results in background changing and option being greyed out
            translucentBox = Surface((106, 60), SRCALPHA)
            draw.rect(translucentBox, (0, 0, 0, 200), (0, 0, 106, 60))
            for i in range(len(backgroundImages)):
                displayedBackgroundImage = Surface((106, 60), SRCALPHA)
                displayedBackgroundImage.blit(transform.scale(backgroundImages[i], (106, 60)), (0, 0))
                if backgroundImageOption.value == i:
                    displayedBackgroundImage.blit(translucentBox, (0, 0))
                screen.blit(displayedBackgroundImage, (int(695 + 106 * (i % 5)), int(40 + (i // 5) * 60)))
                backgroundImageRect = Rect(int(695 + 106 * (i % 5)), int(40 + (i // 5) * 60), 106, 60)
                if not backgroundImageOption.value == i and backgroundImageRect.collidepoint(mousePos) and click:
                    backgroundImageOption.value = i
                    clearCanvas.value = True
            blankBackgroundRect = Rect(801, 100, 106, 60)
            if not len(backgroundImages) > backgroundImageOption.value >= 0:
                draw.rect(screen, 0, blankBackgroundRect)
            else:
                draw.rect(screen, (255, 255, 255), blankBackgroundRect)
            if blankBackgroundRect.collidepoint(mousePos) and click and not len(backgroundImages) > backgroundImageOption.value >= 0:
                backgroundImageOption.value = -1
                clearCanvas.value = True
        elif toolbarOption.value == 14: # undo redo
            # undo button and text
            undoText = optionTextFont.render('Undo:', True, (0, 0, 0))
            screen.blit(undoText, (680, 30))
            undoRect = Rect(680, 60, 100, 20)
            if ableToUndoRedo[0]:
                draw.rect(screen, 0, undoRect)
                if undoRect.collidepoint(mousePos) and click:
                    undoRedoValue.value = 1
            else:
                draw.rect(screen, (122, 122, 122), undoRect)

            # redo button and text
            redoText = optionTextFont.render('Redo:', True, (0, 0, 0))
            screen.blit(redoText, (800, 30))
            redoRect = Rect(800, 60, 100, 20)
            if ableToUndoRedo[1]:
                draw.rect(screen, 0, redoRect)
                if redoRect.collidepoint(mousePos) and click:
                    undoRedoValue.value = 2
            else:
                draw.rect(screen, (122, 122, 122), redoRect)
        elif toolbarOption.value == 15: # saving and loading option
            # saving button and text
            saveText = optionTextFont.render('Save:', True, (0, 0, 0))
            screen.blit(saveText, (680, 30))
            saveRect = Rect(680, 60, 100, 20)
            draw.rect(screen, 0, saveRect)
            if saveRect.collidepoint(mousePos) and click:
                saveLoadOption.value = 1

            # loading button and text
            loadText = optionTextFont.render('Load:', True, (0, 0, 0))
            screen.blit(loadText, (800, 30))
            loadRect = Rect(800, 60, 100, 20)
            draw.rect(screen, 0, loadRect)
            if loadRect.collidepoint(mousePos) and click:
                saveLoadOption.value = 2
        elif toolbarOption.value == 16: # sticker option
            # tool size slider
            toolSizeRect = Rect(690, 60, 250, 20)
            draw.rect(screen, (255, 255, 255), toolSizeRect)
            draw.circle(screen, (255, 255, 255), (690, 70), 10)
            draw.circle(screen, (255, 255, 255), (940, 70), 10)
            draw.circle(screen, (0, 0, 0), (690 + int(250 * ((toolSizeVal.value - 1) / maxToolSize)), 70), 10)
            if toolSizeRect.collidepoint(mousePos) and clicked[0]:
                toolSizeVal.value = int((mousePos[0] - 690)/250 * maxToolSize) + 1
            sizeOptionText = optionTextFont.render('Size:', True, (0, 0, 0))
            screen.blit(sizeOptionText, (680, 30))
            
            # tool size text
            sizeValueText = optionTextFont.render(str(toolSizeVal.value), True, (0, 0, 0))
            screen.blit(sizeValueText, (960, 70 - sizeValueText.get_height()//2))

            # rotation slider
            rotationRect = Rect(690, 140, 250, 20)
            draw.rect(screen, (255, 255, 255), rotationRect)
            draw.circle(screen, (255, 255, 255), (690, 150), 10)
            draw.circle(screen, (255, 255, 255), (940, 150), 10)
            draw.circle(screen, (0, 0, 0), (815 + int(125 *  stickerRotation.value / 180), 150), 10)
            if rotationRect.collidepoint(mousePos) and clicked[0]:
                stickerRotation.value = int((mousePos[0] - 815)/125 * 180)
            rotationText = optionTextFont.render('Rotation:', True, (0, 0, 0))
            screen.blit(rotationText, (680, 110))
            
            # rotation text
            rotationValueText = optionTextFont.render(str(stickerRotation.value), True, (0, 0, 0))
            screen.blit(rotationValueText, (960, 140 - sizeValueText.get_height()//2))

            # flip button and text
            flipText = optionTextFont.render('Flip:', True, (0, 0, 0))
            screen.blit(flipText, (1080, 30))
            flipRect = Rect(1080, 60, 100, 20)
            if flipSticker.value:
                draw.rect(screen, (255, 255, 255), flipRect)
            else:
                draw.rect(screen, 0, flipRect)
            if flipRect.collidepoint(mousePos) and click:
                flipSticker.value = not flipSticker.value
        
        display.flip()

# sticker menu with parameters including multiprocessing variables for cross-process communication
def sticker(toolbarOption, stickerOption):
    # importing global variables and lists
    global iconImage
    global stickerImages
    global config

    stickerData = [] # data about the stickers
    # import all the stickers from stickerImage to stickerData
    for i in range(len(stickerImages)):
        tempImage = stickerImages[i]
        displayedSticker = transform.scale(tempImage, (150, int(tempImage.get_height() * (150 / tempImage.get_width()))))
        height = displayedSticker.get_height()
        if i == 0:
            top = 25
        else:
            top = stickerData[i-1][1] + stickerData[i-1][2] + 25
        stickerData.append([displayedSticker, top, height])
    
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (screen_width // 2 + 640, screen_height // 2 - 485) # positions menu to the right of the canvas
    screen = display.set_mode((200, 720))
    display.set_caption("Sticker Menu")
    display.set_icon(iconImage)

    background = image.load(os.path.dirname(os.path.realpath(__file__)) + '\\source\\imgs\\stickerBackground.png')

    running = True
    
    offset = 0 # scrolling offset from starting position

    notClickedRectangle = Surface((10, 240), SRCALPHA) # scrollbar thumb (not clicked)
    draw.rect(notClickedRectangle, (255, 255, 255, 122), (0, 0, 10, 240))

    while running:
        # bool for if mouse has just been pressed down
        justPressed = False
        for e in event.get():
            if e.type == QUIT:
                running = False
            if e.type == MOUSEBUTTONDOWN:
                if e.button == 1:
                    justPressed = True
                # scrolling for the menu to show all stickers
                if e.button == 4 and offset - 10 >= 0:
                    offset -= 10
                elif e.button == 4 and offset - 10 < 0:
                    offset = 0
                if e.button == 5 and offset + 10 < 1025:
                    offset += 10
                elif e.button == 5 and offset + 10 >= 1025:
                    offset = 1024

        movement = mouse.get_rel()
        mousePos = mouse.get_pos()

        clicked = mouse.get_pressed()

        # makes toolbarOption to sticker option if not selected already
        if toolbarOption.value != 16 and clicked[0]:
            toolbarOption.value = 16

        scrollbarThumb = Rect(190, int((offset/1025) * 480), 10, 240)

        # if scrollbar thumb has pressed
        if clicked[0] and offset/1025 <= 1 and scrollbarThumb.collidepoint(mousePos):
            # moves based on the position of the thumb and changes offset
            if justPressed:
                distToTop = mousePos[1] - int((offset/1025) * 480)
            if (mousePos[1] - distToTop)/480 <= 1 and (mousePos[1] - distToTop)/480 >= 0:
                offset = (mousePos[1] - distToTop)/480 * 1025
        screen.blit(background, (0, 0 - offset))

        # draws scrollbarThumb is clicked or not
        if clicked[0] and scrollbarThumb.collidepoint(mousePos):
            draw.rect(screen, (255, 255, 255), (190, int((offset/1025) * 480), 10, 240))
        else:
            screen.blit(notClickedRectangle, (190, int((offset/1025) * 480)))

        # goes through every sticker and only blits if any part of the specified sticker is somewhat visible on the screen
        for i in range(len(stickerData)):
            top = stickerData[i][1] - offset
            bottom = top + stickerData[i][2]
            if top < 720 and bottom >= 0:
                if toolbarOption.value == 16 and stickerOption.value == i: # adds a grey background to the sticker image if that sticker has been selected
                    selected = Surface((150, stickerData[i][2]), SRCALPHA)
                    selected.fill((122, 122, 122, 122))
                    screen.blit(selected, (25, top))
                screen.blit(stickerData[i][0], (25, top))
                if Rect(25, top, 150, stickerData[i][2]).collidepoint(mousePos) and clicked[0]: # changes sticker option to selected sticker
                    stickerOption.value = i


        
        display.flip()

if __name__ == "__main__": # setup area for processes
    colours = multiprocessing.Array('i', [0, 0, 0]) # Array the canvas process and the toolbar process that stores the RGB values of the colour selected

    mousePosVal = multiprocessing.Array('i', [0, 0]) # Gets the mouse position of the mouse only on the canvas
    
    ableToUndoRedo = multiprocessing.Array(c_bool, [False, False]) # first option is for undo, second option is for redo

    undoRedoValue = multiprocessing.Value('i', 0) # 0 means nothing, 1 means undo, 2 means redo

    toolbarOption = multiprocessing.Value('i', 0) # The toolbar option for the tool selected

    stickerOption = multiprocessing.Value('i', 0) # Sticker chosen by the user

    saveLoadOption = multiprocessing.Value('i', 0) # 0 means nothing, 1 means save, 2 means load

    copyOption = multiprocessing.Value(c_bool, True) # True means you can select a region to copy, False means clicking results in a paste
    
    clearCanvas = multiprocessing.Value(c_bool, True) # True means the canvas clears and restarts, False means nothing

    flipSticker = multiprocessing.Value(c_bool, False) # bool for if sticker is flipped horizontally

    fontSelection = multiprocessing.Value('i', 0) # which font has been selected (int option in the font list)

    fillPolygon = multiprocessing.Value(c_bool, False) # if the polygons will be filled in

    stickerRotation = multiprocessing.Value('f', 0) # the rotation of the stickers (in degrees)

    if config['useDefaults']: # checks if the configs say to use default settings for backgroundImage, sets it blank as default
        backgroundImageOption = multiprocessing.Value('i', -1)
    else:
        backgroundImageOption = multiprocessing.Value('i', config['config']['startupBackground'])

    toolSizeVal = multiprocessing.Value('i', 1) # size of the tools

    # makes and starts all the processes of the different windows, with arguments of all the synchronized variables and arrays
    mainScreenP = multiprocessing.Process(target=mainScreen, args=(toolbarOption, backgroundImageOption, toolSizeVal, colours, stickerOption, fillPolygon, fontSelection, copyOption, clearCanvas, ableToUndoRedo, undoRedoValue, saveLoadOption, stickerRotation, flipSticker, mousePosVal)) # main canvas proccess
    toolbarScreenP = multiprocessing.Process(target=toolbarScreen, args=(toolbarOption, toolSizeVal, colours, fillPolygon, fontSelection, copyOption, clearCanvas, backgroundImageOption, ableToUndoRedo, undoRedoValue, saveLoadOption, stickerRotation, flipSticker, mousePosVal)) # toolbar processes
    stickerP = multiprocessing.Process(target=sticker, args=(toolbarOption, stickerOption)) # sticker menu process
    mainScreenP.start()
    toolbarScreenP.start()
    stickerP.start()
    while True:
        # constantly checks if anyone of the windows has been closed and closes all windows and current program
        if not mainScreenP.is_alive() or not toolbarScreenP.is_alive() or not stickerP.is_alive():
            mainScreenP.terminate()
            toolbarScreenP.terminate()
            stickerP.terminate()
            break