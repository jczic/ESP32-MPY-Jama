

# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 10,
    
    info = dict(
        name        = 'Magnet Sensor',
        version     = [1, 0, 0],
        description = 'Allows to test the hall sensor of the ESP32 chip with detection of the two magnetic poles after automatic calibration.',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),
    
    args = None

)

# === END_CONFIG_PARAMETERS ===


from esp32 import hall_sensor
from time  import sleep

msr = 500
tlr = 25

def getMinMax() :
    _min = None
    _max = None
    for i in range(msr) :
        val = hall_sensor()
        if i == 0 :
            _min = val-tlr
            _max = val+tlr
        else :
            _min = min(_min, val-tlr)
            _max = max(_max, val+tlr)
    return _min, _max

print('Please do not bring any magnets near your device during the calibration process.')
sleep(3.5)
print()
for i in range(3) :
    print('...%s' % (3-i), end='')
    sleep(2)
print()

calMin, calMax = getMinMax()

print('Calibration ok!')
print()
print('You can now approach a magnet to your ESP32 chip in its different poles.')
print('(Click the red button to stop the Jama Func)')
print()

stat = 0
while True :
    _min, _max = getMinMax()
    if _max > calMax + tlr :
        if stat != 1 :
            stat = 1
            print('> POSITIVE MAGNETIC POLE [+++]')
    elif _min < calMin - tlr :
        if stat != -1 :
            stat = -1
            print('> NEGATIVE MAGNETIC POLE [---]')
    elif stat != 0 :
        stat = 0
        print('> NO MAGNET')
    sleep(0.030)
