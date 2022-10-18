import sys
import os
import serial
import webbrowser
import esptool
import json

from datetime import datetime
from PyQt5.QtCore import QUrl, Qt, QThread, QObject, pyqtSignal, pyqtSlot, QSettings, QTimer, QSize, QIODevice
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from PyQt5.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QComboBox, QWidget, QCheckBox, QRadioButton, \
    QButtonGroup, QFileDialog, QProgressBar, QLabel, QMessageBox, QDialogButtonBox, QGroupBox, QFormLayout
from gui import HLayout, VLayout, GroupBoxH, GroupBoxV, SpinBox, dark_palette
from termcolor import colored, cprint

class StdOut(object):
    def __init__(self, processor):
        self.processor = processor

    def write(self, text):
        self.processor(text)

    def flush(self):
        pass

class ESPWorker(QObject):
    finished = pyqtSignal()
    port_error = pyqtSignal(str)

    def __init__(self, port, doErase):
        super().__init__()
        self.port = port
        self.doErase = doErase
        self.partitions_file = os.getcwd() + "\\partitions.bin"
        self.bootloader_file = os.getcwd() + "\\bootloader.bin"
        self.firmware_file = os.getcwd() + "\\firmware.bin"

    @pyqtSlot()
    def execute(self):
        command_base = ["--chip", "esp32", "--port", self.port, "--baud", "115200", "--before",  "default_reset",  "--after", "hard_reset"]
        command_write = ["write_flash", "-z", "--flash_mode", "dio", "--flash_size", "detect", "--verify", "0x1000",  self.bootloader_file, "0x8000",  self.partitions_file, "0x10000", self.firmware_file]

        command_erase = ["erase_flash"]
        command = command_base
        if self.doErase:
            command += command_erase
        else:
            command += command_write
        # print("Using command: ", command)
        try:
            esptool.main(command)
            self.finished.emit()
        except Exception as e:
        # except esptool.FatalError or serial.SerialException as e:
            self.port_error.emit("{}".format(e))

class SendConfigDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(640)
        self.setWindowTitle("Send wifi configuration to device")
        self.commands = None
        self.module_mode = 0
        self.createUI()

    def createUI(self):
        vl = VLayout()
        self.setLayout(vl)
        # Wifi groupbox
        self.gbWifi = QGroupBox("WiFi")
        self.gbWifi.setCheckable(False)
        flWifi = QFormLayout()
        self.leAP = QLineEdit()
        self.leAPPwd = QLineEdit()
        self.leAPPwd.setEchoMode(QLineEdit.Password)
        flWifi.addRow("SSID", self.leAP)
        flWifi.addRow("Password", self.leAPPwd)
        self.gbWifi.setLayout(flWifi)
        vl_wifis = VLayout(0)
        vl_wifis.addWidgets([self.gbWifi])
        hl_wifis_mqtt = HLayout(0)
        hl_wifis_mqtt.addLayout(vl_wifis)
        vl.addLayout(hl_wifis_mqtt)
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

    def accept(self):
        ok = True

        if (len(self.leAP.text()) == 0 or len(self.leAPPwd.text()) == 0):
            ok = False
            QMessageBox.warning(self, "WiFi details incomplete", "Input WiFi SSID and Password")
        if ok:
            x = {"ssid": self.leAP.text(), "password": self.leAPPwd.text() }
            self.commands = json.dumps(x)
            print (self.commands)
            self.done(QDialog.Accepted)


