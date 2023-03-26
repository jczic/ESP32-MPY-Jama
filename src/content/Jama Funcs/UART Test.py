
# === START_CONFIG_PARAMETERS ===

dict(

    timeout = 7,

    info    = dict(
        # ----------------------------------------------------------------------
        name        = 'UART Test',
        version     = [1, 0, 0],
        description = ''' Initializes an UART bus on two GPIO, sends or not a custom command and receives data from the bus.
                          You can choose bus identifier, baud rate, bits per character, parity, stop bits and TX/RX GPIO.
                      ''',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
        # ----------------------------------------------------------------------
    ),
    
    args = dict(

        bus      = dict( label    = 'UART bus:',
                         type     = dict,
                         items    = { '1' : 'Bus 1',
                                      '2' : 'Bus 2' } ),

        baudrate = dict( label    = 'Baud rate (clock rate):',
                         type     = dict,
                         items    = { '110'     :       '110 bps',
                                      '220'     :       '220 bps',
                                      '300'     :       '300 bps',
                                      '1200'    :     '1 200 bps',
                                      '2400'    :     '2 400 bps',
                                      '4800'    :     '4 800 bps',
                                      '9600'    :     '9 600 bps',
                                      '19200'   :    '19 200 bps',
                                      '38400'   :    '38 400 bps',
                                      '57600'   :    '57 600 bps',
                                      '115200'  :   '115 200 bps',
                                      '230400'  :   '230 400 bps',
                                      '460800'  :   '460 800 bps',
                                      '921600'  :   '921 600 bps',
                                      '1843200' : '1 843 200 bps',
                                      '3686400' : '3 686 400 bps' },
                         value     = '115200' ),

        bits      = dict( label    = 'Number of bits per character:',
                          type     = dict,
                          items    = { '7' : '7 bits',
                                       '8' : '8 bits',
                                       '9' : '9 bits' },
                          value    = '8' ),

        parity    = dict( label    = 'Parity:',
                          type     = dict,
                          items    = { 'None' : 'None',
                                       '0'    : '0 (even)',
                                       '1'    : '1 (odd)' },
                          value    = 'None' ),

        stop      = dict( label    = 'Number of stop bits:',
                          type     = dict,
                          items    = { '1' : '1 bit',
                                       '2' : '2 bits' } ),

        txPin     = dict( label    = 'TX GPIO:',
                          type     = list ),

        rxPin     = dict( label    = 'RX GPIO:',
                          type     = list ),

        cmd       = dict( label    = 'Custom command to send (optional):',
                          type     = str )

    )

)

# === END_CONFIG_PARAMETERS ===



from machine import UART

try :
    uart = UART( int(args.bus),
                 baudrate = int(args.baudrate),
                 bits     = int(args.bits),
                 parity   = (int(args.parity) if args.parity != 'None' else None),
                 stop     = int(args.stop),
                 tx       = args.txPin,
                 rx       = args.rxPin,
                 timeout  = 5 * 1000 )
    print('UART bus initialized.')
    cmd = (args.cmd + '\n').encode()
    if not args.cmd or uart.write(cmd) == len(cmd) :
        if args.cmd :
            print('Command "%s" sent.' % args.cmd)
        print('Waiting for data...\n')
        ok = False
        while True :
            b = uart.read()
            if b :
                print(b.decode(), end='')
                ok = True
            else :
                if not ok :
                    print('No data received after sending your command.')
                break
    else :
        print('Error: Unable to write in the UART bus.')
except Exception as ex :
    print('UART bus initialization error (%s).' % ex)
