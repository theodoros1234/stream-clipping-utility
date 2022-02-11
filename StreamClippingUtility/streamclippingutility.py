#!/bin/python3
# This Python file uses the following encoding: utf-8
import sys
from PySide2.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel, QPushButton, QKeySequenceEdit, QSpinBox


# Main window class
class MainWindow(QWidget):
    # Create window
    def __init__(self):
        super().__init__()

        # Main window layout
        self.resize(480,480)
        self.setWindowTitle("Stream Clipping Utility")
        self.mainLayout = QVBoxLayout(self)
        self.setLayout(self.mainLayout)

        # Login label
        self.loginLabel = QLabel(self)
        self.loginLabel.setText("<b>Step 1:</b> Login")
        self.mainLayout.addWidget(self.loginLabel)
        # Login layout
        self.loginLayout = QFormLayout(self)
        self.mainLayout.addLayout(self.loginLayout)

        # Options label
        self.optionsLabel = QLabel(self)
        self.optionsLabel.setText("<b>Step 2:</b> Options")
        self.mainLayout.addWidget(self.optionsLabel)
        # Options layout
        self.optionsLayout = QFormLayout(self)
        self.mainLayout.addLayout(self.optionsLayout)
        # Options
        self.keyComboSelect = QKeySequenceEdit()
        self.clipLength = QSpinBox()
        self.optionsLayout.addRow(self.tr("Key Combination Trigger:"),self.keyComboSelect)
        self.optionsLayout.addRow(self.tr("Clip length (seconds):"),self.clipLength)

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


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
