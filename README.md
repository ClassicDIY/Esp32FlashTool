# EspFlashTool
Simple flash and wifi config tool for the ESP32 

[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2FClassicDIY%2FEspFlashTool&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://hits.seeyoufarm.com)

|If you find this project useful or interesting, please help support further development!|[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://paypal.me/classicdiy?country.x=CA&locale.x=en_US)|
|---|---|

[![GitHub All Releases](https://img.shields.io/github/downloads/ClassicDIY/EspFlashTool/total?style=for-the-badge)](https://github.com/ClassicDIY/EspFlashTool/releases)
[![GitHub](https://img.shields.io/github/license/ClassicDIY/EspFlashTool?style=for-the-badge)](https://github.com/ClassicDIY/EspFlashTool/blob/master/LICENSE)

Uses the ESPtool from Espressif under the hood, and all required settings by default.

Sends WIFI configuration to flashed device via serial.

The program will send a JSON message to the device with the SSID and WIFI Password entered by the user when they enter and save Setup WIFI.
When the ESP32 device is in AP mode, the code should be implemented to receive the wifi info JSON message.

example JSON message from flasher;

{"ssid":"MyRouterSSID", "password":"myWifiPassword"}

Once received, the device should connect to wifi using these credentials and return the following JSON message back to the flasher.

example JSON message from ESP32 device;

{"IP":"192.168.0.20", "ApPassword":"DeviceAPPassword"}

Once the flasher receives the response from the device, it will open the default browser at the given IP address to allow the user to complete the device setup.
The device's AP password can be displayed to the user in the flasher log window.
