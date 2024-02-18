'''
    Arducam programable zoom-lens controller.
    Copyright (c) 2019-4 Arducam <http://www.arducam.com>.
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
    OR OTHER DEALINGS IN THE SOFTWARE.
'''

import cv2 #sudo apt-get install python-opencv
import numpy as py
import os
import sys
import time
import argparse
from RpiCamera import Camera
from Focuser import Focuser
import curses
from datetime import datetime

auto_focus_map = []
auto_focus_idx = 0

class zoom_focus_data:
    def __init__(self):
        self.zoom = 0
        self.focus = 0

# Rendering status bar
def RenderStatusBar(stdscr):
    height, width = stdscr.getmaxyx()
    statusbarstr = "Generate autofocus configuration : 'f' key And Press 'q' to exit"
    stdscr.attron(curses.color_pair(3))
    stdscr.addstr(height-1, 0, statusbarstr)
    stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
    stdscr.attroff(curses.color_pair(3))
    
# Rendering description
def RenderDescription(stdscr):
    focus_desc      = "Focus    : Left and right keys for manual fine-tuning"
    zoom_desc       = "Zoom     : Up and down keys 10x zoom"
    motor_x_desc    = "MotorX   : 'w'-'s' Key"
    motor_y_desc    = "MotorY   : 'a'-'d' Key"
    ircut_desc      = "IRCUT    : Space"
    snapshot_desc   = "Snapshot : 'c' Key"
    Mode_desc       = "Mode     : 't' Key switch mode"

    desc_y = 1
    stdscr.addstr(desc_y + 1, 0, focus_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 2, 0, zoom_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 3, 0, motor_x_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 4, 0, motor_y_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 5, 0, ircut_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 7, 0, snapshot_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 8, 0, Mode_desc, curses.color_pair(1))

