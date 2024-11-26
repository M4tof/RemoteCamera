import time
from LCD import LCD

# Initialize the LCD with specific parameters: Raspberry Pi revision, I2C address, and backlight status
lcd = LCD(2, 0x27, True)  # Using Raspberry Pi revision 2 and above, I2C address 0x3f, backlight enabled

# Display messages on the LCD
lcd.message("NerdCave", 1)        # Display 'NerdCave!' on line 1
lcd.message("Tutorials", 2)    # Display '    - Tutoarials' on line 2

# Keep the messages displayed for 5 seconds
time.sleep(5)

# Clear the LCD display
lcd.clear()