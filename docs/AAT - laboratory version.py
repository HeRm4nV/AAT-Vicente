#!/usr/bin/env python2.7
# coding=utf-8

"""
tested in Python 2.7.13
"""
import csv, pygame , random, sys, os, cv2, wave
from pygame.locals import FULLSCREEN, USEREVENT, KEYDOWN, KEYUP, K_SPACE, K_RETURN, K_ESCAPE, QUIT, Color, K_c
from os.path import isfile, join
from random import randint, shuffle, choice
from time import gmtime, strftime, time

## Configurations:
FullScreenShow = True # Pantalla completa automáticamente al iniciar el experimento
keys = [pygame.K_SPACE] # Teclas elegidas para mano derecha o izquierda
test_name = "AAT"
date_name = strftime("%Y-%m-%d_%H-%M-%S", gmtime())

## Image Loading

#attractive_images_list = {"rect": ["media\\images\\A\\" + f for f in os.listdir("media\\images\\A") if isfile(join("media\\images\\A", f))], "circ": ["media\\images\\A\\" + f for f in os.listdir("media\\images\\A") if isfile(join("media\\images\\A", f))]}
#neutral_images_list = {"rect": ["media\\images\\N\\" + f for f in os.listdir("media\\images\\N") if isfile(join("media\\images\\N", f))], "circ": ["media\\images\\N\\" + f for f in os.listdir("media\\images\\N") if isfile(join("media\\images\\N", f))]}
#trial_images_list = {"rect": ["media\\images\\T\\" + f for f in os.listdir("media\\images\\T") if isfile(join("media\\images\\T", f))], "circ": ["media\\images\\T\\" + f for f in os.listdir("media\\images\\T") if isfile(join("media\\images\\T", f))]}

circ = pygame.image.load("media\\images\\fixationstims\\circ.png")
rect = pygame.image.load("media\\images\\fixationstims\\rect.png")

attractive_images_list = ["media\\images\\A\\" + f for f in os.listdir("media\\images\\A") if isfile(join("media\\images\\A", f))]
neutral_images_list = ["media\\images\\N\\" + f for f in os.listdir("media\\images\\N") if isfile(join("media\\images\\N", f))]
trial_images_list = [["media\\images\\T\\" + f, choice(["circ", "rect"])] for f in os.listdir("media\\images\\T") if isfile(join("media\\images\\T", f))]

# count of image repetitions
repetition_list = [0]*120

shuffle(attractive_images_list)
#shuffle(attractive_images_list["circ"])
shuffle(neutral_images_list)
#shuffle(neutral_images_list["circ"])
shuffle(trial_images_list)
#shuffle(trial_images_list["circ"])

connected_joystick = False
base_size = 350

## Port address and triggers
lpt_address     = 0xD100
trigger_latency = 5
start_trigger   = 254
stop_trigger    = 255

