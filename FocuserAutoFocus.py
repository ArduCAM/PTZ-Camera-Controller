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
import json
from Focuser import Focuser
# from AutoFocus import AutoFocus
import curses

global image_count
image_count = 0
global camera_motor_step 
camera_motor_step = 20
# Rendering status bar
def RenderStatusBar(stdscr):
    height, width = stdscr.getmaxyx()
    statusbarstr = "Press 'q' to exit"
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
    desc_y = 1
    stdscr.addstr(desc_y + 1, 0, focus_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 2, 0, zoom_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 3, 0, motor_x_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 4, 0, motor_y_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 5, 0, ircut_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 7, 0, snapshot_desc, curses.color_pair(1))
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

auto_focus_map = None

def parseKeyByMap(stdscr,k,focuser:Focuser,auto_focus,camera):
    global image_count
    # global auto_focus_map
    motor_step  = 5
    # zoom_step= 32
    focus_step  = 1
    if k == ord('s'):
        focuser.set(Focuser.OPT_MOTOR_Y,focuser.get(Focuser.OPT_MOTOR_Y) + motor_step)
    elif k == ord('w'):
        focuser.set(Focuser.OPT_MOTOR_Y,focuser.get(Focuser.OPT_MOTOR_Y) - motor_step)
    elif k == ord('d'):
        focuser.set(Focuser.OPT_MOTOR_X,focuser.get(Focuser.OPT_MOTOR_X) - motor_step)
    elif k == ord('a'):
        focuser.set(Focuser.OPT_MOTOR_X,focuser.get(Focuser.OPT_MOTOR_X) + motor_step)
    if k == ord('r'):
        focuser.reset(Focuser.OPT_FOCUS)
        focuser.reset(Focuser.OPT_ZOOM)
    elif k == curses.KEY_UP:
        auto_focus   = auto_focus + 1  if auto_focus + 1 < 11 else 10
        focuser.set(Focuser.OPT_ZOOM,auto_focus * camera_motor_step)
        focuser.set(Focuser.OPT_FOCUS,auto_focus_map[str(auto_focus)])
        return auto_focus
    elif k == curses.KEY_DOWN:
        auto_focus   = auto_focus - 1  if auto_focus - 1 > 0 else 1
        focuser.set(Focuser.OPT_ZOOM,auto_focus * camera_motor_step)
        focuser.set(Focuser.OPT_FOCUS,auto_focus_map[str(auto_focus)])
        return auto_focus
    elif k == curses.KEY_RIGHT:
        focuser.set(Focuser.OPT_FOCUS,focuser.get(Focuser.OPT_FOCUS) + focus_step)
    elif k == curses.KEY_LEFT:
        focuser.set(Focuser.OPT_FOCUS,focuser.get(Focuser.OPT_FOCUS) - focus_step)
    elif k == 32:
        focuser.set(Focuser.OPT_IRCUT,focuser.get(Focuser.OPT_IRCUT)^0x0001)
    # elif k == 10:
    #     auto_focus.startFocus()
    #     # auto_focus.startFocus2()
    #     # auto_focus.auxiliaryFocusing()
    #     pass
    elif k == ord('c'):
        #save image to file.
        cv2.imwrite("image{}.jpg".format(image_count), camera.getFrame())
        image_count += 1
    elif k == ord('f') or k == ord('F'):
        genFocusMap(stdscr,focuser,camera)
    if(str(auto_focus) in auto_focus_map):
        with open("./record_log.json","a+") as dump_f:
            dump_f.write("{0}-{1}\n".format(str(auto_focus),auto_focus_map[str(auto_focus)]))

def genFocusMap(stdscr,focuser,camera):
    stdscr.clear()
    keystr = "Reproducing calibration ...."
    stdscr.addstr(0 + 5, 0, keystr)
    stdscr.refresh()
    focusMap = getFocusMap(focuser,camera,stdscr)
    with open("./record.json","w") as dump_f:
        json.dump(focusMap,dump_f)
    stdscr.clear()

def getFocusMap(focuser:Focuser,camera:Camera,stdscr):
    # zoom_step = 20000
    focus_step = 10
    focus_Map = {}
    for i in range(1,11,1):
        focuser.set(Focuser.OPT_ZOOM,i*camera_motor_step)
        maxVal = 0
        curFocus = 0
        for j in range(0,21,1):
            focuser.set(Focuser.OPT_FOCUS,j*focus_step)
            # sleep(1)
            focuser.waitingForFree()
            time.sleep(0.01)
            image = camera.getFrame()
            img2gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
            imageVar = cv2.Laplacian(img2gray,cv2.CV_64F).var()
            if maxVal < imageVar:
                maxVal = imageVar
                curFocus = j*focus_step
        stdscr.clear()
        keystr = "Reproducing calibration ....{}0%".format(i)
        stdscr.addstr(0 + 5, 0, keystr)
        stdscr.refresh()
        [curr_focus_step,maxImgVar] = focusMapFine(camera,focuser,curFocus)
        focus_Map[i]=curr_focus_step
    return focus_Map

def focusMapFine(camera:Camera,fcr:Focuser,max_laplacian_index):
    beg =  max_laplacian_index-10 if max_laplacian_index-10>0 else 0
    end = max_laplacian_index+10 if max_laplacian_index+10<200 else 200
    maxVal = 0
    for i in range(beg,end,1):
        fcr.set(Focuser.OPT_FOCUS,i)
        fcr.waitingForFree()
        time.sleep(0.1)
        
        image = camera.getFrame()
        img2gray = cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)
        imageVar = cv2.Laplacian(img2gray,cv2.CV_64F).var()
        if maxVal < imageVar:
            maxVal = imageVar
            curFocus = i
    return curFocus,maxVal

def focusReset(i2c_bus):
    focuser = Focuser(i2c_bus)
    focuser.set(Focuser.OPT_ZOOM,0)
    focuser.set(Focuser.OPT_FOCUS,0)
    return focuser,1
def foucusMapLoad(stdscr,focuser,camera):
    global auto_focus_map
    try:
        with open("./record.json","r") as load_f:
            auto_focus_map = json.load(load_f)
    except BaseException:
        genFocusMap(stdscr,focuser,camera)
        foucusMapLoad(stdscr,focuser,camera)

def draw_menu_focus_map(stdscr, camera:Camera, i2c_bus):
    focuser,zoom_idx = focusReset(i2c_bus)
    # auto_focus = AutoFocus(focuser,camera)
    # auto_focus = None
    foucusMapLoad(stdscr,focuser,camera)
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
        tmp = parseKeyByMap(stdscr,k,focuser,zoom_idx,camera) 
        if tmp != None :
            zoom_idx = tmp
        # Rendering some text
        whstr = "Width: {}, Height: {}".format(width, height)
        stdscr.addstr(0, 0, whstr, curses.color_pair(1))
        stdscr.addstr(9, 0, "Generate autofocus configuration : 'f' key", curses.color_pair(1))
        stdscr.addstr(10, 0, "Zoom :{}".format(zoom_idx), curses.color_pair(1))

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
    camera.start_preview()

    curses.wrapper(draw_menu_focus_map, camera, 1)

    camera.stop_preview()
    camera.close()

if __name__ == "__main__":
    main()
