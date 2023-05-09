#
# Missile Launcher Code
#
import struct
import os
import sys
import platform
import time
import socket
import re
import json
import base64
import usb.core
import usb.util
from getch import getch, pause

# Protocol command bytes
DOWN    = 0x01
UP      = 0x02
LEFT    = 0x04
RIGHT   = 0x08
FIRE    = 0x10
STOP    = 0x20

DEVICE = None
DEVICE_TYPE = None

# Setup the Cannon
def setup_usb():
    global DEVICE 
    global DEVICE_TYPE

    DEVICE = usb.core.find(idVendor=0x2123, idProduct=0x1010)

    if DEVICE is None:
        DEVICE = usb.core.find(idVendor=0x0a81, idProduct=0x0701)
        if DEVICE is None:
            raise ValueError("Device not found")
        else:
            DEVICE_TYPE = "Original"
    else:
        DEVICE_TYPE = "Thunder"

    # On Linux we need to detach usb HID first
    if "Linux" == platform.system():
        try:
            DEVICE.detach_kernel_driver(0)
        except Exception as ex:
            pass # already unregistered    
    DEVICE.set_configuration()

# Control the LED light
# 1 -> on; 0 -> off
def missile_led(status):
    DEVICE.ctrl_transfer(0x21, 0x09, 0, 0, [0x03, status, 0x00,0x00,0x00,0x00,0x00,0x00])

# Send command
def missile_send_cmd(cmd):
    DEVICE.ctrl_transfer(0x21, 0x09, 0, 0, [0x02, cmd, 0x00,0x00,0x00,0x00,0x00,0x00])

# Send move command
def missile_send_move(cmd):
    if cmd == FIRE:
        time.sleep(0.5)
        missile_send_cmd(FIRE)
        time.sleep(4.5)
    else:
        missile_send_cmd(cmd)
        time.sleep(0.2)
        missile_send_cmd(STOP)

# Command mapping
def missile_get_command(key):
    mapping = {
        "UP": UP, 
        "LEFT": LEFT,
        "RIGHT": RIGHT,
        "DOWN": DOWN,
        "FIRE": FIRE
    }
    return mapping.get(key)






#
# Car Code
#

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)

# status: 1 -> move; 0 -> stop
def car_move(cmd, status):
    pin = car_get_command(cmd)
    GPIO.output(pin, bool(int(status)))

def car_get_command(key):
    mapping = {
        "LEFT": 11, 
        "RIGHT": 7,
        "FORWARD": 13,
        "BACK": 15
    }
    return mapping.get(key)





# 
# Flask Code
# 
from flask import Flask, render_template, request, json

app = Flask(__name__)

IS_MISSILE_LAUNCHER_READY = False

@app.before_first_request
def setup():
    # Set up USB drive for missile launcher
    try:
        setup_usb() 
        missile_led(1)
        global IS_MISSILE_LAUNCHER_READY
        IS_MISSILE_LAUNCHER_READY = True
        print("Missile launcher is ready")
    except Exception:
        print("Missile launcher cannot be initialized")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/car", methods=["POST"])
def car():
    data = json.loads(request.form.get("data"))
    cmd = data["value"]
    status = data["status"]
    car_move(cmd, status)  
    return "success"

@app.route("/missile", methods=["POST"])
def missile():
    data = json.loads(request.form.get("data"))
    cmd = missile_get_command(data["value"])
    if IS_MISSILE_LAUNCHER_READY:
        missile_send_move(cmd)
        return "success"
    return "failure"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

