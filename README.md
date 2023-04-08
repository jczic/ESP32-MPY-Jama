<br />

<p align="center">
    <img src="/img/logo.png" width="100" title="ESP32 MPY-Jama">
</p>
<h1>
    <p align="center">
        ESP32 MPY-Jama<br />
        <br />
    </p>
</h1>

<h6>
    <p align="right">
        🔅 <a href="https://github.com/jczic/ESP32-MPY-Jama/releases/tag/v1.2.0" title="Version 1.2">What's new in version 1.2</a>
    </p>
</h6>

<p align="center">
    <img src="https://img.shields.io/github/v/release/jczic/ESP32-MPY-Jama?style=flat-square" title="Release">
    <img src="https://img.shields.io/github/license/jczic/ESP32-MPY-Jama?color=yellow&style=flat-square" title="License"><br />
    <img src="https://img.shields.io/badge/MacOS_arm64-Ok-green.svg?style=flat-square" title="MacOS arm64">
    <img src="https://img.shields.io/badge/MacOS_Intel_x86%2F64-Ok-green.svg?style=flat-square" title="MacOS Intel x86/64">
    <img src="https://img.shields.io/badge/Windows_64bits-Ok-green.svg?style=flat-square" title="Windows 64-bits">
    <img src="https://img.shields.io/badge/Linux-Ok-green.svg?style=flat-square" title="Linux">
</p>

<br />

<p align="justify">
    :small_orange_diamond: Welcome to <b>ESP32 MPY-Jama</b>, a powerful and versatile <b>cross-platform</b> tool, designed to simplify your development with <b>Espressif's ESP32</b> microcontrollers and <b>MicroPython</b>.<br />
    <br />
    :small_orange_diamond: The <b>lightweight IDE</b>, <b>file manager</b>, <b>terminal</b>, and <b>real-time dashboards</b> provide all the essential features you need to develop your <b>IoT projects</b> quickly and efficiently on <b>MacOS</b>, <b>Windows</b>, and <b>Linux</b>.<br />
    <br />
    :small_orange_diamond: With <b>startup settings</b> and <b>customizable features</b>, this tool can adapt to your workflow and preferences, making your coding experience seamless and enjoyable.
</p>

<p align="center">
    <img src="/img/screen-ide.png" width="700" title="ESP32 MPY-Jama">
</p>

<h4>
    <p align="center">
        MacOS on arm64   ▪️   MacOS on Intel x86/64   ▪️   Windows 64-bits
    </p>
</h4>

<p align="center">
    <a title="Download ESP32 MPY-Jama for MacOS" href="https://github.com/jczic/ESP32-MPY-Jama/releases/download/v1.2.0/ESP32.MPY-Jama.v1.2.0-macos-universal2.dmg"><img src="/img/btn-download-mac.png" width="250"></a>             
    <a title="Download ESP32 MPY-Jama for Windows" href="https://github.com/jczic/ESP32-MPY-Jama/releases/download/v1.2.0/ESP32.MPY-Jama.v1.2.0-win64.exe"><img src="/img/btn-download-win.png" width="250"></a>
</p>

<h4>
    <p align="center">
        To make it work under Linux :penguin: <a href="#linux" title="Instructions for Linux">click here</a>!
    </p>
</h4>

<br />

---

# :bookmark_tabs: &nbsp;Table of contents

