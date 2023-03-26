
# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 2,
    
    info = dict(
        name        = 'DAC Output',
        version     = [1, 0, 0],
        description = 'Set a GPIO output to a specific voltage using digital-to-analog converter (DAC).',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),

    args = dict(

        pin     = dict( label    = 'DAC GPIO:',
                        type     = list ),

        voltage = dict( label    = 'Voltage (0 - 3.3):',
                        type     = float )

        )

)

# === END_CONFIG_PARAMETERS ===


from machine import Pin, DAC

if args.voltage < 0 or args.voltage > 3.3 :
    print('Error: The voltage must be a decimal value between 0 and 3.3.')
else :
    try :
        dac = DAC(Pin(args.pin))
        dac.write(round(args.voltage * 255 // 3.3))
        print('The GPIO output %s has been set to %sV.' % (args.pin, round(args.voltage*100)/100))
    except ValueError as ex :
        print('Error: The selected GPIO-%s is invalid.' % args.pin)
