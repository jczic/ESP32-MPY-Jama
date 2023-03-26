
# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 2,
    
    info = dict(
        name        = 'GPIO Input',
        version     = [1, 0, 0],
        description = ''' Simple reader of low/high voltage signals on a GPIO (pin) input.
                          You can enable an internal pull resistor or not.
                      ''',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),

    args = dict(

        pin     = dict( label    = 'GPIO:',
                        type     = list ),

        pull    = dict( label    = 'Internal pull resistor:',
                        type     = dict,
                        items    = { 'NONE'      : 'No resistor used',
                                     'PULL_UP'   : 'Use PULL-UP resistor',
                                     'PULL_DOWN' : 'Use PULL-DOWN resistor' } )

        )

)

# === END_CONFIG_PARAMETERS ===


from machine import Pin
from time    import sleep

pull = ( eval('Pin.' + args.pull) if args.pull != 'NONE' else None )

try :
    pin = Pin(args.pin, mode=Pin.IN, pull=pull)
except ValueError as ex :
    print('Error: The selected GPIO-%s is invalid.' % args.pin)
    import sys
    sys.exit()

print('Input on GPIO-%s works, click the red button to stop the Jama Func.' % args.pin)
sleep(1)

print('')
last_signal = None
while True :
    if pin() != last_signal :
        sleep(0.030)
        signal = pin()
        if signal != last_signal :
            print('Signal: %s' % ('HIGH' if pin() else 'LOW'))
            last_signal = signal
    sleep(0.001)