- [**Real-time system dashboard**](#system-dashboard)
- [**Real-time networks dashboard**](#networks-dashboard)
- [**Wi-Fi in 2 clicks**](#wifi)
- [**Lightweight integrated IDE**](#ide-gpio)
- [**Embedded Jama Funcs**](#jama-funcs)
  - [**Already included**](#jama-funcs-table)
- [**SD card support**](#sd-card)
- [**Firmware upgrade**](#esptool)
- [**Build &amp; Run**](#build-and-run)
- [**Linux version instructions**](#linux)
- [**Author**](#author)
- [**Special thanks to**](#thanks)
- [**License**](#license)

<br />

---

<a name="system-dashboard"></a>
# :gear: &nbsp;Real-time system dashboard

Access all important <b>system information</b>, adjust the <b>MCU frequency</b>, monitor the <b>current status</b> of the <b>set GPIOs</b>,
check <b>startup configuration options</b> and display the <b>various partitions</b> of the flash memory.<br />
The <b>startup options</b> allow you to <b>save your configurations</b> on the board, so that you can always <b>maintain them</b> after each reboot.

<p align="center">
    <img src="/img/screen-system.png" width="700">
</p>

---

<a name="networks-dashboard"></a>
# :globe_with_meridians: &nbsp;Real-time networks dashboard

Configure and display information about <b>Wi-Fi connection</b> and <b>access point interfaces</b>,
set up a board with an integrated <b>Ethernet PHY interface</b> and verify that the <b>Internet connection</b> is available.<br />
It is also possible to <b>act on the state</b> of the network interfaces, including the one for <b>BLE</b>.

<p align="center">
    <img src="/img/screen-networks.png" width="700">
</p>

---

<a name="wifi"></a>
# :satellite: &nbsp;Wi-Fi in 2 clicks

Quickly <b>connect</b> your device to available <b>Wi-Fi networks</b> and set up an <b>access point</b> with ease.<br />
The <b>authentication options</b> and the <b>maximum number of clients</b> are adjustable.<br />
<br />

<p align="center">
    <img src="/img/screen-wifi-sta.png" height="280">   
    <img src="/img/screen-wifi-ap.png" height="280">
</p>

<br />

---

<a name="ide-gpio"></a>
# :desktop_computer: &nbsp;Lightweight integrated IDE

<b>Develop your MicroPython</b> programs and libraries and <b>test them</b> directly using the <b>lightweight IDE</b>.<br />
Also, <b>a terminal is usable</b> in the same window with the management of the <b>history of your commands</b> like a shell.<br />
<b>Manage and transfer content</b> from the device's <b>flash memory</b> or <b>SD card</b>.

<p align="center">
    <img src="/img/screen-coding.png" width="700">
</p>

<br />

In the code editor, <b>common keyboard shortcuts</b> such as <b>save</b>, <b>undo</b>, <b>search</b> or <b>move line blocks</b> are available.<br />
<b>Tips</b>: leave the mouse on a file to display its full name and size, or double-click on the tab bar to create one more quickly.<br />
<br />
Use <b>Espressif's pinout diagrams</b> for the <b>GPIOs</b>, which are available <b>on most boards</b>:

<p align="center">
    <img src="/img/screen-gpio-pinout.png" width="700">
</p>

---

<a name="jama-funcs"></a>
# :control_knobs: &nbsp;Embedded Jama Funcs

<b>Jama Funcs</b> are small <b>dedicated functions</b> that run <b>on your device</b> to perform a <b>specific task</b>.<br />
They can be used to <b>quickly test</b> the functionality of the <b>ESP32</b> or <b>external modules</b> and are designed to be <b>easily configured</b>.

<p align="center">
    <img src="/img/screen-jama-funcs.png" width="700">
</p>

<b>Choose a Jama Func</b> from those proposed, then <b>configure its parameters</b> directly <b>in the graphical interface</b> before executing it on your device:

<p align="center">
    <img src="/img/screen-jama-funcs-settings.png" width="700">
</p>

When <b>executing a Jama Func</b>, a window with a <b>terminal</b> opens up, allowing you to view <b>its output</b>:

<p align="center">
    <img src="/img/screen-jama-funcs-exec.png" width="700">
</p>

It is of course possible to <b>develop your own Jama Funcs</b> in order to <b>import them</b> into the interface and thus facilitate their use by implementing <b>integrated parameters</b>.<br />
You can find a <b>full template</b> in <b>MicroPython</b> directly in the software or by clicking on
<a href="https://github.com/jczic/ESP32-MPY-Jama/blob/ef2cf1cfbc138dd81a4291fe262d21fccb6dc71a/src/content/Jama%20Funcs%20-%20Template.py"><b>this link</b></a>.<br />
<br />
<a name="jama-funcs-table"></a>
The following table lists all the <b>Jama Funcs</b> already <b>included in ESP32 MPY-Jama</b>:<br />
<br />

|         Jama Func         | Description |
| ------------------------- | ----------- |
|**1-Wire Devices Scan**|Initializes a 1-Wire bus on a single GPIO and finds all the family IDs and serial numbers of slave devices.|
|**ADC Reader**| Simple level and voltage reader on a GPIO using an analog-to-digital converter (ADC). You can specify the dB applied attenuation and the bits resolution.|
|**BLE Scan**|Initializes the Bluetooth Low Energy radio and scans BLE devices via advertising data.|
|**BLE iBeacon**|Initializes the Bluetooth Low Energy radio and simulates an Apple iBeacon object. The advertising message broadcasts an UUID corresponding to "B.JAMA-FUNC.TEST" in binary with the short name "MPY-Jama" while the iBeacon is the response to an active scanner. The iBeacon (Apple beacon format) data are: Major = 123  /  Minor = 456  /  TX at 1 meter = -55 dB|
|**DAC Output**|Set a GPIO output to a specific voltage using digital-to-analog converter (DAC).|
|**GPIO Input**| Simple reader of low/high voltage signals on a GPIO (pin) input. You can enable an internal pull resistor or not.|
|**GPIO Output**|Set a GPIO (pin) output to ON or OFF.|
|**I2C Slaves Scan**|Initializes an I2C bus on two GPIO and scans it to find all the addresses of I2C slaves. You can choose the bus identifier, the SCL and SDA GPIO as well as the frequency in MHz.|
|**KT403A MP3 Player**|For MP3 modules based on KT403A chipset like DFPlayer, Grove-MP3 v2 and more. You will be able to connect your board via an UART bus, play all the sound files in loop from the intended storage source (microSD, USB, flash memory), adjust the volume but also choose an audio EQ effect (normal, pop, rock, jazz, classic, bass). Info: KT403A supports MP3 & WAV audio formats on FAT16 or FAT32 files system, 32 GB max for microSD.|
|**LEDs - DotStar RGB Strip**|Try your DotStar RGB LEDs via SPI bus, compatible with strips APA102, SK9822, and more. You can choose the number of LEDs as well as the bus connectivity settings and the lighting in full power or in fading rainbow. The embedded library can be found via the link below.|
|**LEDs - NeoPixel RBG(+W/Y) Strip**|Try your NeoPixel RGB(+W/Y) LEDs via only one GPIO, compatible with strips WS2812(B), SK6812, ADAxxxx, APA106, FLORA and more. You can choose the number as well as the type of LEDs like RGB or RGB+W/Y, the frequency, and the lighting in full power or in fading rainbow. The NeoPixel library was coded by Damien P. George.|
|**Magnet Sensor**|Allows to test the hall sensor of the ESP32 chip with detection of the two magnetic poles after automatic calibration.|
|**Max Threads**|Returns the maximum number of possible threads to create with the configurable stack size.|
|**Memory Check**|This little tool simply allows you to allocate a maximum amount of memory on your chip in order to force the writing on almost all the available slots.|
|**NTP Time Sync**| This tool synchronizes the UTC date and time from an NTP server. You can choose the NTP server host to connect to.|
|**PWM & Lighting**|Uses a PWM on a GPIO and varies its duty cycle to make a led flash smoothly from 0 to 3.3V.|
|**PWM & Servo Motor**| Uses a PWM on a GPIO and drives a servo motor by varying its duty cycle. Several options are available to configure the servo motor, such as pulse frequency, pulse width and rotation time.|
|**UART Test**| Initializes an UART bus on two GPIO, sends or not a custom command and receives data from the bus. You can choose bus identifier, baud rate, bits per character, parity, stop bits and TX/RX GPIO|
|**Wi-Fi Scan**|Performs a detailed scan of the wireless access points.|

<br />

<h3>
    <p align="center">
        You are welcome to share your own Jama Funcs! 😉
    </p>
</h3>

<br />

---

<a name="sd-card"></a>
# :file_folder: &nbsp;SD card support

If an <b>SD card</b> is available on the board, activate it and <b>mount</b> the corresponding <b>file system</b>.<br />
A <b>reformatting</b> of all content is also possible.

<p align="center">
    <img src="/img/screen-sdcard.png" width="700">
</p>

---

<a name="esptool"></a>
# :hammer_and_wrench: &nbsp;Firmware upgrade

Take advantage of the <b>Espressif esptool</b> to connect the device in <b>bootloader mode</b> and easily <b>load new binary images</b>.<br />
Additionally, the tool allows you to <b>completely erase the device</b> for a full reset.

<p align="center">
    <img src="/img/screen-esptool.png" width="700">
</p>

---

<a name="build-and-run"></a>
# :rocket: &nbsp;Build &amp; Run

- ### Required dependencies

  pyWebView ([Check out on GitHub](https://github.com/r0x0r/pywebview)):
  
  ```console
  python -m pip install pywebview
  ```

  pySerial ([Check out on GitHub](https://github.com/pyserial/pyserial)):
  
  ```console
  python -m pip install pyserial
  ```

- ### Run application
  
  Just use python:
  
  ```console
  python src/app.py
  ```

<br />

---

<a name="linux"></a>
# :penguin: &nbsp;Linux version instructions

This describes how to clone the repository and how to run from source. In the third step you will find instructions how to create a binary from source. All st
eps have been tested on Ubuntu 22.04, but should work with little changes on similar distributions as well.

- ### Installation

  First, First, make sure you have all the required files:

  ```bash
  # clone the repository:
  git clone https://github.com/jczic/ESP32-MPY-Jama

  # install python modules requirements:
  sudo apt install libcairo2-dev libgirepository1.0-dev python3-pyqt5 python3-pyqt5.qtwebengine python3-pyqt5.qtwebchannel libqt5webkit5-dev gir1.2-webkit2-4.0

  # initialize python venv:
  cd ESP32-MPY-Jama
  python3 -m venv venv

  . venv/bin/activate

  pip3 install wheel setuptools
  pip3 install pyserial pywebview[qt] pycairo PyGObject pyinstaller
  ```

- ### Running from source

  When you executed all steps listed under "Installation" you may run directly from sources by executing these steps:

  ```bash
  cd ESP32-MPY-Jama
  . venv/bin/activate
  python3 src/app.py
  ```
  
  In case of an issue with the initialization of the graphical user interface, it is possible to force the desired interface by using the argument `--gui` (or `-g`) followed by `qt` or `gtk`.

  ```bash
  # example:
  python3 src/app.py -g gtk
  ```

- ### Building executable

  Execute the steps listed under "Installation" and then continue like this:

  ```bash
  cd ESP32-MPY-Jama
  ./create_binary.sh
  ```

  When the script finishes you should end up with a "esp32-mpy-jama" executable in the "dist" subfolder.

<br />

---

<a name="author"></a>
# :wink: &nbsp;Author

  **Jean-Christophe Bos** (:fr:)
  - GitHub: *[@jczic](https://github.com/jczic)*
  - Email:  *<jczic.bos@gmail.com>*
  - Profil: *[LinkedIn](https://www.linkedin.com/in/jczic)*
  - Music:  *[SoundCloud](https://soundcloud.com/jczic/sets/electro-pulse)*
            *[Spotify](https://open.spotify.com/album/5fUd57GcAIcdUn9NX3fviG)*
            *[YouTube](https://www.youtube.com/playlist?list=PL9CsGuMbcLaU02VKS7jtR6LaDNpq7MZEq)*

<br />

---

<a name="thanks"></a>
# :+1: &nbsp;Special thanks to

  - **[rdagger](https://github.com/rdagger)** > [www.rototron.info](https://www.rototron.info)
  - **[happenpappen](https://github.com/happenpappen)** > [www.stop.pe](https://stop.pe)

<br />

---

<a name="license"></a>
# :eight_pointed_black_star: &nbsp;License

  - Copyright :copyright: 2023 [Jean-Christophe Bos](https://www.linkedin.com/in/jczic).
  - This project is [MIT](https://github.com/jczic/ESP32-MPY-Jama/blob/master/LICENSE.md) licensed.
