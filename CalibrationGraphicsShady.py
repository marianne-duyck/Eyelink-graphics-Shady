
# Created Apr 2021 by marianne.duyck@gmail.com
# Last updated on Apr 2021

import Shady
import Shady.Text
from PIL import Image, ImageOps
from playsound import playsound
import numpy as np
import pylink
import sys
import os


def _getTargetLayer(world):
    return 0.5

def _getEyeImageLayer(world):
    return 0.9

def _getCrossHairsLayer(world):
    return 0.8

def _getTextLayer(world):
    return 0.7


def _defaultHandler(world, event):
    if event.type == 'key_press' and event.key in ['q', 'escape']:
        world.Close()


def _handleEvents(world, event):
    if event.type == 'key_press':
        mod = 0 # modifier value
        try:
            keycode = ord(event.key)
        except: pass
        if event.key == 'f1':
            keycode = pylink.F1_KEY
        elif event.key == 'f2':
            keycode = pylink.F2_KEY
        elif event.key == 'f3':
            keycode = pylink.F3_KEY
        elif event.key == 'f4':
            keycode = pylink.F4_KEY
        elif event.key == 'f5':
            keycode = pylink.F5_KEY
        elif event.key == 'f6':
            keycode = pylink.F6_KEY
        elif event.key == 'f7':
            keycode = pylink.F7_KEY
        elif event.key == 'f8':
            keycode = pylink.F8_KEY
        elif event.key == 'f9':
            keycode = pylink.F9_KEY
        elif event.key == 'f10':
            keycode = pylink.F10_KEY
        elif event.key == 'pageup':
            keycode = pylink.PAGE_UP
        elif event.key == 'pagedown':
            keycode = pylink.PAGE_DOWN
        elif event.key == 'up':
            keycode = pylink.CURS_UP
        elif event.key == 'down':
            keycode = pylink.CURS_DOWN
        elif event.key == 'left':
            keycode = pylink.CURS_LEFT
        elif event.key == 'right':
            keycode = pylink.CURS_RIGHT
        elif event.key == 'backspace':
            keycode = ord('\b')
        elif event.key == 'return':
            keycode = pylink.ENTER_KEY
        elif event.key == 'space':
            keycode = ord(' ')
        elif event.key == 'escape':
            keycode = pylink.ESC_KEY
        elif event.key == 'tab':
            keycode = ord('\t')
        elif (keycode == pylink.JUNK_KEY):
            keycode = 0
        world.keys.append(pylink.KeyInput(keycode, mod))

    if event.type == 'mouse_motion':
        world.mouse_x = event.x # shady coords
        world.mouse_y = event.y
    if event.type == 'mouse_press':
        world.mouse_anypress = 1 #trackpad returns event.key as None?
    else: world.mouse_anypress = 0



class FixationTarget(object):
    def __init__(self, shady_window):
        self.wind = shady_window
        self.target_size = 32 #pix
        self.target_color = [0]*3
        self.on = None # tracks on screen presence

    def _create(self):
        raise NotImplementedError("_create() must be implemented in subclass")

    def set_target_size(self, size):
        raise NotImplementedError("set_target_size() must be implemented in subclass")

    def set_target_color(self, color):
        raise NotImplementedError("set_target_color() must be implemented in subclass")

    def draw(self, pos=None):
        raise NotImplementedError("draw() must be implemented in subclass")

    def clear(self):
        raise NotImplementedError("draw() must be implemented in subclass")


