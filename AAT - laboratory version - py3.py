#!/usr/bin/env python3.10.9
# coding=utf-8

"""
tested in Python 3.10.9
"""
import csv, pygame, random, sys, os, cv2, serial
from pygame.locals import FULLSCREEN, USEREVENT, KEYUP, K_SPACE, K_RETURN, K_ESCAPE, QUIT, Color, K_c
from os.path import isfile, join
from random import randint, shuffle, choice, getrandbits
from time import gmtime, strftime

debug_mode = False

class TextRectException(Exception):
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message

# Configurations:
FullScreenShow = True  # Pantalla completa automáticamente al iniciar el experimento
keys = [pygame.K_SPACE]  # Teclas elegidas para mano derecha o izquierda
test_name = "AAT"
date_name = strftime("%Y-%m-%d_%H-%M-%S", gmtime())
joysticks = {}

# Image Loading

circ = pygame.image.load("media\\images\\fixationstims\\circ.png")
rect = pygame.image.load("media\\images\\fixationstims\\rect.png")

binge_images_list = ["media\\images\\B\\" + f for f in os.listdir(
    "media\\images\\B") if isfile(join("media\\images\\B", f))]
control_images_list = ["media\\images\\C\\" + f for f in os.listdir(
    "media\\images\\C") if isfile(join("media\\images\\C", f))]
trial_images_list = [["media\\images\\T\\" + f, choice(["circ", "rect"])] for f in os.listdir(
    "media\\images\\T") if isfile(join("media\\images\\T", f))]

# count of image repetitions
# repetition_list = [0]*120

shuffle(trial_images_list)

# middle_index = int(len(binge_images_list)/2)
shuffle(binge_images_list)
shuffle(control_images_list)
# binge_images_list_first = binge_images_list[:40]
# control_images_list_first = control_images_list[:40]

shuffle(binge_images_list)
binge_images_list_second_first = binge_images_list[:120]

shuffle(binge_images_list)
binge_images_list_second_second = binge_images_list[120:240]

# print(len(binge_images_list_second_second))

shuffle(binge_images_list)
shuffle(control_images_list)
binge_images_list_third_first = binge_images_list[:50]
control_images_list_third_first = control_images_list[:50]

shuffle(binge_images_list)
binge_images_list_third_second = binge_images_list[:180]

connected_joystick = False
base_size = 350

# Port address and triggers
lpt_address = 0xD100
trigger_latency = 5
start_trigger = 254
stop_trigger = 255

# Experiment Trigger list
# 1-240: ID images, Ok
# 241-243: Block ID's, Ok
# 244: fixation, Ok
# 245: Avoid Binge, Ok
# 246: Avoid Control, Ok
# 247: Approach Binge, Ok
# 248: Approach Control, Ok
# 250: Correct answer
# 251: Incorrect answer
# 252: Binge image, Ok
# 253: Control image, Ok

# 254: Start experiment
# 255: Stop experiment


# Onscreen instructions
def select_slide(slide_name, between_type=None, AAT_variables={"block_number": 0, "geometry": "circle", "practice": True}):

    if slide_name.startswith("intro_block"):
        slide_to_use = "intro_block"
    else:
        slide_to_use = slide_name

    basic_slides = {
        'welcome': [
            u"Bienvenido/a, a este experimento!!!",
            " ",
            u"Se te indicará paso a paso que hacer.",
            " ",
            u"Para comenzar presiona el número 3 en el joystick."
        ],
        'intro_block': [
            u"Ahora comenzará el " + ("primer" if len(slide_name.split("_")) == 3 and slide_name.split("_")[2] == "1" else "segundo" if len(slide_name.split("_")) == 3 and slide_name.split(
                "_")[2] == "2" else "tercer") + " bloque del experimento",
            " ",
            u"Puedes descansar unos segundos, cuando te sientas",
            u"listo para comenzar presiona el número 3 en el joystick."
        ],
        'Instructions_AAT': [
            u"Instrucciones" +
            ("" if AAT_variables["practice"] else (
                " bloque " + str(AAT_variables["block_number"]))) + "",
            " ",
            u"Esta es una tarea de percepción visual, en la cual se presentarán imágenes",
            u"de manera sucesiva. Estas en su centro tendrán un cuadrado o un círculo azul.",
            " ",
            u"La tarea consiste en que cuando un ítem se presente con un " +
            ("CIRCULO" if AAT_variables["geometry"] ==
             "circ" else "CUADRADO") + " debes ACERCAR",
            u"la imagen hacia ti, y cuando sea un " +
            ("CUADRADO" if AAT_variables["geometry"] ==
             "circ" else "CIRCULO") + " debes ALEJAR la imagen de ti.",
            " ",
            u"Usa el joystick para acercar o alejar la imagen.",
            " ",
            u"Al aparecer la imagen por favor responde lo más rápido y preciso posible.",
            " ",
            u"Para comenzar " +
            ("la fase de prueba " if AAT_variables["practice"]
             else "") + "presiona el número 3 en el joystick."
        ],
        'Break': [
            u"Puedes tomar un descanso.",
            " ",
            u"Cuando te sientas listo para continuar presiona el número 3 en el joystick."
        ],
        'wait': [
            "+"
        ],
        'farewell': [
            u"El experimento ha terminado.",
            "",
            u"Muchas gracias por su colaboración!!"
        ]
    }

    selected_slide = basic_slides[slide_to_use]

    return (selected_slide)

