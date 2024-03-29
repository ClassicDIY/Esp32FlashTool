# Esp32FlashTool
Simple flash and wifi config tool for the ESP32 

[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2FClassicDIY%2FEspFlashTool&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://hits.seeyoufarm.com)

<a href="https://www.buymeacoffee.com/r4K2HIB" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

[![GitHub All Releases](https://img.shields.io/github/downloads/ClassicDIY/EspFlashTool/total?style=for-the-badge)](https://github.com/ClassicDIY/EspFlashTool/releases)
[![GitHub](https://img.shields.io/github/license/ClassicDIY/EspFlashTool?style=for-the-badge)](https://github.com/ClassicDIY/EspFlashTool/blob/master/LICENSE)

Uses the ESPtool from Espressif under the hood with all required settings by default. It will look for the firmware.bin, partitions.bin and bootloader.bin files in the current directory, by creating a zip file that includes your bin files and the flasher executable for your Github Releases will give the user a convenient way to flash and setup the ESP with their Wifi credentials.

<p align="center">
    <img src=https://github.com/ClassicDIY/Esp32FlashTool/blob/master/Pictures/Flasher1.PNG>    
</p>

Flash!

esptool.py --port <COM#>  --baud "115200 --before default_reset --after hard_reset write_flash --flash_mode qio --flash_size detect 0x1000 bootloader.bin 0x8000 partitions.bin 0x10000 firmware.bin

Erase!

esptool.py --port <COM#>  --baud "115200 --before default_reset --after hard_reset erase_flash

Setup Wifi;

Sends WIFI configuration to flashed device via serial.

The program will send a JSON message to the device with the SSID and WIFI Password entered by the user when they enter and save Setup WIFI.
When the ESP32 device is in AP mode, your ESP device must implemented the code to receive the wifi info JSON message and configure Wifi.

example JSON message from flasher;

{"ssid":"MyRouterSSID", "password":"myWifiPassword"}

Once received, the device should connect to wifi using these credentials and return the following JSON message back to the flasher.

example JSON message from ESP32 device;

{"IP":"192.168.0.20", "ApPassword":"DeviceAPPassword"}

Once the flasher receives the response from the device, it will open the default browser at the given IP address to allow the user to complete the device setup.
The device's AP password can be displayed to the user in the flasher log window.
