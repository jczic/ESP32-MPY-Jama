
# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 1,
    
    info = dict(
        name        = 'PWM & Lighting',
        version     = [1, 0, 0],
        description = 'Uses a PWM on a GPIO and varies its duty cycle to make a led flash smoothly from 0 to 3.3V.',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),
    
    args = dict(

        ledPin  = dict( label = 'Led GPIO:',
                        type  = list ),

    )

)

# === END_CONFIG_PARAMETERS ===


from utime import sleep
from machine import Pin, PWM

_min = 0
_max = 2**16 - 1
step = 16

duty = _min
pin  = PWM( Pin(args.ledPin), freq=1000, duty=duty )

print('PWM on GPIO-%s works, click the red button to stop the Jama Func.' % args.ledPin)

while True:
    pin.duty_u16(duty)
    duty += step
    if duty >= _max:
        duty = _max
        step = -step
    elif duty <= 0:
        duty = 0
        step = -step
    sleep(0.0001)
