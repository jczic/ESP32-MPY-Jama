
# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 2,

    info = dict(
        name        = 'ADC Reader',
        version     = [1, 0, 0],
        description = ''' Simple voltage reader on an ADC GPIO.
                          You can specify the dB applied attenuation and the bits resolution.
                      ''',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),
    
    args = dict(

        pin     = dict( label    = 'ADC GPIO:',
                        type     = list ),

        atten   = dict( label    = 'Input attenuation applied in dB:',
                        type     = dict,
                        items    = { 'ATTN_0DB'   : 'No attenuation (100mV - 950mV)',
                                     'ATTN_2_5DB' : '2.5 dB attenuation (100mV - 1250mV)',
                                     'ATTN_6DB'   : '6 dB attenuation (150mV - 1750mV)',
                                     'ATTN_11DB'  : '11 dB attenuation (150mV - 2450mV)' },
                        value    = 'ATTN_11DB' ),
    
        width   = dict( label    = 'Reading resolution in bits:',
                        type     = dict,
                        items    = { 'WIDTH_9BIT'  : '9 bits',
                                     'WIDTH_10BIT' : '10 bits',
                                     'WIDTH_11BIT' : '11 bits',
                                     'WIDTH_12BIT' : '12 bits' },
                        value    = 'WIDTH_12BIT' ),

    )

)

# === END_CONFIG_PARAMETERS ===


from machine import Pin, ADC
from time    import sleep

try :
    adc = ADC(Pin(args.pin, mode=Pin.IN))
except ValueError as ex :
    print('Error: The selected GPIO-%s is invalid.' % args.pin)
    import sys
    sys.exit()

adc.atten(eval('ADC.' + args.atten))
adc.width(eval('ADC.' + args.width))

print('ADC on GPIO-%s works, click the red button to stop the Jama Func.' % args.pin)
sleep(1)

print('')
while True :
    print('--------------------------')
    print('|  %7.3f%%  |  ~%1.3fv  |' % (adc.read_u16()*100/65535, adc.read_uv()/1000000))
    sleep(0.500)