class Full(FixationTarget):
    def __init__(self, shady_window):
        super(Full, self).__init__(shady_window)
        self._crossLw = int(round(0.2 * self.target_size)) # prop of size
        self._centerDiameter = self._crossLw # pix
        self._crossColor = [0.5]*3
        self._create()

    def _create(self):
        center = [0, 0]
        lines = np.zeros((4*self._crossLw, 2))
        loffs = np.arange(self._crossLw) - self._crossLw/2
        arm = self.target_size/2
        k = 0
        for lo in loffs:
            lines[k, 0] = center[0] - arm 
            lines[k, 1] = center[1] + lo
            lines[k+1, 0] = center[0] + arm 
            lines[k+1, 1] = center[1] + lo
            lines[k+2, 0] = center[0] + lo
            lines[k+2, 1] = center[1] - arm
            lines[k+3, 0] = center[0] + lo
            lines[k+3, 1] = center[1] + arm
            k += 4
        self.surround = self.wind.Stimulus(size=self.target_size, color=self.target_color, pp=1, anchor=Shady.LOCATION.CENTER, 
                                           position=[0., 0.], backgroundAlpha=0, visible=False, z=_getTargetLayer(self.wind)+0.1)
        self.cross = self.wind.Stimulus(size=self.wind.size, color=self._crossColor, drawMode=Shady.DRAWMODE.LINES, 
                                        penThickness=1, backgroundAlpha=0, points=lines, visible=False, z=_getTargetLayer(self.wind))
        self.center = self.wind.Stimulus(size=self._centerDiameter, color=self.target_color, pp=1, anchor=Shady.LOCATION.CENTER, 
                                         position=[0., 0.],backgroundAlpha=0, visible=False, z=_getTargetLayer(self.wind)-0.1)
        self.on = False

    def set_target_size(self, size):
        # because cross different, simpler to recreate (so removes previous stims)
        for element in [self.surround, self.cross, self.center]:
            element.Leave()
        self.target_size = size
        self._create()

    def set_target_color(self, color):
        self.target_color = color
        for element in [self.surround, self.center]:
            element.color = self.target_color

    def draw(self, pos=None):
        if pos:
            for element in [self.surround, self.cross, self.center]:
                element.position = pos
            self.cross.position = [pos[0]+self.wind.size[0]/2, pos[1]+self.wind.size[1]/2] #diff ref frame
        for element in [self.surround, self.cross, self.center]:
            element.visible = True
        self.on = True

    def clear(self):
        for element in [self.surround, self.cross, self.center]:
            element.visible = False
        self.on = False



class Circle(FixationTarget):
    '''
    if outer circle artifacts, should consider implement a 2 overlapping disks version i.of proper circle
    '''
    def __init__(self, shady_window):
        super(Circle, self).__init__(shady_window)
        self.target_inner = 0.25*self.target_size # in prop of outer radius
        self._create()

    def _create(self):
        nSides, lw, radius = 30, int(round(self.target_size/2 - self.target_inner/2)), self.target_size/2
        center = [0, 0]
        poffs = radius-np.arange(lw)
        dimPolygon = nSides+2
        points = np.zeros((1, lw*dimPolygon), dtype=complex)
        k=0
        for p in poffs: 
            points[0, k:k+nSides+2] = p*Shady.ComplexPolygonBase(nSides, joined=True) + [center[0]+1j*center[1]]
            k += nSides+2
        self.circle = self.wind.Stimulus(size=self.wind.size, anchor = Shady.LOCATION.CENTER, position = [0., 0.], drawMode=Shady.DRAWMODE.LINE_STRIP, 
                                         penThickness=1, points=points, color=self.target_color, visible=False, z=_getTargetLayer(self.wind))
        self.on = False

    def set_target_size(self, size):
        self.target_size = size # because cross different, simpler to recreate (so removes previous stim)
        self.circle.Leave()
        self._create()

    def set_target_color(self, color):
        self.target_color = color
        self.circle.color = color

    def draw(self, pos=None):
        if pos:
            self.circle.position = [pos[0]+self.wind.size[0]/2, pos[1]+self.wind.size[1]/2]
        self.circle.visible = True
        self.on = True

    def clear(self):
        self.circle.visible = False
        self.on = False