# EEG Functions


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


def init_com(address="COM3"):
    """Creates and tests a serial port"""
    global ser
    try:
        ser = serial.Serial()
        ser.port = address
        ser.baudrate = 115200
        ser.open()
        print('Serial port opened')
    except:
        pass
        print('The serial port couldn\'t be opened')


def send_triggert(trigger):
    """Sends a trigger to the serial port"""
    try:
        ser.write((trigger).to_bytes(1, 'little'))
        print('Trigger ' + str(trigger) + ' sent')
    except:
        pass
        print('Failed to send trigger ' + str(trigger))


def sleepy_trigger(trigger, address, latency):
    send_triggert(trigger)
    pygame.time.wait(100)

# Text Functions


def setfonts():
    """Sets font parameters"""
    global bigchar, char, charnext
    pygame.font.init()
    font = join('media', 'Arial_Rounded_MT_Bold.ttf')
    bigchar = pygame.font.Font(font, 96)
    char = pygame.font.Font(font, 32)
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
                    raise TextRectException(
                        "The word " + word + " is too long to fit in the rect passed.")
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
            raise TextRectException(
                "Once word-wrapped, the text string was too tall to fit in the rect.")
        if line != "":
            tempsurface = font.render(line, 1, text_color)
            if justification == 0:
                surface.blit(tempsurface, (0, accumulated_height))
            elif justification == 1:
                surface.blit(
                    tempsurface, ((rect.width - tempsurface.get_width()) / 2, accumulated_height))
            elif justification == 2:
                surface.blit(tempsurface, (rect.width -
                             tempsurface.get_width(), accumulated_height))
            else:
                raise TextRectException(
                    "Invalid justification argument: " + str(justification))
        accumulated_height += font.size(line)[1]

    return final_lines, surface


def paragraph_old(text, just_info, key, rise=0, color=None):
    """Organizes a text into a paragraph"""
    screen.fill(background)
    row = center[1] - 20 * len(text)

    if color == None:
        color = char_color

    for line in text:
        phrasebox = pygame.Rect(
            (resolution[0]/8, rise + 0 + row, resolution[0]*6/8, resolution[1]*5/8))
        final_lines, phrase = render_textrect(line.strip(u'\u200b'), char,  pygame.Rect(
            (resolution[0]/8, resolution[1]/8, resolution[0]*6/8, resolution[1]*6/8)), color, background)
        screen.blit(phrase, phrasebox)
        row += 40 * len(final_lines)
    if just_info:
        if key == K_SPACE:
            foot = "Para continuar presione el NÚMERO 3 DEL JOYSTICK..."
        elif key == K_RETURN:
            foot = "Para continuar presione la tecla ENTER..."
    else:
        foot = ""
    nextpage = charnext.render(foot, True, charnext_color)
    nextbox = nextpage.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(nextpage, nextbox)
    pygame.display.flip()


def paragraph(text, key=None, no_foot=False, color=None):
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
            foot = u"Para continuar presione el NÚMERO 3 DEL JOYSTICK..."
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


def slide(text, info, key, limit_time=0):
    """Organizes a paragraph into a slide"""
    paragraph(text, info, key)
    wait_time = wait(key, limit_time)
    return wait_time

# Program Functions


