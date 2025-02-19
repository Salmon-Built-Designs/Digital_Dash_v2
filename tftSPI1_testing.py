#!/usr/bin/python

import Image
import ImageDraw
import ImageFont
import glob
import redis
import signal
import sys

#import Adafruit_BBIO.ADC as ADC
import time
import datetime

import Adafruit_ILI9341 as TFT
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import Adafruit_BBIO.PWM as PWM
from time import sleep

# BeagleBone Black configuration.
DC = 'P9_15'
RST = 'P9_12'
SPI_PORT = 2
SPI_DEVICE = 0
sensor_pin = 'P9_40'

#Connect to redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# Create TFT LCD display class.
disp = TFT.ILI9341(DC, rst=RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))

# Initialize display.
disp.begin()

# Alternatively can clear to a black screen by calling:
disp.clear()

# Get a PIL Draw object to start drawing on the display buffer.
draw = disp.draw()

# Start PWM pin for  backlight
PWM.start("P9_14", 0)

############################
## Functions
##
##

#Signal handler for controlled process shutdown
def signal_term_handler(signal, frame):
    #print 'got SIGTERM'
    #Reduce the duty cycle of the backlight PWM pin in steps to fade out
    duty_cycle = 100
    while duty_cycle > 0:
        duty_cycle -= 1
        PWM.set_duty_cycle("P9_14", duty_cycle)
        sleep(0.01)
    sys.exit(0)

# Define a function to create rotated text.  Unfortunately PIL doesn't have good
# native support for rotated fonts, but this function can be used to make a 
# text image and rotate it so it's easy to paste in the buffer.
def draw_rotated_text(image, text, position, angle, font, fill=(255,0,0)):
	# Get rendered font width and height.
	draw = ImageDraw.Draw(image)
	width, height = draw.textsize(text, font=font)
        height=int(height*(1+0.8))
	# Create a new image with transparent background to store the text.
	textimage = Image.new('RGBA', (width, height), (0,0,0,0))
	# Render the text.
	textdraw = ImageDraw.Draw(textimage)
	textdraw.text((0,0), text, font=font, fill=fill)
	# Rotate the text image.
	rotated = textimage.rotate(angle, expand=1)
	# Paste the text into the image, using it as a mask for transparency.
	image.paste(rotated, position, rotated)

#Setup the analog pins
#ADC.setup()


##############################
##
## Main Loop
##

#Loop forever reading data from Redis and displaying the value on the screen
duty_cycle = 0
while True:
    #Fade in backlight until it reaches 100%
    if duty_cycle < 100:
        duty_cycle += 10
        PWM.set_duty_cycle("P9_14", duty_cycle)
    #Take time stamp at the begining of the loop
    start_time = time.time()
    #Grab the speed from redis
    speed = r.get('speed')
    #Draw bar at top of screen
    draw.rectangle((0, 0, 40, 320), outline=(100,100,100), fill=(100,100,100))
    #Draw white line under gray bar
    draw.line((40, 0, 40, 320), fill=(255,255,255))
    draw.line((41, 0, 41, 320), fill=(255,255,255))
    draw.line((42, 0, 42, 320), fill=(255,255,255))
    #Draw the speed value with a custom font
    font = ImageFont.truetype('/home/ubuntu/Digital_Dash_v2/fonts/ArialBold.ttf', 140)
    draw_rotated_text(disp.buffer, str(speed), (40, 100), 90, font, fill=(255,255,255))
    #Draw mph text with a smaller font
    font = ImageFont.truetype('/home/ubuntu/Digital_Dash_v2/fonts/ArialBold.ttf', 40)
    draw_rotated_text(disp.buffer, str('mph'), (90, 10), 90, font, fill=(255,255,255))
    #Draw time
    datestring = datetime.datetime.now().strftime("%I:%M%p").lower()
    font = ImageFont.truetype('/home/ubuntu/Digital_Dash_v2/fonts/ArialBold.ttf', 20)
    draw_rotated_text(disp.buffer, datestring, (210, 120), 90, font, fill=(255,255,255))
    #Draw Temperature
    tempval = '54' + chr(176)
    font = ImageFont.truetype('/home/ubuntu/Digital_Dash_v2/fonts/ArialBold.ttf', 20)
    draw_rotated_text(disp.buffer, tempval, (210, 10), 90, font, fill=(255,255,255))
    #Take time stamp before we start drawing on the TFT screen
    ###start_time = time.time()
    draw.line((200, 0, 200, 320), fill=(255,0,0))
    draw.line((201, 0, 201, 320), fill=(255,0,0))
    draw.line((202, 0, 202, 320), fill=(255,0,0))
    #Draw the new screen on the TFT display
    disp.display()
    #Take time stamp after drawing has completed.
    end_time = time.time()
    #sleep(0.25)
    disp.clear()
    #Calculate the difference between the two times.
    #This tells us how long it took to draw the TFT screen. 
    ####print 'DIFF: ' + str(end_time - start_time)
    signal.signal(signal.SIGTERM, signal_term_handler)