class Disk(FixationTarget):
    def __init__(self, shady_window):
        super(Disk, self).__init__(shady_window)
        self._create()

    def _create(self):
        self.disk = self.wind.Stimulus(size=self.target_size, color=self.target_color, pp=1, anchor=Shady.LOCATION.CENTER, 
                                       position=[0., 0.], backgroundAlpha=0, visible=False, z=_getTargetLayer(self.wind))
        self.on = False

    def set_target_size(self, size):
        self.target_size = size
        self.disk.size = self.target_size

    def set_target_color(self, color):
        self.target_color = color
        self.disk.color = self.target_color

    def draw(self, pos=None):
        if pos:
            self.disk.position = pos
        self.disk.visible = True
        self.on = True

    def clear(self):
        self.disk.visible = False
        self.on = False


class Cross(FixationTarget):
    def __init__(self, shady_window):
        super(Cross, self).__init__(shady_window)
        self._crossLw = int(round(0.1*self.target_size)) # pix
        self._centerDiameter = self._crossLw*2
        self._centerColor = [np.abs(i-1) for i in self.target_color]
        self._create()

    def _create(self):
        center = [0, 0]
        lines = np.zeros((4*self._crossLw, 2))
        loffs = np.arange(self._crossLw) - self._crossLw/2
        arm = self.target_size/2
        k = 0
        for lo in loffs:
            lines[k, 0] = center[0] - arm 
            lines[k, 1] = center[1] + lo
            lines[k+1, 0] = center[0] + arm 
            lines[k+1, 1] = center[1] + lo
            lines[k+2, 0] = center[0] + lo
            lines[k+2, 1] = center[1] - arm
            lines[k+3, 0] = center[0] + lo
            lines[k+3, 1] = center[1] + arm
            k += 4
  
        self.cross = self.wind.Stimulus(size=self.wind.size, color=self.target_color, drawMode=Shady.DRAWMODE.LINES, 
                                        penThickness=1, points=lines, visible=False, z=_getTargetLayer(self.wind))
        self.center = self.wind.Stimulus(size=self._centerDiameter, color=self._centerColor, pp=1, anchor=Shady.LOCATION.CENTER, 
                                       position=[0., 0.], backgroundAlpha=0, visible=False, z=_getTargetLayer(self.wind)-0.1)
        self.on = False

    def set_target_size(self, size):
        # recreates stim, so resets position
        self.target_size = size
        self._crossLw = int(round(0.1*self.target_size)) # pix
        self._centerDiameter = self._crossLw*2
        for element in [self.cross, self.center]:
            element.Leave()
        self._create()

    def set_target_color(self, color):
        self.target_color = color
        self._centerColor = [np.abs(i-1) for i in self.target_color]
        self.cross.color = self.target_color
        self.center.color = self._centerColor

    def draw(self, pos=None):
        if pos:
            self.cross.position = [pos[0]+self.wind.size[0]/2, pos[1]+self.wind.size[1]/2]
            self.center.position = pos
        self.cross.visible = True
        self.center.visible = True
        self.on = True

    def clear(self):
        self.cross.visible = False
        self.center.visible = False
        self.on = False


class MenuScreen(object):

    #MD size in percent of screen size
    def __init__(self, shady_window):
        self._win = shady_window
        self._fontSize = 18
        self._txtColor = [0]*3
        self._menuTxt = ("ENTER: Show/Hide Camera Image \n"+
                         "LEFT/RIGHT: Switch between camera views \n"+
                         "C: Start Calibration \n"+
                         "V: Start Validation \n"+
                         "ESCAPE: Exit Eyelink System Setup \n\n"+
                         "A: Auto-Threshold Image\n"+
                         "UP/DOWN: Manually Adjust Pupil Threshold\n"+
                         "+/-: Manually Adjust CR Threshold")
        self.on = None
        self._create()

    def _create(self):
        self._txt = self._win.Stimulus(text=self._menuTxt, text_align='left', 
                                     text_fill=self._txtColor, text_size=self._fontSize,
                                     y=-self._win.size[1]/4, visible=False)

    def set_menu_color(self, color):
        self._txtColor = color
        self._txt.text_fill = self._txtColor

    def draw(self):
        self._txt.visible = True
        self.on = True

    def clear(self):
        self._txt.visible = False
        self.on = False


