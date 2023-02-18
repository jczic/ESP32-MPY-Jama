
# === START_CONFIG_PARAMETERS ===

dict(
    
    info = dict(
        name        = 'GPIO Output',
        version     = [1, 0, 0],
        description = 'Set a GPIO (pin) output to ON or OFF.',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),

    args = dict(

        pin        = dict( label = 'GPIO:',
        type       = list ),

        OnOff      = dict( label = 'Set the GPIO to ON or OFF:',
        type       = bool,
        value      = True  ) )

)

# === END_CONFIG_PARAMETERS ===

from machine import Pin

Pin(args.pin, Pin.OUT, value=args.OnOff)
print('The GPIO output %s has been set to %s.' % (args.pin, ('ON (3v3)' if args.OnOff else 'OFF')))