def init():
    """Init display and others"""
    setfonts()
    global screen, resolution, center, background, char_color, charnext_color, fix, fixbox, fix_think, fixbox_think, izq, der, quest, questbox
    pygame.init()  # soluciona el error de inicializacion de pygame.time
    pygame.display.init()
    pygame.display.set_caption(test_name)
    pygame.mouse.set_visible(False)
    if FullScreenShow:
        resolution = (pygame.display.Info().current_w,
                      pygame.display.Info().current_h)
        screen = pygame.display.set_mode(resolution, FULLSCREEN)
    else:
        try:
            resolution = pygame.display.list_modes()[3]
        except:
            resolution = (1280, 720)
        screen = pygame.display.set_mode(resolution)
    center = (int(resolution[0] / 2), int(resolution[1] / 2))
    izq = (int(resolution[0] / 8), (int(resolution[1] / 8)*7))
    der = ((int(resolution[0] / 8)*7), (int(resolution[1] / 8)*7))
    background = Color('lightgray')
    char_color = Color('black')
    charnext_color = Color('lightgray')
    fix = char.render('+', True, char_color)
    fixbox = fix.get_rect(centerx=center[0], centery=center[1])
    fix_think = bigchar.render('+', True, Color('red'))
    fixbox_think = fix.get_rect(centerx=center[0], centery=center[1])
    quest = bigchar.render('?', True, char_color)
    questbox = quest.get_rect(centerx=center[0], centery=center[1])
    screen.fill(background)
    pygame.display.flip()


def blackscreen(blacktime=0):
    """Erases the screen"""
    screen.fill(background)
    pygame.display.flip()
    pygame.time.delay(blacktime)


def ends():
    """Closes the show"""
    blackscreen()
    dot = char.render('.', True, char_color)
    dotbox = dot.get_rect(left=15, bottom=resolution[1] - 15)
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
        pygame.time.set_timer(TIME_OUT_WAIT, limit_time, loops=1)

    tw = pygame.time.get_ticks()

    switch = True
    while switch:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame_exit()
            elif event.type == pygame.JOYBUTTONDOWN:
                joystick = joysticks[event.instance_id]
                # number 3 in joystick
                if joystick.get_button(2) == 1:
                    switch = False

                '''
                change button from here:
                buttons = joystick.get_numbuttons()
                for i in range(buttons):
                    button = joystick.get_button(0)
                    print(f"Button {i:>2} value: {button}")
                '''
            elif event.type == pygame.JOYDEVICEREMOVED:
                del joysticks[event.instance_id]
                print(f"Joystick {event.instance_id} disconnected")
                reconnect_joystick()
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
    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()

            elif event.type == pygame.JOYDEVICEADDED:
                # This event will be generated when the program starts for every
                # joystick, filling up the list without needing to create them manually.
                joy = pygame.joystick.Joystick(event.device_index)
                joysticks[joy.get_instance_id()] = joy
                print(f"Joystick {joy.get_instance_id()} connected")
                done = True
                return (joy)
        '''
        if pygame.joystick.get_count() > 0:
            done = True
            print("Joystick conectado")
            joystick = pygame.joystick.Joystick(
                pygame.joystick.get_count() - 1)
            joystick.init()
            return (joystick)
        else:
            pygame.joystick.quit()
        '''


def image_in_center(picture):
    center = [int(resolution[0] / 2), int(resolution[1] / 2)]
    return [x - picture.get_size()[count]/2 for count, x in enumerate(center)]


def show_image(image, scale, stimulus=None):
    screen.fill(background)
    picture = pygame.image.load(image)
    picture = pygame.transform.scale(picture, [int(scale[0]), int(scale[1])])
    screen.blit(picture, image_in_center(picture))

    if stimulus != None:
        if stimulus == "rect":
            stimulus = rect
        else:
            stimulus = circ
        screen.blit(stimulus, image_in_center(stimulus))

    pygame.display.flip()


def zoom(image=None, factor=1, time=0, iteration_speed=10):
    global resolution

    # time in sec to ms
    time = time*1000
    max_value = int(resolution[1])*1.2

    # set the scaling to max_value
    if time != 0 and factor**(time/iteration_speed)*base_size > max_value:
        factor = round((max_value/base_size)**(1/(time/iteration_speed)), 3)

    done = False
    zoom_event = USEREVENT + 2
    end_zoom_event = USEREVENT + 3

    pygame.image.load(image)
    size = [base_size, base_size]

    pygame.time.set_timer(zoom_event, iteration_speed,
                          loops=int(time/iteration_speed))
    pygame.time.set_timer(end_zoom_event, int(time), loops=1)

    zoomed = 0
    print("zoom started") if debug_mode else None
    while not done:
        for event in pygame.event.get():
            # and zoomed >= int(time/iteration_speed):
            if event.type == end_zoom_event:
                done = True
                break
            elif event.type == zoom_event:
                zoomed += 1
                # TODO: Min size
                size = [size[0]*factor, size[1]*factor]
                show_image(image, size)

    pygame.time.set_timer(zoom_event, 0)
    pygame.time.set_timer(end_zoom_event, 0)