## Onscreen instructions
def select_slide(slide_name, between_type = None, AAT_variables = {"block_number": 0, "geometry": "circle", "stick": "right", "practice": True}):
    
    if slide_name == "exposure":
        slide_name = slide_name + "_" + between_type
    
    basic_slides = {
        'welcome': [
            u"Bienvenido/a, a este experimento!!!",
            " ",
            u"Se te indicará paso a paso que hacer.",
            u"Ahora pon atención al video.",
            " ",
            u"Para comenzar presiona la barra espaciadora."
            ],
        'intro_block_1': [
            u"Ahora, aplica las instrucciones del vídeo a las imágenes que aparecerán a continuación.",
            u"Las imágenes cambiarán automáticamente.",
            " ",
            u"Para comenzar presiona la barra espaciadora."
            ],
        'intro_block_3': [
            u"Ahora comenzará la segunda mitad del experimento",
            " ",
            u"Pon atención al video.",
            " ",
            u"Puedes descansar unos segundos, cuando te sientas",
            u"listo para comenzar presiona la barra espaciadora."
            ],
        'Instructions_AAT': [
            u"Instrucciones" + ("" if AAT_variables["practice"] else (" " + str(AAT_variables["block_number"]))) + "",
            " ",
            u"Esta es una tarea de percepción visual, en la cual se presentarán imágenes",
            u"de manera sucesiva. Estas en su centro tendrán un cuadrado o un círculo azul.",
            " ",
            u"La tarea consiste en que cuando un ítem se presente con un " + ("CIRCULO" if AAT_variables["geometry"] == "circ" else "CUADRADO") + " debes ACERCAR",
            u"la imagen hacia ti, y cuando sea un " + ("CUADRADO" if AAT_variables["geometry"] == "circ" else "CIRCULO") + " debes ALEJAR la imagen de ti.",
            " ",
            u"Usa la palanca " + ("DERECHA" if AAT_variables["stick"] == "right" else "IZQUIERDA") + " para acercar o alejar la imagen.",
            " ",
            u"Al aparecer la imagen por favor responde lo más rápido y preciso posible.",
            " ",
            u"Para comenzar " + ("la fase de prueba " if AAT_variables["practice"] else "") + "presiona la barra espaciadora."
            ],
        'exposure_mindful': [
            u"Recuerda que tus pensamientos sobre estas imágenes",
            u"son meros eventos mentales que vienen y se van."
            ],
        'exposure_control': [
            u"Recuerda mirar las imágenes atentamente"
            ],
        'wait': [
            "+"
            ],
        'farewell': [
            u"El Experimento ha terminado.",
            "",
            u"Muchas gracias por su colaboración!!"
            ]
        }

    selected_slide = basic_slides[slide_name]
    
    return (selected_slide)

## EEG Functions
def init_lpt(address):
    """Creates and tests a parallell port"""
    try:
        from ctypes import windll
        global io
        io = windll.dlportio  # requires dlportio.dll !!!
        print('Parallel port opened')
    except:
        pass
        print("Oops!", sys.exc_info(), "occurred.")
        print('The parallel port couldn\'t be opened')
    try:
        io.DlPortWritePortUchar(address, 0)
        print('Parallel port set to zero')
    except:
        pass
        print('Failed to send initial zero trigger!')

def send_trigger(trigger, address, latency):
    """Sends a trigger to the parallell port"""
    try:
        io.DlPortWritePortUchar(address, trigger)  # Send trigger
        pygame.time.delay(latency)  # Keep trigger pulse for some ms
        io.DlPortWritePortUchar(address, 0)  # Get back to zero after some ms
        print('Trigger ' + str(trigger) + ' sent')
    except:
        pass
        print('Failed to send trigger ' + str(trigger))

def sleepy_trigger(trigger, address, latency):
    send_trigger(trigger, address, latency)
    pygame.time.wait(100)

## Text Functions
def setfonts():
    """Sets font parameters"""
    global bigchar, char, charnext
    pygame.font.init()
    font     = join('media', 'Arial_Rounded_MT_Bold.ttf')
    bigchar  = pygame.font.Font(font, 96)
    char     = pygame.font.Font(font, 32)
    charnext = pygame.font.Font(font, 24)

def render_textrect(string, font, rect, text_color, background_color, justification=1):
    """Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapping as necessary. The text
    will be anti-aliased.

    Takes the following arguments:

    string - the text you wish to render. \n begins a new line.
    font - a Font object
    rect - a rectstyle giving the size of the surface requested.
    text_color - a three-byte tuple of the rgb value of the
                 text color. ex (0, 0, 0) = BLACK
    background_color - a three-byte tuple of the rgb value of the surface.
    justification - 0 left-justified
                    1 (default) horizontally centered
                    2 right-justified

    Returns the following values:

    Success - a surface object with the text rendered onto it.
    Failure - raises a TextRectException if the text won't fit onto the surface.
    """

    import pygame

    final_lines = []

    requested_lines = string.splitlines()

    # Create a series of lines that will fit on the provided
    # rectangle.

    for requested_line in requested_lines:
        if font.size(requested_line)[0] > rect.width:
            words = requested_line.split(' ')
            # if any of our words are too long to fit, return.
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise(TextRectException, "The word " + word + " is too long to fit in the rect passed.")
            # Start a new line
            accumulated_line = ""
            for word in words:
                test_line = accumulated_line + word + " "
                # Build the line while the words fit.
                if font.size(test_line)[0] < rect.width:
                    accumulated_line = test_line
                else:
                    final_lines.append(accumulated_line)
                    accumulated_line = word + " "
            final_lines.append(accumulated_line)
        else:
            final_lines.append(requested_line)

    # Let's try to write the text out on the surface.

    surface = pygame.Surface(rect.size)
    surface.fill(background_color)

    accumulated_height = 0
    for line in final_lines:
        if accumulated_height + font.size(line)[1] >= rect.height:
            raise(TextRectException, "Once word-wrapped, the text string was too tall to fit in the rect.")
        if line != "":
            tempsurface = font.render(line, 1, text_color)
            if justification == 0:
                surface.blit(tempsurface, (0, accumulated_height))
            elif justification == 1:
                surface.blit(tempsurface, ((rect.width - tempsurface.get_width()) / 2, accumulated_height))
            elif justification == 2:
                surface.blit(tempsurface, (rect.width - tempsurface.get_width(), accumulated_height))
            else:
                raise(TextRectException, "Invalid justification argument: " + str(justification))
        accumulated_height += font.size(line)[1]

    return final_lines, surface

