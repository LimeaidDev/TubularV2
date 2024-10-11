import os
import shutil
import subprocess
import sys
import winreg as reg
from xml.sax.expatreader import version

import win32com.client
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon

class InstallerApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon())

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Tubular Installer')
        self.setGeometry(100, 100, 300, 150)

        # Center the window
        qr = self.frameGeometry()  # Get the window's geometry
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()  # Get the center of the screen
        qr.moveCenter(cp)  # Move the window's center to the screen's center
        self.move(qr.topLeft())  # Move the window to the top-left of the new rectangle

        self.label = QtWidgets.QLabel('Click to Install:', self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)

        self.file_label = QtWidgets.QLabel('', self)
        self.file_label.setAlignment(QtCore.Qt.AlignCenter)

        self.install_button = QtWidgets.QPushButton('Install', self)
        self.install_button.clicked.connect(self.install_files)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.file_label)
        self.layout.addWidget(self.install_button)

        self.setLayout(self.layout)

    def get_resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def create_shortcut(self):
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        shortcut_path = os.path.join(desktop, 'Tubular.lnk')
        target_path = r'C:\Program Files\Tubular\Tubular.exe'
        wsh = win32com.client.Dispatch("WScript.Shell")
        shortcut = wsh.CreateShortcut(shortcut_path)
        shortcut.TargetPath = target_path
        shortcut.WorkingDirectory = r'C:\Program Files\Tubular'
        shortcut.IconLocation = target_path
        shortcut.save()

    def create_system_wide_start_menu_shortcut(self):
        system_start_menu = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs'
        shortcut_path = os.path.join(system_start_menu, 'Tubular.lnk')
        target_path = r'C:\Program Files\Tubular\Tubular.exe'
        wsh = win32com.client.Dispatch("WScript.Shell")
        shortcut = wsh.CreateShortcut(shortcut_path)
        shortcut.TargetPath = target_path
        shortcut.WorkingDirectory = r'C:\Program Files\Tubular'
        shortcut.IconLocation = target_path
        shortcut.save()

    def install_files(self):
        src_dir = self.get_resource_path('files')  # Get the bundled resource path
        dest_dir = r'C:\Program Files\Tubular'

        # Ensure the destination directory exists
        try:
            os.makedirs(dest_dir, exist_ok=True)
        except PermissionError:
            QtWidgets.QMessageBox.critical(self, 'Error', 'Permission denied! Run as administrator.')
            return

        # Copy files from the source directory to the destination
        try:
            for item in os.listdir(src_dir):
                s = os.path.join(src_dir, item)
                d = os.path.join(dest_dir, item)

                if os.path.isdir(s):
                    self.file_label.setText(f'Copying directory: {d}')
                    shutil.copytree(s, d, False, None)
                else:
                    self.file_label.setText(f'Copying file: {d}')
                    shutil.copy2(s, d)

            # Define the registry key and values
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Tubular"
            display_name = "Tubular"
            uninstall_string = r'"C:\Program Files\Tubular\uninstall.bat"'
            install_location = r'"C:\Program Files\Tubular"'
            publisher = "limeade"
            icon_path = r"C:\Program Files\Tubular\tubular.ico"
            version = "1.1"

            try:
                key = reg.CreateKey(reg.HKEY_LOCAL_MACHINE, key_path)
                reg.SetValueEx(key, "DisplayName", 0, reg.REG_SZ, display_name)
                reg.SetValueEx(key, "UninstallString", 0, reg.REG_SZ, uninstall_string)
                reg.SetValueEx(key, "InstallLocation", 0, reg.REG_SZ, install_location)
                reg.SetValueEx(key, "Publisher", 0, reg.REG_SZ, publisher)
                reg.SetValueEx(key, "DisplayIcon", 0, reg.REG_SZ, icon_path)
                reg.SetValueEx(key, "DisplayVersion",0, reg.REG_SZ, version)
                reg.CloseKey(key)
                print("Registry entry created successfully.")
            except Exception as e:
                print(f"Failed to create registry entry: {e}")

            # Create the shortcut
            self.create_shortcut()
            self.create_system_wide_start_menu_shortcut()

            QtWidgets.QMessageBox.information(self, 'Success', f'Files installed to {dest_dir}')
            sys.exit()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Failed to install files: {str(e)}')

def main():
    app = QtWidgets.QApplication(sys.argv)
    installer = InstallerApp()
    installer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
