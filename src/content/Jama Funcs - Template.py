

print("You could write MicroPython code before the configuration.")


# === START_CONFIG_PARAMETERS ===

dict(

    timeout = 2,    # Delay in seconds before showing the interrupt button to the user.
                    # A value of 0 will never display the button.
                    # It is not mandatory, the default value is 5 seconds.    

    info    = dict(
        # ----------------------------------------------------------------------
        name        = 'My template of Jama Funcs',              # Name is mandatory
        version     = [1, 0, 0],                                # Version is mandatory (list of 3 int)
        description =                                           # Description is mandatory
                      ''' This template is a guide to developing Jama Funcs in MicroPython for your ESP32 device.\
                          You just have a "dict" to place in your code file with the 2 commented lines above and below.\
                          You can create user inputs of several types (str, int, float, bool, list, dict) in order to retrieve them at runtime via the "args" class.
                          Use a "list" type to propose a choice between all the GPIO pins of the ESP32.
                          Also, use the "dict" type to propose a multiple choice via the "items" sub-tree.
                          You will be able to write your test scripts very quickly!
                      ''',
        author      = 'John Smith',                             # Author is mandatory
        mail        = 'john.smith@super-micropython-coders.io', # Mail is not mandatory
        www         = 'https://docs.micropython.org'            # Web link is not mandatory
        # ----------------------------------------------------------------------
    ),
    
    args    = dict(              # Label and type are mandatory
        # ----------------------------------------------------------------------
        my_first_arg_id    = dict( label    = 'Enter a text below:',
                                   type     = str,
                                   value    = "Test..."),  # This default value is not mandatory
        # ----------------------------------------------------------------------
        my_second_arg_id   = dict( label    = 'Enter an integer number below:',
                                   type     = int ),
                                   # You could add a default value (int)
        # ----------------------------------------------------------------------
        my_third_arg_id    = dict( label    = 'Choose a GPIO pin below:',
                                   type     = list,
                                   optional = True ),      # User can choose "No pin"
        # ----------------------------------------------------------------------
        my_fourth_arg_id   = dict( label    = 'Enter a float number below:',
                                   type     = float,
                                   value    = 123.456 ),   # This default value is not mandatory
        # ----------------------------------------------------------------------
        my_fifth_arg_id    = dict( label    = 'Choose a boolean value via the button below:',
                                   type     = bool ),
                                   # You could add a default value (True)
        # ----------------------------------------------------------------------
        my_sixth_arg_id    = dict( label    = 'Choose an option from the list below:',
                                   type     = dict,
                                   items    = dict( option1_id = "Select this first option",
                                                    option2_id = "Select this second option",
                                                    option3_id = "Select this third option" ),
                                   value    = 'option2_id' # This default value is not mandatory
                                 )
        # ----------------------------------------------------------------------
    )

)

# === END_CONFIG_PARAMETERS ===


print("You could write MicroPython code after the configuration.")


print()
print('* This code is executed on your ESP32 *')
print()
print('You have defined these parameters:')
print('  - args.my_first_arg_id   ->  %s' % args.my_first_arg_id)
print('  - args.my_second_arg_id  ->  %s' % args.my_second_arg_id)
print('  - args.my_third_arg_id   ->  %s' % args.my_third_arg_id)
print('  - args.my_fourth_arg_id  ->  %s' % args.my_fourth_arg_id)
print('  - args.my_fifth_arg_id   ->  %s' % args.my_fifth_arg_id)
print('  - args.my_sixth_arg_id   ->  %s' % args.my_sixth_arg_id)
print()
print('You can access all parameters from the "args" class.')
print('It\'s easy!')
print()

import os
print('For example, here are the contents of the root folder:\n%s' % os.listdir())
print('Bye')
