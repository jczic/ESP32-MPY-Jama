# <img src="/img/logo.png" width="75" valign="middle">   ESP32 MPY-Jama v1.2

#### <p align="justify">A powerful cross-platform tool that easily connects to and manages Espressif's ESP32 with MicroPython, providing a lightweight IDE, file manager, terminal, real-time dashboards, startup settings and customizable features for fast and efficient development on MacOS, Windows, and Linux.</p>

![Release](https://img.shields.io/github/v/release/jczic/ESP32-MPY-Jama?include_prereleases&color=success)
![Windows 64bits](https://img.shields.io/badge/Windows_64bits-Ok-green.svg)
![MacOS ARM64](https://img.shields.io/badge/MacOS_ARM64-Ok-green.svg)
![MacOS Intel x86_64](https://img.shields.io/badge/MacOS_Intel_x86__64-Ok-green.svg)
![License](https://img.shields.io/github/license/jczic/ESP32-MPY-Jama?color=yellow)

<br />
<p align="center">
    <img src="/img/screen-ide.png" width="850">
</p>

<h4>
    <p align="center">
        MacOS on arm64   ▪️   MacOS on Intel x86/64   ▪️   Windows 64-bits
    </p>
</h4>

<p align="center">
    <a href="https://github.com/jczic/ESP32-MPY-Jama/releases/download/v1.2.0/ESP32.MPY-Jama.v1.2.0-macos-universal2.dmg"><img src="/img/btn-download-mac.png" width="250"></a>             
    <a href="https://github.com/jczic/ESP32-MPY-Jama/releases/download/v1.2.0/ESP32.MPY-Jama.v1.2.0-win64.exe"><img src="/img/btn-download-win.png" width="250"></a>
</p>

<h4>
    <p align="center">
        To make it work under Linux :penguin: <a href="#linux">click here</a>!
    </p>
</h4>
<br />

---

## :cyclone: &nbsp;Access information dashboards instantly
<p align="center">
    <img src="/img/screen-networks.png" width="700">
</p>

---

## :cyclone: &nbsp;Connect to a Wi-Fi and create an access point in 2 clicks
<p align="center">
    <img src="/img/screen-wifi-sta.png" height="280">          
    <img src="/img/screen-wifi-ap.png" height="280">
</p>

---

## :cyclone: &nbsp;Install a new firmware on the flash very easily.
<p align="center">
    <img src="/img/screen-esptool.png" width="700">
</p>

---

## :cyclone: &nbsp;Embedded Jama Funcs

Run Jama Funcs on your device, choose from the ones offered and customize them with adjustable settings.
Develop and share yours with other users as well.
Get the MicroPython template file by clicking on the "template" button in the interface or by using <a href="https://github.com/jczic/ESP32-MPY-Jama/blob/ef2cf1cfbc138dd81a4291fe262d21fccb6dc71a/src/content/Jama%20Funcs%20-%20Template.py">this link</a>.

<p align="center">
    <img src="/img/screen-jama-funcs.png" width="700"><br />
    <br />
    You are welcome to send me your Jama Funcs! 😉<br />
    <br />
</p>

### Available Jama Funcs
| Name | Description |
| ---- | ----------- |
|1-Wire Devices Scan|Initializes a 1-Wire bus on a single GPIO and finds all the family IDs and serial numbers of slave devices.|
|ADC Reader| Simple level and voltage reader on a GPIO using an analog-to-digital converter (ADC). You can specify the dB applied attenuation and the bits resolution.|
|BLE Scan|Initializes the Bluetooth Low Energy radio and scans BLE devices via advertising data.|
|BLE iBeacon|Initializes the Bluetooth Low Energy radio and simulates an Apple iBeacon object. The advertising message broadcasts an UUID corresponding to "B.JAMA-FUNC.TEST" in binary with the short name "MPY-Jama" while the iBeacon is the response to an active scanner. The iBeacon (Apple beacon format) data are: Major = 123  /  Minor = 456  /  TX at 1 meter = -55 dB|
|DAC Output|Set a GPIO output to a specific voltage using digital-to-analog converter (DAC).|
|GPIO Input| Simple reader of low/high voltage signals on a GPIO (pin) input. You can enable an internal pull resistor or not.|
|GPIO Output|Set a GPIO (pin) output to ON or OFF.|
|I2C Slaves Scan|Initializes an I2C bus on two GPIO and scans it to find all the addresses of I2C slaves. You can choose the bus identifier, the SCL and SDA GPIO as well as the frequency in MHz.|
|KT403A MP3 Player|For MP3 modules based on KT403A chipset like DFPlayer, Grove-MP3 v2 and more. You will be able to connect your board via an UART bus, play all the sound files in loop from the intended storage source (microSD, USB, flash memory), adjust the volume but also choose an audio EQ effect (normal, pop, rock, jazz, classic, bass). Info: KT403A supports MP3 & WAV audio formats on FAT16 or FAT32 files system, 32 GB max for microSD.|
|LEDs - DotStar RGB Strip|Try your DotStar RGB LEDs via SPI bus, compatible with strips APA102, SK9822, and more. You can choose the number of LEDs as well as the bus connectivity settings and the lighting in full power or in fading rainbow. The embedded library can be found via the link below.|
|LEDs - NeoPixel RBG(+W/Y) Strip|Try your NeoPixel RGB(+W/Y) LEDs via only one GPIO, compatible with strips WS2812(B), SK6812, ADAxxxx, APA106, FLORA and more. You can choose the number as well as the type of LEDs like RGB or RGB+W/Y, the frequency, and the lighting in full power or in fading rainbow. The NeoPixel library was coded by Damien P. George.|
|Magnet Sensor|Allows to test the hall sensor of the ESP32 chip with detection of the two magnetic poles after automatic calibration.|
|Max Threads|Returns the maximum number of possible threads to create with the configurable stack size.|
|Memory Check|This little tool simply allows you to allocate a maximum amount of memory on your chip in order to force the writing on almost all the available slots.|
|NTP Time Sync| This tool synchronizes the UTC date and time from an NTP server. You can choose the NTP server host to connect to.|
|PWM & Lighting|Uses a PWM on a GPIO and varies its duty cycle to make a led flash smoothly from 0 to 3.3V.|
|PWM & Servo Motor| Uses a PWM on a GPIO and drives a servo motor by varying its duty cycle. Several options are available to configure the servo motor, such as pulse frequency, pulse width and rotation time.|
|UART Test| Initializes an UART bus on two GPIO, sends or not a custom command and receives data from the bus. You can choose bus identifier, baud rate, bits per character, parity, stop bits and TX/RX GPIO|
|Wi-Fi Scan|Performs a detailed scan of the wireless access points.|

---

<a name="build and run"></a>
## :rocket: &nbsp;Build &amp; Run

### Required

  - pyWebView ([Check out on GitHub](https://github.com/r0x0r/pywebview))
    ```console
    python -m pip install pywebview
    ```

  - pySerial ([Check out on GitHub](https://github.com/pyserial/pyserial))
    ```console
    python -m pip install pyserial
    ```

### Run
  
  - Just use python

    ```console
    python SRC/app.py
    ```

---

<a name="linux"></a>

## :penguin: &nbsp;Linux version instructions

This describes how to clone the repository and how to run from source. In the third step you will find instructions how to create a binary from source. All st
eps have been tested on Ubuntu 22.04, but should work with little changes on similar distributions as well.

### Installation

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

### Running from source

When you executed all steps listed under "Installation" you may run directly from sources by executing these steps:

```bash
cd ESP32-MPY-Jama
. venv/bin/activate
python3 src/app.py
```

### Building executable

Execute the steps listed under "Installation" and then continue like this:

```bash
cd ESP32-MPY-Jama
./create_binary.sh
```

When the script finishes you should end up with a "esp32-mpy-jama" executable in the "dist" subfolder.

---

<a name="author"></a>
## :wink: &nbsp;Author

  **Jean-Christophe Bos** (:fr:)
  - GitHub: *[@jczic](https://github.com/jczic)*
  - Email:  *<jczic.bos@gmail.com>*
  - Profil: *[LinkedIn](https://www.linkedin.com/in/jczic)*
  - Music:  *[SoundCloud](https://soundcloud.com/jczic/sets/electro-pulse)*
            *[Spotify](https://open.spotify.com/album/5fUd57GcAIcdUn9NX3fviG)*
            *[YouTube](https://www.youtube.com/playlist?list=PL9CsGuMbcLaU02VKS7jtR6LaDNpq7MZEq)*
---

<a name="thanks"></a>
## :+1: &nbsp;Special thanks to 

  - **[rdagger](https://github.com/rdagger)** > [www.rototron.info](https://www.rototron.info)
  - **[happenpappen](https://github.com/happenpappen)** > [www.stop.pe](https://stop.pe)

---

<a name="license"></a>
## :eight_pointed_black_star: &nbsp;License

  - Copyright :copyright: 2023 [Jean-Christophe Bos](https://www.linkedin.com/in/jczic).
  - This project is [MIT](https://github.com/jczic/ESP32-MPY-Jama/blob/master/LICENSE.md) licensed.

---

<br />