def wait_control_answer(image, joystick, axis_number):

    image_change = USEREVENT + 4
    pygame.time.set_timer(image_change, 3000, loops=1)

    tw = pygame.time.get_ticks()

    zoom_activate = False
    done = False
    while not done:
        for event in pygame.event.get():

            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()

            elif event.type == pygame.JOYDEVICEREMOVED:
                del joysticks[event.instance_id]
                print(f"Joystick {event.instance_id} disconnected")
                reconnect_joystick()

            elif event.type == KEYUP and event.key == K_c:
                pygame.time.set_timer(image_change, 0)
                pygame.event.clear()        # CLEAR EVENTS
                return (False)

            elif event.type == pygame.JOYAXISMOTION:
                axis = round(joystick.get_axis(axis_number), 2)
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

            elif event.type == image_change:
                zoom_mode = None
                done = True
                break

    pygame.time.set_timer(image_change, 0)
    rt = pygame.time.get_ticks() - tw

    pygame.event.clear()                    # CLEAR EVENTS

    if (zoom_activate):
        image_type = "T"
        if (len(image.split("\\")) >= 2 and image.split("\\")[2] != "T"):
            print(image.split("\\")[2]) if debug_mode else None
            image_type = image.split("\\")[2]
            print(245 + (2 if zoom_mode == "in" else 0) + (0 if image_type == "B" else 1)) if debug_mode else None
            # 245-248: Avoid Binge, Avoid Control, Approach Binge, Approach Control
            sleepy_trigger(245 + (2 if zoom_mode == "in" else 0) + (0 if image_type == "B" else 1) , lpt_address, trigger_latency) # user answer

        if zoom_mode == "out":
            zoom(image=image, factor=0.96, time=0.6, iteration_speed=10)
        elif zoom_mode == "in":
            zoom(image=image, factor=1.11, time=0.6, iteration_speed=16)
        print("zoom finished") if debug_mode else None
    else:
        zoom_mode = None
        if (len(image.split("\\")) >= 2 and image.split("\\")[2] != "T"):
            print(image.split("\\")[2]) if debug_mode else None
            image_type = image.split("\\")[2]
            print(252 + (0 if image_type == "B" else 1)) if debug_mode else None
            # 252-253: Binge image, Control image
            sleepy_trigger(252 + (0 if image_type == "B" else 1) , lpt_address, trigger_latency) # user answer

    pygame.event.clear()                    # CLEAR EVENTS
    return ({"zoom_mode": zoom_mode, "rt": rt})


def show_images(image_list, condition):
    global binge_images_list, control_images_list

    phase_change = USEREVENT + 5

    shuffle(image_list)

    pygame.time.set_timer(phase_change, 500, loops=1)

    done = False
    count = 0

    screen.fill(background)
    pygame.display.flip()

    actual_phase = 1
    joystick_reconnected = False

    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()

            elif event.type == pygame.JOYDEVICEREMOVED:
                del joysticks[event.instance_id]
                print(f"Joystick {event.instance_id} disconnected")
                reconnect_joystick()
                joystick_reconnected = True

            elif event.type == KEYUP and event.key == K_c:
                done = True

            elif event.type == phase_change or joystick_reconnected:
                if actual_phase == 1:
                    show_image(image_list[count], (base_size, base_size))
                    # Exposure image trigger first
                    sleepy_trigger(int(image_list[count].split('\\')[3].split("_")[0]), lpt_address, trigger_latency) # image ID
                    pygame.time.set_timer(phase_change, 3500-200, loops=1)
                    actual_phase = 2
                elif actual_phase == 2:
                    screen.fill(background)
                    pygame.display.flip()
                    pygame.time.set_timer(phase_change, 500, loops=1)
                    actual_phase = 3
                elif actual_phase == 3:
                    show_image(image_list[count], (base_size, base_size))
                    pygame.time.set_timer(phase_change, 500-100, loops=1)
                    actual_phase = 4
                elif actual_phase == 4:
                    screen.fill(background)
                    screen.blit(fix, fixbox)
                    pygame.display.update(fixbox)
                    pygame.display.flip()
                    sleepy_trigger(244, lpt_address, trigger_latency) # fixation
                    pygame.time.set_timer(
                        phase_change, randint(1000, 1300)-100, loops=1)
                    actual_phase = 5
                elif actual_phase == 5:
                    screen.fill(background)
                    pygame.display.flip()
                    count += 1
                    if (count % 20 != 0):
                        pygame.time.set_timer(phase_change, 500, loops=1)
                        actual_phase = 1
                    else:
                        pygame.time.set_timer(phase_change, 500, loops=1)
                        actual_phase = 6
                    if count >= len(image_list):
                        pygame.time.wait(600)
                        done = True
                        break
                elif actual_phase == 6:
                    screen.fill(background)
                    pygame.display.flip()
                    pygame.time.set_timer(phase_change, 500, loops=1)
                    actual_phase = 1

                joystick_reconnected = False

    pygame.time.set_timer(phase_change, 0)

    pygame.event.clear()                    # CLEAR EVENTS


