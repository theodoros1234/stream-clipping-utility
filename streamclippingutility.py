#!/bin/python3
# This Python file uses the following encoding: utf-8
import sys
from PySide2.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel, QPushButton, QKeySequenceEdit, QSpinBox, QCheckBox, QSystemTrayIcon, QMenu


# Main window class
class MainWindow(QWidget):
    # Create window
    def __init__(self):
        super().__init__()

        # Main window layout
        self.resize(360,320)
        self.setWindowTitle("Stream Clipping Utility")
        self.mainLayout = QVBoxLayout(self)
        self.setLayout(self.mainLayout)

        # Login label
        self.mainLayout.addWidget(QLabel("<b>Step 1:</b> Login",self))
        # Login layout
        self.loginStatus = QLabel("Not logged in",self)
        self.loginLayout = QHBoxLayout(self)
        self.mainLayout.addWidget(self.loginStatus)
        self.mainLayout.addLayout(self.loginLayout)
        # Login options
        self.retryButton = QPushButton("Retry",self)
        self.retryButton.setVisible(False)
        self.loginButton = QPushButton("Login",self)
        self.loginLayout.addWidget(self.retryButton)
        self.loginLayout.addWidget(self.loginButton)
        self.loginLayout.addStretch()

        # Options label
        self.mainLayout.addWidget(QLabel("<b>Step 2:</b> Options",self))
        # Options layout
        self.optionsLayout = QFormLayout(self)
        self.mainLayout.addLayout(self.optionsLayout)
        # Options
        self.keyComboSelect = QKeySequenceEdit(self)
        self.clipLength = QSpinBox(self)
        self.clipNotif = QCheckBox("Show notification on successful clip")
        self.errorNotif = QCheckBox("Show notification on error",self)
        self.optionsLayout.addRow(self.tr("Key Combination Trigger:"),self.keyComboSelect)
        self.optionsLayout.addRow(self.tr("Clip length (seconds):"),self.clipLength)
        self.optionsLayout.addRow(self.clipNotif)
        self.optionsLayout.addRow(self.errorNotif)

        # Button Layout
        self.buttonLayout = QHBoxLayout(self)
        self.mainLayout.addStretch()
        self.mainLayout.addLayout(self.buttonLayout)
        # Buttons
        self.statusButton = QPushButton("Start",self)
        self.hideButton = QPushButton("Minimize to Tray",self)
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.statusButton)
        self.buttonLayout.addWidget(self.hideButton)
        
        # System tray icon
        #self.trayIcon = QSystemTrayIcon(self)
        #self.trayMenu = QMenu(self)
        #self.trayIcon.show()


# Main function
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