class CalibrationGraphics(pylink.EyeLinkCustomDisplay):

    """
    Handles interaction pylink/shady mainly used for calibration.
    functions_like_that are callable by the eyelink tracker
    functionsLikeThat are callable by the main code to setup some parameters
    _functionsLikeThat are utilities used inside the previous cases

    Parameters:
        tracker: eyelink tracker
        win: shady window, canvas with background color set
        target_type: "full" (default), "disk", "circle" or "cross"

    Check which function called when leaves setup display for good 
    and makes all stimuli Leave() the world?
    """

    def __init__(self, tracker, win, target='full', verbose=False):

        pylink.EyeLinkCustomDisplay.__init__(self)

        self.win = win  # screen to use for calibration (assumes canvas mode with background color preset)
        self.tracker = tracker  # connection to the tracker
        self._targetType = target
        self.target = None
        self.verbose = verbose

        # initialize events variables
        self.win.keys = []
        self.win.mouse_x, self.win.mouse_y = self.win.size[0]/2, self.win.size[1]/2
        self.win.mouse_anypress = 0

        # initialize camera eye stims (image and cross hair)
        self.eye_image_title = None
        self.eye_image_size = [640, 480] # intended size of displayed eye_image from camera (bigger than input)
        self.eye_image = None
        self._resetCrossHair()

        self.cross_hair_stims = None

        self.target = self._createCalibrationTarget() 
        self.menu = MenuScreen(self.win)


    def _createCalibrationTarget(self):
        if self.verbose: print("_createCalibrationTarget")
        if self._targetType == 'full':
            return Full(self.win)
        elif self._targetType == 'disk':
            return Disk(self.win)
        elif self._targetType == 'circle':
            return Circle(self.win)
        elif self._targetType == 'cross':
            return Cross(self.win)


    def _getColorFromIndex(self, colorindex):
        ''' color scheme for different elements only 4 possible colors'''

        if colorindex == pylink.CR_HAIR_COLOR:
            return (1, 1, 1, 1)
        elif colorindex == pylink.PUPIL_HAIR_COLOR:
            return (1, 1, 1, 1)
        elif colorindex == pylink.PUPIL_BOX_COLOR:
            return (0, 1, 0, 1)
        elif colorindex == pylink.SEARCH_LIMIT_BOX_COLOR:
            return (1, 0, 0, 1)
        elif colorindex == pylink.MOUSE_CURSOR_COLOR:
            return (1, 0, 0, 1)
        else:
            return (0, 0, 0, 0)


    def _meta_draw_cross_hair(self):
        '''
        draw cross hair with putative components:
        - mouse position (red crosses)
        - CR and pupil cross hair (white crosses)
        - pupil box color (green square)
        - search limits on head view (red "lozenge")

        instead of using typical pygame/psychopy draw_line/draw_lozenge usage function,
        only collects data from these functions to update the 4 putative stim
        A bit messy
        '''
        self._resetCrossHair()
        self.draw_cross_hair() # Eyelink defined function, calls other functions (draw_line, get_mouse_state and draw_lozenge from what I gathered...)
        
        if self.cross_hair_stims is None:
            self.cross_hair_stims = {}
            for s in self.cross_hair_lines.keys():
                color = self._getColorFromIndex(abs(s))
                if np.sign(s) > 0:
                    self.cross_hair_stims[s] = self.win.Stimulus(size=self.eye_image_size, anchor=Shady.LOCATION.CENTER, position=[0., 0.], 
                                                                 drawMode=Shady.DRAWMODE.LINES, penThickness=5, points=self.cross_hair_lines[s], 
                                                                 color=color, visible=True, smoothing=True, z=_getCrossHairsLayer(self.win))
                else:
                    self.cross_hair_stims[s] = self.win.Stimulus(size=self.eye_image_size, anchor=Shady.LOCATION.CENTER, position=[0., 0.], 
                                                                 drawMode=Shady.DRAWMODE.LINE_LOOP, penThickness=5, points=self.cross_hair_lines[s], 
                                                                 color=color, visible=True, smoothing=True, z=_getCrossHairsLayer(self.win))

        else:
            for s in self.cross_hair_lines.keys():
                self.cross_hair_stims[s].points = self.cross_hair_lines[s]


    def _resetCrossHair(self):
        self.cross_hair_lines = {}
        for i in range(1, 6): # possible color indices, used for lines
            self.cross_hair_lines[i] = []
        self.cross_hair_lines[-5] = [] # index for lozenge


    def setCalibrationColor(self, color):
        """ Set calibration color
        Parameters:
            color--foreground color for the calibration target, eg: [0.5, 0.5, 0.5]
        only after target has been created
        """
        if self.verbose: print("setCalibrationColor")
        self._targetColor = color
        if self.target is not None:
            self.target.set_target_color(self._targetColor)


    def setCalibrationSize(self, size):
        """ Set calibration target size
        Parameters:
            size: total width/diameter in pixels
        only after target has been created
        """
        if self.verbose: print("setCalibrationSize")
        self._targetSize = size
        if self.target is not None:
            self.target.set_target_size(self._targetSize)


    def setCalibrationSounds(self, target_beep, done_beep, error_beep):
        """ Provide three wav files as the warning beeps

        Parameters:
            target_beep -- sound to play when the target comes up
            done_beep -- calibration is done successfully
            error_beep -- calibration/drift-correction error.
        """
        if self.verbose: print("setCalibrationSounds")

        # target beep
        if target_beep == '':
            self._target_beep = "type.wav"
        elif target_beep == 'off':
            self._target_beep = None
        else:
            self._target_beep = target_beep

        # done beep
        if done_beep == '':
            self._done_beep = "qbeep.wav"
        elif done_beep == 'off':
            self._done_beep = None
        else:
            self._done_beep = done_beep

        # error beep
        if error_beep == '':
            self._error_beep = "error.wav"
        elif error_beep == 'off':
            self._error_beep = None
        else:
            self._error_beep = error_beep


    def setup_cal_display(self):
        if self.verbose: print("setup_cal_display")
        '''init event handling while in camera setup mode and shows menu options'''
        if self.tracker.getCurrentMode() == pylink.IN_SETUP_MODE:
            self.menu.draw()
        self.win.SetEventHandler(_handleEvents, slot=0)


    def exit_cal_display(self):
        if self.verbose: print("exit_cal_display")
        '''exits camera setup and release corresponding Shady resources'''
        self.clear_cal_display()
        if self.tracker.getCurrentMode() == pylink.IN_IDLE_MODE:
            self.win.SetEventHandler(_defaultHandler, slot=0)


    def clear_cal_display(self):
        if self.verbose: print("clear_cal_display")
        if self.menu.on:
            self.menu.clear()
        if self.target.on:
            self.target.clear()
        if self.eye_image_title is not None:
            self.eye_image_title.visible = False
        if self.eye_image is not None:
            self.eye_image.visible = False
        if self.cross_hair_stims is not None:
            for element in self.cross_hair_stims.values():
                element.visible = False


    def erase_cal_target(self):
        if self.verbose: print("erase_cal_target")
        self.clear_cal_display()


    def draw_cal_target(self, x, y):
        if self.verbose: print('draw_cal_target', x, y)
        # converts to shady default coords
        x = x - self.win.size[0]/2
        y = - (y - self.win.size[1]/2)
        self.target.draw(pos=(x, y))


    def get_input_key(self):
        ''' handle key input and send it over to the tracker'''
        # if self.win._World__event_handlers[0].__name__ != _handleEvents:
        #     self.win.SetEventHandler(_handleEvents, slot=0)
        if len(self.win.keys) > 0:
            k = self.win.keys
            self.win.keys = []
            return k
        else:
            return None


    def play_beep(self, beepid):
        if self.verbose: print("play_beep")
        '''play warning beeps if being requested'''
        # sound playback should work on all platforms
        if beepid in [pylink.DC_TARG_BEEP, pylink.CAL_TARG_BEEP]:
            if self._target_beep is not None:
                playsound(self._target_beep, block=False)
        if beepid in [pylink.CAL_ERR_BEEP, pylink.DC_ERR_BEEP]:
            if self._error_beep is not None:
                playsound(self._error_beep)
        if beepid in [pylink.CAL_GOOD_BEEP, pylink.DC_GOOD_BEEP]:
            if self._done_beep is not None:
                playsound(self._done_beep)


    def image_title(self, text):
        if self.verbose: print("image_title")
        if self.eye_image_title is None:
            self.eye_image_title = self.win.Stimulus(text=text, text_align='left', 
                                                      text_fill=0, text_size=18,
                                                      y=-self.win.size[1]/4, visible=True, z=_getTextLayer(self.win))
        else:
            self.eye_image_title.text = text
            self.eye_image_title.visible = True


    def setup_image_display(self, width, height):
        if self.verbose: print("setup_image_display", width, height)
        ''' set up the camera image display

        return 1 to request high-resolution camera image'''
        self._size = [width, height]
        self.clear_cal_display()
        self._rgb_index_array = np.zeros((int(height/2), int(width/2)), dtype=np.uint8)

        return 1


    def set_image_palette(self, r, g, b):
        if self.verbose: print("set_image_palette", len(r))
        ''' Sets color palette used by Host PC when sending images
        Saves all rgb values on that palette. Then for each eye image frame, 
        the eyelnk just sends the palette index for each pixel.
        '''
        sz = len(r)
        self._rgb_palette = np.zeros((sz, 3), dtype=np.uint8)
        i=0
        while i < sz:
            self._rgb_palette[i, :] = [int(r[i]), int(g[i]), int(b[i])]
            i = i + 1


    def draw_image_line(self, width, line, totlines, buff):
        if self._rgb_index_array.shape[1] != width: # because different size of the 2 camera views
            self._rgb_index_array = np.zeros((totlines, width), dtype=np.uint8)
        for i in range(width):
            try: self._rgb_index_array[line-1, i] = buff[i]
            except Exception:
               print('Failed to draw pixel to image line %d %d'%(line-1, i))
        if line == totlines:
            #if self.verbose: print("draw_image_line", width, totlines)
            try:
                image = Image.fromarray(self._rgb_index_array,
                                           mode='P')
                image.putpalette(self._rgb_palette)
                image = ImageOps.fit(image, self.eye_image_size) #MD
                image_array = np.array(image.convert('RGB'))

                if self.eye_image is None:
                    self.eye_image = self.win.Stimulus(size=self.eye_image_size, anchor=Shady.LOCATION.CENTER, position=[0., 0.], visible=False, z=_getEyeImageLayer(self.win))
                self.eye_image.LoadTexture(image_array)
                self.eye_image.visible = True
                self._meta_draw_cross_hair()

            except: pass


    def exit_image_display(self):
        ''' exit the camera image display'''
        self.clear_cal_display()


    def get_mouse_state(self):
        if self.verbose: print("get_mouse_state", self.win.mouse_x, self.win.mouse_y, self.win.mouse_anypress)
        ''' get mouse position and any mouse button press and rescales to image
        apparently will call draw_line of coords > 0
        '''
        x = self.win.mouse_x + self.win.size[0]/2 # eyelink coords
        y = - self.win.mouse_y + self.win.size[1]/2
        x = x * self.eye_image_size[0]/self.win.size[0]/2 # cam image / eyelink coords
        y = y * self.eye_image_size[1]/self.win.size[1]/2
        return ((x, y), self.win.mouse_anypress)


    def draw_line(self, x1, y1, x2, y2, colorindex):
        if self.verbose: print("draw line", x1, x2, y1, y2, colorindex)
        if self.eye_image_size[0] > 192:
            x1 = int((float(x1) / 192) * self.eye_image_size[0])
            x2 = int((float(x2) / 192) * self.eye_image_size[0])
            y1 = self.eye_image_size[1] - int((float(y1) / 160) * self.eye_image_size[1])
            y2 = self.eye_image_size[1] - int((float(y2) / 160) * self.eye_image_size[1])
        if True not in [x < 0 for x in [x1, x2, y1, y2]]:
            self.cross_hair_lines[colorindex].append([x1, y1])
            self.cross_hair_lines[colorindex].append([x2, y2])


    def draw_lozenge(self, x, y, width, height, colorindex):
        ''' used to draw search limits on HEAD view
        colorindex always 5 (not 4)
        implemented a lazy circle version that takes average width and height as diameter
        cf. draw_lozenge() of SR research pygame/psychopy example for exact implementation
        '''
        if self.verbose: print("draw_lozenge", x, y, width, height)
        if self.eye_image_size[0] > 192:
            x = int((float(x) / 192) * self.eye_image_size[0])
            y = self.eye_image_size[1] - int((float(y) / 160) * self.eye_image_size[1])
            width = int((float(width) / 192) * self.eye_image_size[0])
            height = int((float(height) / 160) * self.eye_image_size[1])
        radius = np.mean((width, height))/2.
        nSides, lw = 30, 2

        center_pos = [x+radius, y-radius]
        self.cross_hair_lines[-5] = radius*Shady.ComplexPolygonBase(nSides, joined=True) + [center_pos[0]+1j*center_pos[1]]


    def alert_printf(self, msg):
        print(msg)

    def record_abort_hide(self):
        '''This function is called if aborted'''
        pass