def create_image_list(condition, geometry):
    global binge_images_list_third_first, control_images_list_third_first, binge_images_list_second_first, binge_images_list_second_second, binge_images_list_third_second

    # AAT lists (binge + control)
    first_image_list = []  # 80
    second_image_list = []  # 100
    third_image_list = []  # 100

    first_base_list = []
    third_base_list = []

    # ------------------------ first and third block control balancing ------------------------
    # se debe separar 20 de 25 conjuntos de a 4
    for i in range(25):
        firstbit = getrandbits(1)
        secondbit = getrandbits(1)
        third_base_list.append([[binge_images_list_third_first.pop(), ("circ" if firstbit else "rect")], [binge_images_list_third_first.pop(), ("rect" if firstbit else "circ")], [
                               control_images_list_third_first.pop(), ("circ" if secondbit else "rect")], [control_images_list_third_first.pop(), ("rect" if secondbit else "circ")]])

    first_base_list = third_base_list[:20]

    shuffle(first_base_list)
    shuffle(third_base_list)

    # se obtienen los 4 elementos que se separarán
    first_poped_list = [item for sublist in first_base_list[:4]
                        for item in sublist]
    third_poped_list = [item for sublist in third_base_list[:5]
                        for item in sublist]

    del first_base_list[:4]
    del third_base_list[:5]

    shuffle(first_poped_list)
    shuffle(third_poped_list)

    first_image_list = [
        item for sublist in first_base_list for item in sublist]
    third_image_list = [
        item for sublist in third_base_list for item in sublist]

    numbers_first = [i for i in range(4, 7) for _ in range(8)]
    numbers_third = [i for i in range(4, 7) for _ in range(8)]

    shuffle(numbers_first)
    shuffle(numbers_third)

    actual_position_first = -1
    actual_position_third = -1
    for i in range(len(third_poped_list)):
        if i < len(first_poped_list):
            actual_position_first += numbers_first[i]
            first_image_list.insert(actual_position_first, first_poped_list[i])
        actual_position_third += numbers_third[i]
        third_image_list.insert(actual_position_third, third_poped_list[i])

    shuffle(third_base_list)
    shuffle(third_poped_list)

    second_image_list = [
        item for sublist in third_base_list for item in sublist]

    shuffle(numbers_third)

    actual_position_second = -1
    for i in range(len(third_poped_list)):
        actual_position_second += numbers_third[i]
        second_image_list.insert(actual_position_second, third_poped_list[i])

    second_image_list = list(
        map(lambda x: [x[0], 'rect' if x[1] == 'circ' else 'circ'], second_image_list))

    # ------------------------ second block control separation ------------------------
    # primeras 120: binge_images_list_second_first  segundas 120: binge_images_list_second_second bloque con 180: binge_images_list_third_second

    second_block_first_list = []
    second_block_second_list = []
    third_block_first_list = []

    # sham = 50/50, training = 90/10
    selector = (geometry == "circ")
    if condition == "sham":
        second_block_first_list = list(
            map(lambda x: [x, 'rect' if selector else 'circ'],
                binge_images_list_second_first[:60]))
        temporal_array = list(map(lambda x: [
            x, 'circ' if selector else 'rect'], binge_images_list_second_first[60:120]))
        second_block_first_list.extend(temporal_array)

        second_block_second_list = list(
            map(lambda x: [x, 'rect' if selector else 'circ'],
                binge_images_list_second_second[:60]))
        temporal_array = list(map(lambda x: [
            x, 'circ' if selector else 'rect'], binge_images_list_second_second[60:120]))
        second_block_second_list.extend(temporal_array)

        third_block_first_list = list(
            map(lambda x: [x, 'rect' if selector else 'circ'],
                binge_images_list_third_second[:90]))
        temporal_array = list(map(lambda x: [
            x, 'circ' if selector else 'rect'], binge_images_list_third_second[90:180]))
        third_block_first_list.extend(temporal_array)

    else:
        second_block_first_list = list(
            map(lambda x: [x, 'rect' if selector else 'circ'],
                binge_images_list_second_first[:108]))
        temporal_array = list(map(lambda x: [
            x, 'circ' if selector else 'rect'], binge_images_list_second_first[108:120]))
        second_block_first_list.extend(temporal_array)

        second_block_second_list = list(
            map(lambda x: [x, 'rect' if selector else 'circ'],
                binge_images_list_second_second[:108]))
        temporal_array = list(map(lambda x: [
            x, 'circ' if selector else 'rect'], binge_images_list_second_second[108:120]))
        second_block_second_list.extend(temporal_array)

        third_block_first_list = list(
            map(lambda x: [x, 'rect' if selector else 'circ'],
                binge_images_list_third_second[:162]))
        temporal_array = list(map(lambda x: [
            x, 'circ' if selector else 'rect'], binge_images_list_third_second[162:180]))
        third_block_first_list.extend(temporal_array)

    shuffle(second_block_first_list)
    shuffle(second_block_second_list)
    shuffle(third_block_first_list)

    # 80, 120, 120, 100, 180, 100
    return ([first_image_list, second_block_first_list, second_block_second_list, second_image_list, third_block_first_list, third_image_list])