class Flasher(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESP32 Flasher 1.2")
        self.setMinimumWidth(480)
        self.mode = 0  # BIN file
        self.release_data = b""
        self.createUI()
        self.refreshPorts()
        self.jsonStart = False
        self.jsonBuffer = ""

    def createUI(self):
        vl = VLayout()
        self.setLayout(vl)

        # Port groupbox
        gbPort = GroupBoxH("Select port", 3)
        self.cbxPort = QComboBox()
        pbRefreshPorts = QPushButton("Refresh")
        gbPort.addWidget(self.cbxPort)
        gbPort.addWidget(pbRefreshPorts)
        gbPort.layout().setStretch(0, 4)
        gbPort.layout().setStretch(1, 1)

        # Buttons
        self.pbFlash = QPushButton("Flash!")
        self.pbFlash.setFixedHeight(50)
        self.pbFlash.setStyleSheet("background-color: #223579;")
        self.pbErase = QPushButton("Erase!")
        self.pbErase.setFixedHeight(50)
        self.pbErase.setStyleSheet("background-color: #223579;")
        self.pbConfig = QPushButton("Setup WIFI")
        self.pbConfig.setStyleSheet("background-color: #571054;")
        self.pbConfig.setFixedHeight(50)
        self.pbQuit = QPushButton("Quit")
        self.pbQuit.setStyleSheet("background-color: #c91017;")
        self.pbQuit.setFixedSize(QSize(50, 50))
        hl_btns = HLayout([50, 3, 50, 3])
        hl_btns.addWidgets([self.pbFlash, self.pbErase, self.pbConfig, self.pbQuit])
        vl.addWidgets([gbPort])
        vl.addLayout(hl_btns)
        pbRefreshPorts.clicked.connect(self.refreshPorts)
        self.pbFlash.clicked.connect(self.start_flash_process)
        self.pbErase.clicked.connect(self.start_erase_process)
        self.pbConfig.clicked.connect(self.send_config)
        self.pbQuit.clicked.connect(self.reject)

    def refreshPorts(self):
        self.cbxPort.clear()
        ports = reversed(sorted(port.portName() for port in QSerialPortInfo.availablePorts()))
        for p in ports:
            port = QSerialPortInfo(p)
            self.cbxPort.addItem(port.portName(), port.systemLocation())

    def send_config(self):
        dlg = SendConfigDialog()
        if dlg.exec_() == QDialog.Accepted:
            if dlg.commands:
                try:
                    self.serial = QSerialPort(self.cbxPort.currentText())
                    self.serial.setBaudRate(115200)
                    self.serial.open(QIODevice.ReadWrite)
                    self.serial.readyRead.connect(self.on_serial_read)
                    bytes_sent = self.serial.write(bytes(dlg.commands, 'utf8'))
                except Exception as e:
                    QMessageBox.critical(self, "COM Port error", e)
            else:
                QMessageBox.information(self, "Done", "Nothing to send")

    def on_serial_read(self):
        self.process_bytes(bytes(self.serial.readAll()))

    def process_bytes(self, bs):
        text = bs.decode('ascii')
        # print("!Received: " + text)
        try:
            for b in text:
                if b == '{':  # start json
                    self.jsonStart = True
                    # print("start JSON")
                if self.jsonStart == True:
                    self.jsonBuffer += b
                if b == '}':  # end json
                    self.jsonStart = False
                    # print("found JSON")
                    print(self.jsonBuffer)
                    obj = json.loads(self.jsonBuffer)
                    url = "http://" + obj["IP"]
                    print("Device IP: {0} ".format(url))
                    txt = "******* Use admin/{0} to enter configuration page *******".format(obj["ApPassword"])
                    print(txt)
                    webbrowser.get().open(url)
                    self.serial.close()
                    
        except Exception as e:
            print(colored("JSON error", "red"), e)

    def doneWithESPWorker(self):
        cprint("Flash completed!", "green")
        self.espthread.quit()
        self.espthread.wait(2000)

    def error(self, e):
        print(colored("\nConnect error:\n", "red"), e)
        self.espthread.quit()
        self.espthread.wait(2000)

    def run_esptool(self, doErase):
        self.espthread = QThread()
        self.espworker = ESPWorker(self.cbxPort.currentText(), doErase)
        self.espworker.port_error.connect(self.error)
        self.espworker.finished.connect(self.doneWithESPWorker)
        self.espworker.moveToThread(self.espthread)
        self.espthread.started.connect(self.espworker.execute)
        self.espthread.start()

    def start_flash_process(self):
        print(colored("\n********* You may need to press the Boot button for a few seconds to start the flashing process *********\n", "red"))
        self.run_esptool(False)

    def start_erase_process(self):
        print(colored("\n********* You may need to press the Boot button for a few seconds to start the erase process *********\n", "red"))
        self.run_esptool(True)

    def mousePressEvent(self, e):
        self.old_pos = e.globalPos()

    def mouseMoveEvent(self, e):
        delta = e.globalPos() - self.old_pos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = e.globalPos()

def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    app.setQuitOnLastWindowClosed(True)
    app.setStyle("Fusion")
    app.setPalette(dark_palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")
    app.setStyle("Fusion")
    mw = Flasher()
    mw.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