def demo():
    """ Short script to illustrate usage
    We connect to the tracker, open a Shady window, and then configure the
    graphics environment for calibration. Then, perform a calibration, 
    disconnects from the tracker and get eyetracker file.
    """

    # connect to the tracker
    el_tracker = pylink.EyeLink()

    # open an EDF data file on the Host PC
    el_tracker.openDataFile('test.edf')

    # open a Shady window
    background_color = (0.5, 0.5, 0.5)
    win = Shady.World(screen=2, canvas=True, backgroundColor=background_color)

    # send over a command to let the tracker know the correct screen resolution
    scn_coords = "screen_pixel_coords = 0 0 %d %d" % (win.size[0], win.size[1])
    el_tracker.sendCommand(scn_coords)

    # Instantiate a graphics environment (genv) for calibration
    genv = CalibrationGraphics(el_tracker, win)

    # Set target color and size (these are actually the default)
    genv.setCalibrationColor((0, 0, 0))
    genv.setCalibrationSize(32)

    # Beeps to play during calibration, validation, and drift correction
    # parameters: target, good, error
    # Each parameter could be ''--default sound, 'off'--no sound, or a wav file
    genv.setCalibrationSounds('', '', '')

    # reduces calibration area
    el_tracker.sendCommand('calibration_area_proportion %2.1f %2.1f'%(0.5, 0.5))
    el_tracker.sendCommand('validation_area_proportion %2.1f %2.1f'%(0.5, 0.5))

    # Request Pylink to use the graphics environment (genv) we customized above
    pylink.openGraphicsEx(genv)

    # calibrates the tracker
    el_tracker.doTrackerSetup() 

    # close the data file and transfers it from the eyelink Host PC
    el_tracker.closeDataFile()
    el_tracker.receiveDataFile('test.edf', os.path.join(os.getcwd(), 'test.edf'))

    # disconnect from the tracker
    el_tracker.close()

    #close window
    win.Close()



if __name__ == '__main__':
    demo()