def fixation_image_list(fixation_time, fixation=True):

    fixation_event = USEREVENT + 6
    pygame.time.set_timer(fixation_event, fixation_time, loops=1)
    done = False

    screen.fill(background)
    pygame.display.flip()
    if fixation:
        screen.blit(fix, fixbox)
        pygame.display.update(fixbox)
    pygame.display.flip()

    tw = pygame.time.get_ticks()

    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()
            elif event.type == KEYUP and event.key == K_c:
                done = True

            elif event.type == fixation_event:  # and pygame.time.get_ticks() - tw >= fixation_time
                if fixation:
                    sleepy_trigger(244, lpt_address, trigger_latency) # fixation
                done = True
                break

    pygame.time.set_timer(fixation_event, 0)
    pygame.event.clear()                    # CLEAR EVENTS


def show_image_list(joystick, axis_number, image_list, geometry, condition, uid, subj_name, dfile, block_number):

    for actual_image in image_list:

        print(actual_image) if debug_mode else None

        fixation_image_list(200-100 + (150))
        fixation_image_list(500, fixation=False)

        actual_image_type = actual_image[0].split('\\')[2]
        show_image(actual_image[0], (base_size,
                   base_size), stimulus=actual_image[1])
        answer = wait_control_answer(actual_image[0], joystick, axis_number)
        print("exit answer") if debug_mode else None
        if not answer:
            break
        else:
            print("answer") if debug_mode else None
            print(250 + (0 if (((geometry == actual_image[1]) == (answer["zoom_mode"] == "in")) and answer["zoom_mode"] != None) else 1)) if debug_mode else None
            sleepy_trigger(250 + (0 if (((geometry == actual_image[1]) == (answer["zoom_mode"] == "in")) and answer["zoom_mode"] != None) else 1), lpt_address, trigger_latency) # Correct answer
            # file writer
            print("writing") if debug_mode else None

            if actual_image_type != "T":
                actual_image_number = int(actual_image[0].split('\\')[3].split("_")[0])
                dfile.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (subj_name, condition.capitalize(), geometry == "rect", uid, answer["rt"]+300, ("Binge" if actual_image_type == "B" else "Control"), ("Círculo" if actual_image[1] == "circ" else "Cuadrado"), ("Approach" if (answer["zoom_mode"] == "in") else (
                    "Avoid" if (answer["zoom_mode"] == "out") else answer["zoom_mode"])), actual_image_number, ("Mano Derecha" if axis_number == 3 else "Mano Izquierda"), "???", block_number, (False if answer["zoom_mode"] == None else ((geometry == actual_image[1]) == (answer["zoom_mode"] == "in")))))

def obtain_images(actual_block):
    return actual_block[0]


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
    video_width = video.get(cv2.CAP_PROP_FRAME_WIDTH)   # float `width`
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
                done = True
        success, video_image = video.read()
        if success:
            video_image = cv2.cvtColor(video_image, cv2.COLOR_BGR2RGB)
            video_surf = pygame.image.frombuffer(
                video_image.tobytes(), video_image.shape[1::-1], "RGB")
        else:
            done = True
        screen.blit(
            video_surf, (center[0] - video_width/2, center[1] - video_height/2))
        pygame.display.flip()

    while channel.get_busy() and not skyping:
        pygame.time.wait(100)

    actual_audio.stop()

    screen.fill(background)
    pygame.display.flip()

# Main Function


