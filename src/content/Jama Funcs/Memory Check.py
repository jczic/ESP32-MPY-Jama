

# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 15,
    
    info = dict(
        name        = 'Memory Check',
        version     = [1, 0, 0],
        description = 'This little tool simply allows you to allocate a maximum ' \
                    + 'amount of memory on your chip in order to force the writing '\
                    + 'on almost all the available slots.',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),
    
    args = None

)

# === END_CONFIG_PARAMETERS ===

import gc

def _sizeToText(size, unity) :
    if size >= 1024*1024 :
        return '%s M%s' % (round(size/1024/1024*100)/100, unity[0])
    if size >= 1024 :
        return '%s K%s' % (round(size/1024*100)/100, unity[0])
    return '%s %s' % (size, unity)

def _memFree() :
    gc.collect()
    return _sizeToText(gc.mem_free(), 'bytes')

array = [ ]
alloc = 10*1024
total = 0
print('Memory free before allocation: %s' % _memFree())
print()
print('Checking memory...', end='')
while alloc > 256 :
    try :
        while True :
            array.append(bytearray(alloc))
            total += alloc
    except :
        alloc = alloc // 2
        print('.', end='')
print()
print()
print('Total memory allocated:        %s' % _sizeToText(total, 'bytes'))
print('Memory free after allocation:  %s' % _memFree())
del array
print('Memory free after release:     %s' % _memFree())
