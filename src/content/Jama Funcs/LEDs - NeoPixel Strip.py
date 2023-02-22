
# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 1,

    info = dict(
        name        = 'LEDs - NeoPixel RBG(+W/Y) Strip',
        version     = [1, 0, 0],
        description = 'Try your NeoPixel RGB(+W/Y) LEDs via only one GPIO, compatible with strips WS2812(B), SK6812, ADA4xx6, APA106, FLORA and more. ' \
                    + 'You can choose the number as well as the type of LEDs like RGB or RGB+W/Y, the frequency, and the lighting in full ' \
                    + 'power or in fading rainbow. The NeoPixel library was coded by Damien P. George.',
        author      = 'JC`zic for the colors demo',
    ),

    args = dict(

        ledsCount  = dict( label = 'Number of LEDs:',
                           type  = int,
                           value = 1 ),

        pin        = dict( label = 'GPIO:',
                           type  = list ),

        ledType    = dict( label = 'Type of LEDs:',
                           type  = dict,
                           items = { '3' : 'Standard RGB (3 in 1)',
                                     '4' : 'Extended RGB+W/Y (4 in 1)' } ),

        fullPower  = dict( label = 'Set the lighting in full power:',
                           type  = bool ),

        frequency  = dict( label = 'Protocol frequency:',
                           type  = dict,
                           items = { '0' : '400 KHz > v1 (APA106, FLORA)',
                                     '1' : '800 KHz > v2' },
                           value = '1' ),

        reverseRGB = dict( label = 'Reversed RGB protocol (APA106, FLORA):',
                           type  = bool ) )

)

# === END_CONFIG_PARAMETERS ===


# ----------------------------------------------------------------------------

from machine import Pin
from time    import sleep

def setColor(red, green, blue, white=0, fading=False) :
    global np, r, g, b, w
    rStep = (red-r)   / speed
    gStep = (green-g) / speed
    bStep = (blue-b)  / speed
    wStep = (white-w) / speed
    while r != red or g != green or b != blue or w != white or not fading :
        if not fading :
            r = red
            g = green
            b = blue
            w = white
        else :
            if (r < red and rStep > 0) or (r > red and rStep < 0) :
                r += rStep
                if r < 0 or r > 255 :
                    r = red
            else :
                r = red
            if (g < green and gStep > 0) or (g > green and gStep < 0) :
                g += gStep
                if g < 0 or g > 255 :
                    g = green
            else :
                g = green
            if (b < blue and bStep > 0) or (b > blue and bStep < 0) :
                b += bStep
                if b < 0 or b > 255 :
                    b = blue
            else :
                b = blue
            if (w < white and wStep > 0) or (w > white and wStep < 0) :
                w += wStep
                if w < 0 or w > 255 :
                    w = white
            else :
                w = white
        for n in range(len(np)) :
            c = (round(r), round(g), round(b), round(w)) \
                if int(args.ledType) == 4 else           \
                (round(r), round(g), round(b))
            np[n] = c
        np.write()
        if not fading :
            break

# ------------------------------------------------------------------------------

if args.ledsCount < 1 or args.ledsCount > 1000 :
    print('The number of LEDs must be between 1 and 1000.')
    import sys
    sys.exit()

try :
    from neopixel import NeoPixel
    print('NeoPixel works, click the red button to stop the Jama Func.')
except :
    print('Unable to load the "neopixel" library. You must install it.')
    import sys
    sys.exit()

NeoPixel.ORDER = (0, 1, 2, 3) if args.reverseRGB else (1, 0, 2, 3)
np             = NeoPixel( pin    = Pin(args.pin),
                           n      = args.ledsCount,
                           bpp    = int(args.ledType),
                           timing = int(args.frequency) )
(r, g, b, w)   = (0.0, 0.0, 0.0, 0.0)
speed          = 70

try :

    if args.fullPower :
        setColor(255, 255, 255, 255);
        while True :
            sleep(1)
    else :
        while True :
            setColor(255, 0, 0, 0, True);
            setColor(0, 255, 0, 50, True);
            setColor(0, 0, 255, 100, True);
            setColor(255, 255, 0, 150, True);
            setColor(80, 0, 80, 100, True);
            setColor(0, 255, 255, 50, True);

except KeyboardInterrupt :
    c = (0, 0, 0, 0) if int(args.ledType) == 4 else (0, 0, 0)
    np.fill(c)
    np.write()