def main():
    global block1_images, block3_images
    """Game's main loop"""

    init_com()

    # Si no existe la carpeta data se crea
    if not os.path.exists('data/'):
        os.makedirs('data/')

    # Username = id_condition_geometry_hand
    print("No olvidar activar el boton ANALOG del joystick")
    subj_name = input(
        "Ingrese el ID del participante y presione ENTER para iniciar: ")

    while (len(subj_name.split("_")) != 3):
        os.system('cls')
        print("No olvidar activar el boton ANALOG del joystick")
        print("ID ingresado no cumple con las condiciones, contacte con el encargado...")
        subj_name = input(
            "Ingrese el ID del participante y presione ENTER para iniciar: ")

    uid, condition, geometry = subj_name.split("_")

    if condition == "C1":
        condition = "sham"
    elif condition == "C2":
        condition = "training"

    if geometry == "circle":
        geometry = "circ"
    elif geometry == "rect":
        geometry = "rect"

    # 1 = vertical |, 3 = horizontal -
    axis_number = 1

    image_list = create_image_list(condition, geometry)

    # Create a file to save the data
    bfile = open('list.csv', 'w')
    bfile.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % ("First Block AAT", " ", " ",
                "Second Block First List", " ", " ", "Second Block Second List", " ", " ",
                                                                             "Third Block First AAT", " ", " ", "Third Block List", " ", " ", "Third Block Second AAT", " ", " "))
    bfile.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % ("Type", "Image", "Geometric",
                "Type", "Image", "Geometric", "Type", "Image", "Geometric", "Type", "Image", "Geometric", "Type", "Image", "Geometric", "Type", "Image", "Geometric"))

    for i in range(len(image_list[4])):
        # print(image_list[0][i][0].split('_')[0].split('\\')[-1])
        # print(int(image_list[0][i][0].split('_')[2].split('.')[0]))
        bfile.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" %
                    ((image_list[0][i][0].split('_')[0].split('\\')[2] if len(image_list[0]) > i else ""),
                     int(image_list[0][i][0].split('_')[0].split(
                         '\\')[-1]) if len(image_list[0]) > i else "",
                     image_list[0][i][1] if len(
                        image_list[0]) > i else "",
                     image_list[1][i][0].split('_')[0].split(
                        '\\')[2] if len(image_list[1]) > i else "",
                     int(image_list[1][i][0].split('_')[0].split(
                         '\\')[-1]) if len(image_list[1]) > i else "",
                     image_list[1][i][1] if len(
                        image_list[1]) > i else "",
                     image_list[2][i][0].split('_')[0].split(
                        '\\')[2] if len(image_list[2]) > i else "",
                     int(image_list[2][i][0].split('_')[0].split(
                         '\\')[-1]) if len(image_list[2]) > i else "",
                     image_list[2][i][1] if len(
                        image_list[2]) > i else "",
                     image_list[3][i][0].split('_')[0].split(
                        '\\')[2] if len(image_list[3]) > i else "",
                     int(image_list[3][i][0].split('_')[0].split(
                         '\\')[-1]) if len(image_list[3]) > i else "",
                     image_list[3][i][1] if len(
                        image_list[3]) > i else "",
                     image_list[4][i][0].split('_')[0].split(
                        '\\')[2] if len(image_list[4]) > i else "",
                     int(image_list[4][i][0].split('_')[0].split(
                         '\\')[-1]) if len(image_list[4]) > i else "",
                     image_list[4][i][1] if len(
                        image_list[4]) > i else "",
                     image_list[5][i][0].split('_')[0].split(
                        '\\')[2] if len(image_list[5]) > i else "",
                     int(image_list[5][i][0].split('_')[0].split(
                         '\\')[-1]) if len(image_list[5]) > i else "",
                     image_list[5][i][1] if len(image_list[5]) > i else "")
                    )
    bfile.close()

    block_images = []

    for block in image_list:
        block_images.append(list(map(obtain_images, block)))

    # Conexión de Joystick
    pygame.init()

    csv_name = join('data', date_name + '_' + subj_name + '.csv')
    dfile = open(csv_name, 'w')
    dfile.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % ("Grupo", "Condicion", "CirculoAlejar", "Sujeto", "TReaccion",
                "TipoImagen", "TipoCue", "Respuesta", "IdImagen", "FormadeRespuesta", "ManoDominante", "Bloque", "Acierto"))
    dfile.flush()

    init()
    pygame.mixer.pre_init(48000, -16, 2, 512)
    pygame.mixer.init()
    pygame.mixer.music.set_volume(2)

    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("Joystick desconectado")
        joystick = reconnect_joystick()
    else:
        joystick = pygame.joystick.Joystick(0)
        joysticks[joystick.get_instance_id()] = joystick

    send_triggert(start_trigger)

    '''
    S001_C1_circle
    S002_C2_rect
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

    # carga de lista de imágenes, return ([first_image_list, second_image_list, third_image_list, fourth_image_list])
    slide(select_slide('welcome'), False, K_SPACE)

    # ------------------------ first block ------------------------

    slide(select_slide('intro_block_1'), False, K_SPACE)
    # practice trials
    slide(select_slide('Instructions_AAT', AAT_variables={
          "block_number": 1, "geometry": geometry, "practice": True}), False, K_SPACE)

    show_image_list(joystick, axis_number, trial_images_list,
                    geometry, condition, uid, subj_name, dfile, 0)

    # first 80 trials AAT
    slide(select_slide('Instructions_AAT', AAT_variables={
          "block_number": 1, "geometry": geometry, "practice": False}), False, K_SPACE)
    sleepy_trigger(240 + 1, lpt_address, trigger_latency) # block number
    show_image_list(joystick, axis_number,
                    image_list[0], geometry, condition, uid, subj_name, dfile, 1)
    dfile.flush()

    # ------------------------ second block ------------------------

    slide(select_slide('intro_block_2'), False, K_SPACE)
    # practice trials
    slide(select_slide('Instructions_AAT', AAT_variables={
          "block_number": 2, "geometry": geometry, "practice": True}), False, K_SPACE)

    show_image_list(joystick, axis_number, trial_images_list,
                    geometry, condition, uid, subj_name, dfile, 0)

    # first 120 trials AAT
    slide(select_slide('Instructions_AAT', AAT_variables={
          "block_number": 2, "geometry": geometry, "practice": False}), False, K_SPACE)
    sleepy_trigger(240 + 2, lpt_address, trigger_latency) # block number
    show_image_list(joystick, axis_number,
                    image_list[1], geometry, condition, uid, subj_name, dfile, 2)
    dfile.flush()

    slide(select_slide('Break'), False, K_SPACE)

    # second 120 trials AAT
    slide(select_slide('Instructions_AAT', AAT_variables={
          "block_number": 2, "geometry": geometry, "practice": False}), False, K_SPACE)
    sleepy_trigger(240 + 2, lpt_address, trigger_latency) # block number
    show_image_list(joystick, axis_number,
                    image_list[2], geometry, condition, uid, subj_name, dfile, 2)
    dfile.flush()

    # ------------------------ third block ------------------------

    # slide(select_slide('intro_block_3'), False, K_SPACE)
    # play_video("VIDEO " + condition.upper())

    # show_images(block_images[2], condition)

    slide(select_slide('intro_block_3'), False, K_SPACE)

    # practice trials
    slide(select_slide('Instructions_AAT', AAT_variables={
          "block_number": 3, "geometry": geometry, "practice": True}), False, K_SPACE)

    show_image_list(joystick, axis_number, trial_images_list,
                    geometry, condition, uid, subj_name, dfile, 0)

    # first 100 trials AAT
    slide(select_slide('Instructions_AAT', AAT_variables={
          "block_number": 3, "geometry": geometry, "practice": False}), False, K_SPACE)
    sleepy_trigger(240 + 3, lpt_address, trigger_latency) # block number
    show_image_list(joystick, axis_number,
                    image_list[3], geometry, condition, uid, subj_name, dfile, 3)
    dfile.flush()

    slide(select_slide('Break'), False, K_SPACE)
    # 180 training trials
    slide(select_slide('Instructions_AAT', AAT_variables={
          "block_number": 3, "geometry": geometry, "practice": False}), False, K_SPACE)
    sleepy_trigger(240 + 3, lpt_address, trigger_latency) # block number
    show_image_list(joystick, axis_number,
                    image_list[4], geometry, condition, uid, subj_name, dfile, 4)
    dfile.flush()

    slide(select_slide('Break'), False, K_SPACE)
    # second 100 trials AAT
    slide(select_slide('Instructions_AAT', AAT_variables={
          "block_number": 3, "geometry": geometry, "practice": False}), False, K_SPACE)
    sleepy_trigger(240 + 3, lpt_address, trigger_latency) # block number
    show_image_list(joystick, axis_number,
                    image_list[5], geometry, condition, uid, subj_name, dfile, 4)
    dfile.flush()

    slide(select_slide('farewell'), True, K_SPACE)
    send_triggert(stop_trigger)
    dfile.close()
    ends()


# Experiment starts here...
if __name__ == "__main__":
    main()
