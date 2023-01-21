
# === START_CONFIG_PARAMETERS ===

dict(

    timeout         = 5,
    
    info = dict(
        name        = 'Max Threads',
        version     = [1, 0, 0],
        description = 'Returns the maximum number of possible threads to create with the configurable stack size.',
        author      = 'JC`zic',
        mail        = 'jczic.bos@gmail.com',
        www         = 'https://github.com/jczic'
    ),
    
    args = dict(

        stack_size  = dict( label    = 'Choose the stack size for each thread:',
                            type     = dict,
                            items    = dict( _4  = "4 Kbytes",
                                             _6  = "6 Kbytes",
                                             _8  = "8 Kbytes",
                                             _10 = "10 Kbytes",
                                             _16 = "16 Kbytes" ) )
    
    )

)

# === END_CONFIG_PARAMETERS ===


from _thread import stack_size, start_new_thread
from time    import sleep

def _threadProcess() :
    sleep(3)

stack_size_kb   = int(args.stack_size[1:])
save_stack_size = stack_size(stack_size_kb * 1024)
count           = 1 # One thread already created by ESP32 MPY-Jama

while True :
    try :
        start_new_thread(_threadProcess, ())
        count += 1
    except :
        break;

stack_size(save_stack_size)

print('Maximum number of threads allowed (with %sKb stack) --> %s' % (stack_size_kb, count))
