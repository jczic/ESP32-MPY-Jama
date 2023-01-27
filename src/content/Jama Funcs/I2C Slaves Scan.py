
# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 2,
    
    info = dict(
        name        = 'I2C Slaves Scan',
        version     = [1, 0, 0],
        description = ''' Initializes an I2C bus on two GPIO and scans it to find all the addresses of I2C slaves.
                          You can choose the bus identifier, the SCL and SDA GPIO as well as the frequency in MHz.
                      ''',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),
    
    args = dict(

        bus     = dict( label    = 'I2C bus:',
                        type     = dict,
                        items    = { '0' : 'Bus 0',
                                     '1' : 'Bus 1' } ),

        sclPin  = dict( label    = 'I2C SCL GPIO:',
                        type     = list ),

        sdaPin  = dict( label    = 'I2C SDA GPIO:',
                        type     = list ),

        freqMHz = dict( label    = 'I2C bus frequency in MHz:',
                        type     = int,
                        value    = 400 )
    
    )

)

# === END_CONFIG_PARAMETERS ===



from machine import I2C, Pin

if args.freqMHz > 0 and args.freqMHz <= 500 :
    try :
        i2c = I2C( int(args.bus),
                   scl  = Pin(args.sclPin),
                   sda  = Pin(args.sdaPin),
                   freq = args.freqMHz * 1000 )
        print('Scans the I2C bus...')
        devicesAddr = i2c.scan()
        if devicesAddr :
            for addr in devicesAddr :
                print('  - Slave found on address [%s]' % hex(addr))
        else :
            print('No I2C slave found.')
        del i2c
    except Exception as ex :
        print('I2C bus initialization error (%s).' % ex)
else :
    print('Error: The frequency must be between 1MHz and 500MHz.')
