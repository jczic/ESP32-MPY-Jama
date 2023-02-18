
# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 1,

    info    = dict(
        # ----------------------------------------------------------------------
        name        = 'PWM & Servo Motor',
        version     = [1, 0, 0],
        description = ''' Uses a PWM on a GPIO and drives a servo motor by varying its duty cycle.
                          Several options are available to configure the servo motor, such as pulse frequency, pulse width and rotation time.   
                      ''',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
        # ----------------------------------------------------------------------
    ),
    
    args = dict(

        pin        = dict( label    = 'Signal wire GPIO:',
                           type     = list ),

        freqHz     = dict( label    = 'Pulse frequency (in hertz):',
                           type     = int,
                           value    = 50 ),

        minPulseUS = dict( label    = 'Minimum pulse width (in microseconds):',
                           type     = int,
                           value    = 544 ),

        maxPulseUS = dict( label    = 'Maximum pulse width (in microseconds):',
                           type     = int,
                           value    = 2400 ),

        rotateMS   = dict( label    = 'Maximum rotation time (in milliseconds):',
                           type     = int,
                           value    = 1000 )

    )

)

# === END_CONFIG_PARAMETERS ===


from machine import Pin, PWM
from time    import sleep

def setPWMDutyUS(pwm, dutyUS) :
    pwm.duty_ns(dutyUS * 1000)
    sleep(args.rotateMS / 1000)
    print('.', end='')

if args.freqHz > 0 and args.freqHz < 10000 :
    if args.minPulseUS < args.maxPulseUS :
        if args.rotateMS > 0 and args.rotateMS < 10000 :
            pwm = PWM(Pin(args.pin), freq=args.freqHz, duty=0)
            print('PWM on GPIO-%s works, click the red button to stop the Jama Func.' % args.pin)
            while True :
                setPWMDutyUS(pwm, args.minPulseUS)
                setPWMDutyUS(pwm, args.maxPulseUS)
        else :
            print('Error: maximum rotation time value is incorrect.')
    else :
        print('Error: minimum and maximum pulse width values are incorrect.')
else :
    print('Error: pulse frequency value is incorrect.')