# Rendering  middle text
def RenderMiddleText(stdscr,k,focuser):
    # get height and width of the window.
    height, width = stdscr.getmaxyx()
    # Declaration of strings
    title = "Arducam Controller"[:width-1]
    subtitle = ""[:width-1]
    keystr = "Last key pressed: {}".format(k)[:width-1]
    
    # Obtain device infomation
    focus_value = "Focus    : {}".format(focuser.get(Focuser.OPT_FOCUS))[:width-1]
    zoom_value  = "Zoom     : {}".format(focuser.get(Focuser.OPT_ZOOM))[:width-1]
    motor_x_val = "MotorX   : {}".format(focuser.get(Focuser.OPT_MOTOR_X))[:width-1]
    motor_y_val = "MotorY   : {}".format(focuser.get(Focuser.OPT_MOTOR_Y))[:width-1]
    ircut_val   = "IRCUT    : {}".format(focuser.get(Focuser.OPT_IRCUT))[:width-1]   
    sysStatus   = "Mode     : {}".format("Adjust" if focuser.get(Focuser.OPT_MODE) else "Fix")
    zoom_val    = "Zoom     : {}x".format(auto_focus_idx+1)

    if k == 0:
        keystr = "No key press detected..."[:width-1]

    # Centering calculations
    start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)
    start_x_subtitle = int((width // 2) - (len(subtitle) // 2) - len(subtitle) % 2)
    start_x_keystr = int((width // 2) - (len(keystr) // 2) - len(keystr) % 2)
    start_x_device_info = int((width // 2) - (len("Focus    : 00000") // 2) - len("Focus    : 00000") % 2)
    start_y = int((height // 2) - 6)
    
    
    # Turning on attributes for title
    stdscr.attron(curses.color_pair(2))
    stdscr.attron(curses.A_BOLD)

    # Rendering title
    stdscr.addstr(start_y, start_x_title, title)

    # Turning off attributes for title
    stdscr.attroff(curses.color_pair(2))
    stdscr.attroff(curses.A_BOLD)

    # Print rest of text
    stdscr.addstr(start_y + 1, start_x_subtitle, subtitle)
    stdscr.addstr(start_y + 3, (width // 2) - 2, '-' * 4)
    stdscr.addstr(start_y + 5, start_x_keystr, keystr)
    # Print device info
    stdscr.addstr(start_y + 6, start_x_device_info, focus_value)
    stdscr.addstr(start_y + 7, start_x_device_info, zoom_value)
    stdscr.addstr(start_y + 8, start_x_device_info, motor_x_val)
    stdscr.addstr(start_y + 9, start_x_device_info, motor_y_val)
    stdscr.addstr(start_y + 10, start_x_device_info, ircut_val)
    stdscr.addstr(start_y + 12, start_x_device_info, sysStatus)
    stdscr.addstr(start_y + 11, start_x_device_info, zoom_val)

def parseKeyByMap(stdscr,k,focuser:Focuser,camera):
    global auto_focus_idx
    
    motor_step  = 5
    focus_step  = 5
    if k == ord('s'):
        focuser.set(Focuser.OPT_MOTOR_Y,focuser.get(Focuser.OPT_MOTOR_Y) + motor_step)
    elif k == ord('w'):
        focuser.set(Focuser.OPT_MOTOR_Y,focuser.get(Focuser.OPT_MOTOR_Y) - motor_step)
    elif k == ord('d'):
        focuser.set(Focuser.OPT_MOTOR_X,focuser.get(Focuser.OPT_MOTOR_X) - motor_step)
    elif k == ord('a'):
        focuser.set(Focuser.OPT_MOTOR_X,focuser.get(Focuser.OPT_MOTOR_X) + motor_step)
    elif k == ord('r'):
        focuser.set(Focuser.OPT_RESET,0x01)
    elif k == ord('t'):
        t = focuser.get(Focuser.OPT_MODE)
        focuser.set(Focuser.OPT_MODE,t^0x0001)
        focuser.waitingForFree()
    elif k == curses.KEY_UP:
        auto_focus_idx = (auto_focus_idx + 1)%10
        focuser.move(auto_focus_map[auto_focus_idx].focus, auto_focus_map[auto_focus_idx].zoom)
    elif k == curses.KEY_DOWN:
        auto_focus_idx   = (auto_focus_idx - 1)%10
        focuser.move(auto_focus_map[auto_focus_idx].focus, auto_focus_map[auto_focus_idx].zoom)
    elif k == curses.KEY_RIGHT:
        focuser.set(Focuser.OPT_FOCUS,focuser.get(Focuser.OPT_FOCUS) + focus_step)
    elif k == curses.KEY_LEFT:
        focuser.set(Focuser.OPT_FOCUS,focuser.get(Focuser.OPT_FOCUS) - focus_step)
    elif k == 32:
        focuser.set(Focuser.OPT_IRCUT,focuser.get(Focuser.OPT_IRCUT)^0x0001)
    elif k == ord('c'):
        #save image to file.
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        cv2.imwrite("image{}.jpg".format(formatted_time), camera.getFrame())
    elif k == ord('f') or k == ord('F'):
        genFocusMap(stdscr,focuser,camera)
        foucusMapLoad(stdscr,focuser,camera)

def genFocusMap(stdscr,focuser,camera):
    stdscr.clear()
    keystr = "Reproducing calibration ...."
    stdscr.addstr(0 + 5, 0, keystr)
    stdscr.refresh()
    focusMap = coarseAdjustment(focuser,camera,stdscr)
    focuser.write_map(focusMap)

    stdscr.clear()

def coarseAdjustment(focuser:Focuser,camera:Camera,stdscr):
    zoom_step = 200
    focus_step = 100
    focus_Map = [focuser.opts[Focuser.OPT_ZOOM]["MAX_VALUE"],
                 focuser.opts[Focuser.OPT_FOCUS]["MAX_VALUE"]]
    for i in range(0,10,1):
        focuser.set(Focuser.OPT_ZOOM,i*zoom_step)
        maxVal = 0
        curFocus = 0
        stdscr.clear()
        keystr = "Reproducing calibration ....{}0%".format(i)
        stdscr.addstr(0 + 2, 0, keystr)
        keystr = "zoom ....{}x".format(i+1)
        stdscr.addstr(0 + 3, 0, keystr)
        stdscr.refresh()
        for j in range(0,22,2):
            focuser.set(Focuser.OPT_FOCUS,j*focus_step)
            focuser.waitingForFree()
            time.sleep(0.01)
            image = camera.getFrame()
            img2gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
            imageVar = cv2.Laplacian(img2gray,cv2.CV_64F).var()
            if maxVal < imageVar:
                maxVal = imageVar
                curFocus = j*focus_step
            keystr = "focusing calibration ....{}".format(j)
            stdscr.addstr(0 + 4, 0, keystr)
            stdscr.refresh()
        curFocus = curFocus-focus_step  if curFocus-focus_step > 0 else 0
        [curr_focus_step,maxImgVar] = focusMapFine(camera,focuser,curFocus,stdscr)
        focus_Map.append(i*zoom_step)
        focus_Map.append(curr_focus_step)
    return focus_Map

def focusMapFine(camera:Camera,fcr:Focuser,beg,stdscr):
    maxVal = 0
    curFocus = 0
    end = fcr.opts[Focuser.OPT_FOCUS]["MAX_VALUE"]
    decCount = 0;
    keystr = "focusing .....begin: {} end: {}".format(beg,end)
    stdscr.addstr(0 + 6, 0, keystr)

    for i in range(beg,end,10):
        fcr.set(Focuser.OPT_FOCUS,i)
        fcr.waitingForFree()
        time.sleep(0.5)
        image = camera.getFrame()
        img2gray = cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)
        imageVar = cv2.Laplacian(img2gray,cv2.CV_64F).var()
        if maxVal < imageVar:
            maxVal = imageVar
            curFocus = i
            decCount = 0
        else:
            decCount += 1
            if decCount >= 21:
                break
            # stdscr.clear()
        keystr = "focus step: {},value :{}".format(i,imageVar)
        stdscr.addstr(0 + 7, 0, keystr)
        stdscr.refresh()
    return curFocus,maxVal

def focusReset(i2c_bus):
    focuser = Focuser(i2c_bus)
    # focuser.set(Focuser.OPT_ZOOM,0)
    # focuser.set(Focuser.OPT_FOCUS,0)
    return focuser

def foucusMapLoad(stdscr,focuser,camera):
    global auto_focus_map
    data = focuser.read_map()
    if data[0] == 0xffff:
        focuser.set(Focuser.OPT_MODE,0x01)
        time.sleep(3)
        genFocusMap(stdscr,focuser,camera)
        foucusMapLoad(stdscr,focuser,camera);
    else:
        focuser.opts[Focuser.OPT_ZOOM]["MAX_VALUE"] = data[0]
        focuser.opts[Focuser.OPT_FOCUS]["MAX_VALUE"] = data[1]
        
        for i in range(2,len(data),2):
            t = zoom_focus_data()
            t.zoom = data[i]
            t.focus = data[i+1]
            auto_focus_map.append(t)

def draw_menu_focus_map(stdscr, camera:Camera, i2c_bus):
    focuser = focusReset(i2c_bus)
    # auto_focus = AutoFocus(focuser,camera)
    # auto_focus = None
    if focuser.driver_version() >= 0x104:
        foucusMapLoad(stdscr,focuser,camera)
    else :
        print("firmware version too low!")
        sys.exit(0)
        
    k = 0
    cursor_x = 0
    cursor_y = 0

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

    # Loop where k is the last character pressed
    while (k != ord('q')):
        # Initialization
        stdscr.clear()
        # Flush all input buffers. 
        curses.flushinp()
        # get height and width of the window.
        height, width = stdscr.getmaxyx()
        # parser input key
        parseKeyByMap(stdscr,k,focuser,camera) 

        # Rendering some text
        whstr = "Width: {}, Height: {}".format(width, height)
        stdscr.addstr(0, 0, whstr, curses.color_pair(1))

        # render key description
        RenderDescription(stdscr)
        # render status bar
        RenderStatusBar(stdscr)
        # render middle text
        RenderMiddleText(stdscr,k,focuser)
        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        k = stdscr.getch()


def main():

    #open camera
    camera = Camera()
    #open camera preview

    camera.start_preview(1280,720)
    time.sleep(1)
    curses.wrapper(draw_menu_focus_map, camera, 1)

    camera.stop_preview()
    camera.close()

if __name__ == "__main__":
    main()