def paragraph_old(text, just_info, key, rise = 0, color = None):
    """Organizes a text into a paragraph"""
    screen.fill(background)
    row = center[1] - 20 * len(text)

    if color == None:
        color = char_color

    for line in text:
        phrasebox = pygame.Rect((resolution[0]/8, rise + 0 + row, resolution[0]*6/8, resolution[1]*5/8))
        final_lines, phrase = render_textrect(line.strip(u'\u200b'), char,  pygame.Rect((resolution[0]/8, resolution[1]/8, resolution[0]*6/8, resolution[1]*6/8)), color, background)
        screen.blit(phrase, phrasebox)
        row += 40 * len(final_lines)
    if just_info:
        if key == K_SPACE:
            foot = "Para continuar presione la BARRA ESPACIADORA..."
        elif key == K_RETURN:
            foot = "Para continuar presione la tecla ENTER..."
    else:
        foot = ""
    nextpage = charnext.render(foot, True, charnext_color)
    nextbox  = nextpage.get_rect(left = 15, bottom = resolution[1] - 15)
    screen.blit(nextpage, nextbox)
    pygame.display.flip()

def paragraph(text, key = None, no_foot = False, color = None):
    """Organizes a text into a paragraph"""
    screen.fill(background)
    row = center[1] - 20 * len(text)

    if color == None:
        color = char_color
    
    for line in text:
        phrase = char.render(line, True, char_color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 40
    if key != None:
        if key == K_SPACE:
            foot = u"Para continuar presione la BARRA ESPACIADORA..."
        elif key == K_RETURN:
            foot = u"Para continuar presione la tecla ENTER..."
    else:
        foot = u"Responda con la fila superior de teclas de numéricas"
    if no_foot:
        foot = ""
    nextpage = charnext.render(foot, True, charnext_color)
    nextbox = nextpage.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(nextpage, nextbox)
    pygame.display.flip()

def slide(text, info, key, limit_time = 0):
    """Organizes a paragraph into a slide"""
    paragraph(text, info, key)
    wait_time = wait(key, limit_time)
    return wait_time

## Program Functions
def init():
    """Init display and others"""
    setfonts()
    global screen, resolution, center, background, char_color, charnext_color, fix, fixbox, fix_think, fixbox_think, izq, der, quest, questbox
    pygame.init() # soluciona el error de inicializacion de pygame.time
    pygame.display.init()
    pygame.display.set_caption(test_name)
    pygame.mouse.set_visible(False)
    if FullScreenShow:
        resolution = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        screen     = pygame.display.set_mode(resolution, FULLSCREEN)
    else:
        try:
            resolution = pygame.display.list_modes()[3]
        except:
            resolution = (1280, 720)
        screen     = pygame.display.set_mode(resolution)
    center = (int(resolution[0] / 2), int(resolution[1] / 2))
    izq = (int(resolution[0] / 8), (int(resolution[1] / 8)*7))
    der = ((int(resolution[0] / 8)*7), (int(resolution[1] / 8)*7))
    background     = Color('lightgray')
    char_color     = Color('black')
    charnext_color = Color('lightgray')
    fix            = char.render('+', True, char_color)
    fixbox         = fix.get_rect(centerx = center[0], centery = center[1])
    fix_think      = bigchar.render('+', True, Color('red'))
    fixbox_think   = fix.get_rect(centerx = center[0], centery = center[1])
    quest          = bigchar.render('?', True, char_color)
    questbox       = quest.get_rect(centerx = center[0], centery = center[1])
    screen.fill(background)
    pygame.display.flip()

def blackscreen(blacktime = 0):
    """Erases the screen"""
    screen.fill(background)
    pygame.display.flip()
    pygame.time.delay(blacktime)

def ends():
    """Closes the show"""
    blackscreen()
    dot    = char.render('.', True, char_color)
    dotbox = dot.get_rect(left = 15, bottom = resolution[1] - 15)
    screen.blit(dot, dotbox)
    pygame.display.flip()
    while True:
        for evento in pygame.event.get():
            if evento.type == KEYUP and evento.key == K_ESCAPE:
                pygame_exit()

def pygame_exit():
    pygame.quit()
    sys.exit()

def wait(key, limit_time):
    """Hold a bit"""

    TIME_OUT_WAIT = USEREVENT + 1
    if limit_time != 0:
        pygame.time.set_timer(TIME_OUT_WAIT, limit_time)

    tw = pygame.time.get_ticks()

    switch = True
    while switch:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame_exit()
            elif event.type == KEYUP:
                if event.key == key:
                    switch = False
            elif event.type == TIME_OUT_WAIT and limit_time != 0:
                switch = False
                pygame.time.set_timer(TIME_OUT_WAIT, 0)

    pygame.event.clear()                    # CLEAR EVENTS
                
    return (pygame.time.get_ticks() - tw)

def reconnect_joystick():
    done = False
    pygame.joystick.quit()
    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            done = True
            print("Joystick conectado")
            joystick = pygame.joystick.Joystick(pygame.joystick.get_count() - 1)
            joystick.init()
            return(joystick)
        else:
            pygame.joystick.quit()

def image_in_center(picture):
    center = [int(resolution[0] / 2), int(resolution[1] / 2)]
    return [x - picture.get_size()[count]/2 for count, x in enumerate(center)]

def show_image(image, scale, stimulus = None):
    screen.fill(background)
    picture = pygame.image.load(image)
    picture = pygame.transform.scale(picture, [int(scale[0]), int(scale[1])])
    screen.blit(picture,image_in_center(picture))

    if stimulus != None:
        if stimulus == "rect":
            stimulus = rect
        else:
            stimulus = circ
        screen.blit(stimulus,image_in_center(stimulus))
        
    pygame.display.flip()

def zoom(image = None, factor = 1, time = 0, iteration_speed = 10):
    global resolution

    # time in sec to ms
    time = time*1000
    max_value = int(resolution[1])*1.2

    # set the scaling to max_value
    if time != 0 and factor**(time/iteration_speed)*base_size > max_value:
        factor = round((max_value/base_size)**(1/(time/iteration_speed)), 3)

    done = False
    zoom_event = USEREVENT + 1
    end_zoom_event = USEREVENT + 2

    picture = pygame.image.load(image)
    size = [base_size, base_size]

    pygame.time.set_timer(zoom_event, iteration_speed)
    pygame.time.set_timer(end_zoom_event, int(time))

    zoomed = False
    
    while not done:
        for event in pygame.event.get():
            if event.type == end_zoom_event and zoomed:
                done = True
                break
            if event.type == zoom_event:
                zoomed = True
                #TODO: Min size
                size = [size[0]*factor, size[1]*factor]
                show_image(image, size)

    pygame.event.clear()                    # CLEAR EVENTS

def wait_control_answer(image, joystick, axis_number):

    #image_change = USEREVENT + 1
    #pygame.time.set_timer(image_change, 3000)

    tw = pygame.time.get_ticks()

    zoom_activate = False
    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()

            elif event.type == KEYUP and event.key == K_c:
                done=True
                pygame.event.clear()        # CLEAR EVENTS
                return(False)
                
            elif event.type == pygame.JOYAXISMOTION:
                axis = round(joystick.get_axis(axis_number), 2)
                #axis = round(event.value, 2)
                if axis > 0.75 and event.axis == axis_number:
                    zoom_activate = True
                    zoom_mode = "in"
                    done = True
                    break
                elif axis < -0.75 and event.axis == axis_number:
                    zoom_activate = True
                    zoom_mode = "out"
                    done = True
                    break

    pygame.event.clear()                    # CLEAR EVENTS
    
    if (zoom_activate):
        sleepy_trigger(230 + (0 if zoom_mode == "in" else 1) + (2 if axis_number == 1 else 0), lpt_address, trigger_latency) # user answer
        if zoom_mode == "out":
            zoom(image = image, factor = 0.96, time = 0.6, iteration_speed = 10)
        elif zoom_mode == "in":
            zoom(image = image, factor = 1.11, time = 0.6, iteration_speed = 16)
    
    pygame.event.clear()                    # CLEAR EVENTS
    return(zoom_mode)

def show_images(image_list, condition):
    global attractive_images_list, neutral_images_list
    
    phase_change = USEREVENT + 1

    shuffle(image_list)

    pygame.time.set_timer(phase_change, 500)

    done = False
    count = 0

    screen.fill(background)
    pygame.display.flip()

    actual_phase = 1

    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()

            elif event.type == KEYUP and event.key == K_c:
                done=True

            elif event.type == phase_change:
                if actual_phase == 1:
                    show_image(image_list[count], (base_size, base_size))
                    sleepy_trigger(240 + (0 if condition == "mindful" else 1) + (4 if image_list[count].split('\\')[2] == "N" else 0), lpt_address, trigger_latency) # Exposure image trigger first
                    sleepy_trigger(int(image_list[count].split('\\')[3].split("_")[0]), lpt_address, trigger_latency) # image ID
                    pygame.time.set_timer(phase_change, 3500-200)
                    actual_phase = 2
                elif actual_phase == 2:
                    screen.fill(background)
                    pygame.display.flip()
                    pygame.time.set_timer(phase_change, 500)
                    actual_phase = 3
                elif actual_phase == 3:
                    show_image(image_list[count], (base_size, base_size))
                    sleepy_trigger(240 + (2 if condition == "mindful" else 3) + (4 if image_list[count].split('\\')[2] == "N" else 0), lpt_address, trigger_latency) # Exposure image trigger second
                    pygame.time.set_timer(phase_change, 500-100)
                    actual_phase = 4
                elif actual_phase == 4:
                    screen.fill(background)
                    screen.blit(fix, fixbox)
                    pygame.display.update(fixbox)
                    pygame.display.flip()
                    sleepy_trigger(150, lpt_address, trigger_latency) # fixation
                    pygame.time.set_timer(phase_change, randint(1000,1300)-100)
                    actual_phase = 5
                elif actual_phase == 5:
                    screen.fill(background)
                    pygame.display.flip()
                    count += 1
                    if (count % 20 != 0):
                        pygame.time.set_timer(phase_change, 500)
                        actual_phase = 1
                    else:
                        pygame.time.set_timer(phase_change, 500)
                        actual_phase = 6
                    if count >= len(image_list):
                        pygame.time.wait(600)
                        done=True
                        break
                elif actual_phase == 6:
                    slide(select_slide('exposure_' + condition), False , K_SPACE, 2000)
                    pygame.time.set_timer(phase_change, 2000)
                    actual_phase = 7              
                elif actual_phase == 7:
                    screen.fill(background)
                    pygame.display.flip()
                    pygame.time.set_timer(phase_change, 500)
                    actual_phase = 1

    pygame.event.clear()                    # CLEAR EVENTS

def create_image_list():
    global attractive_images_list, neutral_images_list
    counter_balancing_stimulus = 0
    counter_balancing_type = 0
    attractive_images = 0
    neutral_images = 0
    circles = 0
    rects = 0

    first_image_list = []
    second_image_list = []
    second_image_dict = {"attractivecirc": [], "attractiverect": [], "neutralcirc": [], "neutralrect": []}
    second_image_order = []
    third_image_list = []
    fourth_image_dict = {"attractivecirc": [], "attractiverect": [], "neutralcirc": [], "neutralrect": []}
    fourth_image_order = []
    fourth_image_list = []

    for i in range(60):
        if counter_balancing_stimulus >= 1 or circles == 30:
            actual_stimulus = "rect"
        elif counter_balancing_stimulus <= -1 or rects == 30:
            actual_stimulus = "circ"
        else:
            actual_stimulus = choice(["circ", "rect"])

        if actual_stimulus == "rect":
            counter_stimulus = "circ"
            counter_balancing_stimulus -= 1
            rects += 1
        else:
            counter_stimulus = "rect"
            counter_balancing_stimulus += 1
            circles += 1


        if counter_balancing_type >= 1 or neutral_images == 30:
            actual_type = "attractive"
        elif counter_balancing_type <= -1 or attractive_images == 30:
            actual_type = "neutral"
        else:
            actual_type = choice(["attractive", "neutral"])

        if actual_type == "attractive":
            counter_balancing_type -= 1
            attractive_images += 1
            actual_image = attractive_images_list.pop(0)
        else:
            counter_balancing_type += 1
            neutral_images += 1
            actual_image = neutral_images_list.pop(0)

        first_image_list.append([actual_image, actual_stimulus])
        second_image_dict[actual_type + counter_stimulus].append([actual_image, counter_stimulus])
        second_image_order.append(actual_type + counter_stimulus)

    shuffle(second_image_dict["attractivecirc"])
    shuffle(second_image_dict["attractiverect"])
    shuffle(second_image_dict["neutralcirc"])
    shuffle(second_image_dict["neutralrect"])

    for image in second_image_order:
        second_image_list.append(second_image_dict[image].pop(0))

    counter_balancing_stimulus = 0
    counter_balancing_type = 0
    attractive_images = 0
    neutral_images = 0
    circles = 0
    rects = 0

    for i in range(60):
        if counter_balancing_stimulus >= 1 or circles == 30:
            actual_stimulus = "rect"
        elif counter_balancing_stimulus <= -1 or rects == 30:
            actual_stimulus = "circ"
        else:
            actual_stimulus = choice(["circ", "rect"])

        if actual_stimulus == "rect":
            counter_stimulus = "circ"
            counter_balancing_stimulus -= 1
            rects += 1
        else:
            counter_stimulus = "rect"
            counter_balancing_stimulus += 1
            circles += 1

        if counter_balancing_type >= 1 or neutral_images == 30:
            actual_type = "attractive"
        elif counter_balancing_type <= -1 or attractive_images == 30:
            actual_type = "neutral"
        else:
            actual_type = choice(["attractive", "neutral"])

        if actual_type == "attractive":
            counter_balancing_type -= 1
            attractive_images += 1
            actual_image = attractive_images_list.pop(0)
        else:
            counter_balancing_type += 1
            neutral_images += 1
            actual_image = neutral_images_list.pop(0)

        third_image_list.append([actual_image, actual_stimulus])
        fourth_image_dict[actual_type + counter_stimulus].append([actual_image, counter_stimulus])
        fourth_image_order.append(actual_type + counter_stimulus)

    shuffle(fourth_image_dict["attractivecirc"])
    shuffle(fourth_image_dict["attractiverect"])
    shuffle(fourth_image_dict["neutralcirc"])
    shuffle(fourth_image_dict["neutralrect"])

    for image in fourth_image_order:
        fourth_image_list.append(fourth_image_dict[image].pop(0))

    return ([first_image_list, second_image_list, third_image_list, fourth_image_list])

def fixation_image_list(fixation_time, fixation = True):
    fixation_event = USEREVENT + 1
    pygame.time.set_timer(fixation_event, fixation_time)
    done = False
    
    screen.fill(background)
    pygame.display.flip()
    if fixation:
        screen.blit(fix, fixbox)
        pygame.display.update(fixbox)
    pygame.display.flip()

    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()
            elif event.type == KEYUP and event.key == K_c:
                done=True

            elif event.type == fixation_event:
                if fixation:
                    sleepy_trigger(150, lpt_address, trigger_latency) # fixation
                done = True
                break
    pygame.event.clear()                    # CLEAR EVENTS
  
def show_image_list(joystick, axis_number, image_list, geometry, condition):
    sleepy_trigger(190 + (2 if geometry == "circ" else 1), lpt_address, trigger_latency) # circle/rect trigger
    
    for actual_image in image_list:

        fixation_image_list(200-100 + (150))
        fixation_image_list(500, fixation = False)
        
        actual_image_type = actual_image[0].split('\\')[2]
        show_image(actual_image[0], (base_size, base_size), stimulus = actual_image[1])
        if actual_image_type != "T":
            sleepy_trigger(200 + (1 if condition == "mindful" else 3) + (1 if geometry == actual_image[1] else 0) + (10 if actual_image[0].split('\\')[2] == "N" else 0), lpt_address, trigger_latency) # Correct answer
            actual_image_number = int(actual_image[0].split('\\')[3].split("_")[0])
            sleepy_trigger(actual_image_number, lpt_address, trigger_latency) # image ID
            repetition_list[actual_image_number - 1] += 1
            sleepy_trigger(180 + repetition_list[actual_image_number - 1], lpt_address, trigger_latency) # repetition time            
        else:
            sleepy_trigger(253, lpt_address, trigger_latency)
        answer = wait_control_answer(actual_image[0], joystick, axis_number)
        if not answer:
            break
        else:
            sleepy_trigger(237 + (0 if ((geometry == actual_image[1]) == (answer == "in")) else 1), lpt_address, trigger_latency) # Correct answer
            
        #fixation_image_list(200)

def play_video(video_name):
    VIDEO_PATH = "media\\videos\\" + video_name + ".mp4"
    SOUND_PATH = "media\\sounds\\" + video_name + ".wav"

    video = cv2.VideoCapture(VIDEO_PATH)
    success, video_image = video.read()
    fps = video.get(cv2.CAP_PROP_FPS)

    clock = pygame.time.Clock()
    actual_audio = pygame.mixer.Sound(SOUND_PATH)
    
    done = False

    center = [int(resolution[0] / 2), int(resolution[1] / 2)]
    video_width  = video.get(cv2.CAP_PROP_FRAME_WIDTH)   # float `width`
    video_height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float `height`

    channel = actual_audio.play()

    skyping = False
    
    while not done:
        clock.tick(fps)            
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame_exit()
            elif (event.type == KEYUP and event.key == K_c):
                skyping = True
                done=True
        success, video_image = video.read()
        if success:
            video_image = cv2.cvtColor(video_image, cv2.COLOR_BGR2RGB)
            video_surf = pygame.image.frombuffer(
            video_image.tobytes(), video_image.shape[1::-1], "RGB")
        else:
            done = True
        screen.blit(video_surf, (center[0] - video_width/2, center[1] - video_height/2))
        pygame.display.flip()

    while channel.get_busy() and not skyping:
        pygame.time.wait(100)

    actual_audio.stop()
    #pygame.mixer.music.unload()
    
    screen.fill(background)
    pygame.display.flip()

## Main Function
def main():
    """Game's main loop"""
    
    init_lpt(lpt_address)

    # Si no existe la carpeta data se crea
    if not os.path.exists('data/'):
        os.makedirs('data/')

    # Username = id_condition_geometry_hand
    # conditions = Mindful, Inmerse
    print("No olvidar activar el boton ANALOG del joystick")
    subj_name = raw_input("Ingrese el ID del participante y presione ENTER para iniciar: ")

    while( len(subj_name.split("_")) != 4 ):
        os.system('cls')
        print("No olvidar activar el boton ANALOG del joystick")
        print("ID ingresado no cumple con las condiciones, contacte con el encargado...")
        subj_name = raw_input("Ingrese el ID del participante y presione ENTER para iniciar: ")

    uid, condition, geometry, hand = subj_name.split("_")

    if condition == "C1":
        condition = "control"
    elif condition == "C2":
        condition = "mindful"

    if geometry == "circle":
        geometry = "circ"
    elif geometry == "rect":
        geometry = "rect"

    # 1 = izq, 3 = der
    if hand == "right":
        axis_number = 3
    elif hand == "left":
        axis_number = 1

    #csv_name  = join('data', date_name + '_' + subj_name + '.csv')
    #dfile = open(csv_name, 'w')
    #dfile.write("%s,%s,%s,%s\n" % ("ID", "BT", "RT", "TT"))
    init()
    pygame.mixer.pre_init(48000, -16, 2, 512)
    pygame.mixer.init()
    pygame.mixer.music.set_volume(2)

    # Conexión de Joystick
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("Joystick desconectado")
        joystick = reconnect_joystick()
    else:
        connected_joystick = True
        joystick = pygame.joystick.Joystick(0)
    joystick.init()

    send_trigger(start_trigger, lpt_address, trigger_latency)  # start EEG recording

    '''
    S001_C1_circle_right
    - primera instruction general
    - primer video
    - instrucciones de aplica del video
    - Boke exposicion 1  (imagenes sin estimulo) -> cada 20 mensaje
    - instruccion de aproximacion evidacion
    - Bloque de practica
    - instruccion de aproximacion evidacion (ahora empezara la tarea de verdad)
    - Bloque aproximacion evitacion (AAT) 1
    - instruccion de aproximacion evidacion
    - Bloque aproximacion evitacion (AAT) 2

    - Pantalla instruccion de que viene la siguinte mirad
    - Video
    - Boke exposicion 2  (imagenes restantes sin estimulo)
    - instruccion de aproximacion evidacion (MANO CONTRARIA)
    - instruccion de aproximacion evidacion (ahora empezara la tarea de verdad)
    - Bloque aproximacion evitacion (AAT) 3
    - instruction de aproximacion evidacion
    - Bloque aproximacion evitacion (AAT) 4
    '''

    #carga de lista de imágenes, return ([first_image_list, second_image_list, third_image_list, fourth_image_list])
    image_list = create_image_list()
  
    slide(select_slide('welcome'), False , K_SPACE)

    play_video("VIDEO " + condition.upper())

    slide(select_slide('intro_block_1'), False , K_SPACE)

    show_images([row[0] for row in image_list[1]], condition)

    slide(select_slide('Instructions_AAT', AAT_variables = {"block_number": 0, "geometry": geometry, "stick": hand, "practice": True}), False , K_SPACE)

    show_image_list(joystick, axis_number, trial_images_list, geometry, condition)

    slide(select_slide('Instructions_AAT', AAT_variables = {"block_number": 1, "geometry": geometry, "stick": hand, "practice": False}), False , K_SPACE)    
    sleepy_trigger(195 + 1, lpt_address, trigger_latency) # block number
    show_image_list(joystick, axis_number, image_list[0], geometry, condition)

    slide(select_slide('Instructions_AAT', AAT_variables = {"block_number": 2, "geometry": geometry, "stick": hand, "practice": False}), False , K_SPACE)    
    sleepy_trigger(195 + 2, lpt_address, trigger_latency) # block number
    show_image_list(joystick, axis_number, image_list[1], geometry, condition)
    
    #if geometry == "circ":
    #    geometry = "rect"
    #elif geometry == "rect":
    #    geometry == "circ"

    if hand == "right":
        hand = "left"
        axis_number = 1
    elif hand == "left":
        hand = "right"
        axis_number = 3

    slide(select_slide('intro_block_3'), False , K_SPACE)
    play_video("VIDEO " + condition.upper())

    slide(select_slide('intro_block_1'), False , K_SPACE)

    show_images([row[0] for row in image_list[1]], condition)
    
    slide(select_slide('Instructions_AAT', AAT_variables = {"block_number": 3, "geometry": geometry, "stick": hand, "practice": False}), False , K_SPACE)    
    sleepy_trigger(195 + 3, lpt_address, trigger_latency) # block number
    show_image_list(joystick, axis_number, image_list[2], geometry, condition)

    slide(select_slide('Instructions_AAT', AAT_variables = {"block_number": 4, "geometry": geometry, "stick": hand, "practice": False}), False , K_SPACE)    
    sleepy_trigger(195 + 4, lpt_address, trigger_latency) # block number
    show_image_list(joystick, axis_number, image_list[3], geometry, condition)
    
    slide(select_slide('farewell'), True , K_SPACE)
    send_trigger(stop_trigger, lpt_address, trigger_latency)  # stop EEG recording
    ends()

## Experiment starts here...
if __name__ == "__main__":
    main()
