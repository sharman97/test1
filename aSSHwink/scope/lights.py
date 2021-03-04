from rpi_ws281x import PixelStrip, Color
import argparse
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

class Lights():
    # LED st£rip configuration:
    LED_COUNT = 8  # Number of LED pixels.
    LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
    # LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
    LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA = 10  # DMA channel to use for generating signal (try 10)
    LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
    LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
    LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53


    BF_LED=11

    disp_r=True
    disp_g=True
    disp_b=True
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    init=False


    def __init__(self):
        if not Lights.init:
            print("Initing")
            Lights.init=True
            Lights.strip.begin()
            GPIO.setup(Lights.BF_LED, GPIO.OUT)
            for i in range(0, Lights.strip.numPixels()):
                Lights.strip.setPixelColor(i, Color(255,255,255))
            Lights.strip.show()



    def df(self,color):
        if color=='r':
            Lights.disp_r=not Lights.disp_r
        elif color =='g':
            Lights.disp_g = not Lights.disp_g
        elif color =='b':
            Lights.disp_b = not Lights.disp_b

        for i in range(0, Lights.strip.numPixels()):
            Lights.strip.setPixelColor(i, Color( int(Lights.disp_r)*255,int(Lights.disp_g)*255,int(Lights.disp_b)*255))
        Lights.strip.show()

    def bf(self):
        GPIO.output(Lights.BF_LED,int(not GPIO.input(Lights.BF_LED)))
