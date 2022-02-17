#!/bin/python3
# This Python file uses the following encoding: utf-8
import sys, os
from PySide2.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel, QPushButton, QKeySequenceEdit, QSpinBox, QCheckBox, QSystemTrayIcon, QMenu, QErrorMessage
from PySide2.QtGui import QKeySequence, QIcon


config = {}
default_client_id = "2ya1fhz3io1xhy9ao03ull3k8wwqff"

# Function that saves config file
def save_config():
  path = "app.config"
  try:
    config_file = open(path,'w')
    for item in config.items():
      # Write each line to the config file
      config_file.write("%s=%s\n"%(item[0],item[1]))
    config_file.close()
    print("Updated config file")
  except:
    # Show error message in case something goes wrong
    window.configErrorDialog.showMessage("Could not save configuration.")

# Main window class
class MainWindow(QWidget):
    # Make key sequence valid
    def keySequenceUpdate(self):
      seq = self.keyComboSelect.keySequence().toString().lower()
      prev_plus = False
      i=0
      for c in seq:
        if c=='+':
          prev_plus=True
        else:
          if (prev_plus==False) & (c==','):
            seq = seq[0:i]
            break
          prev_plus=False
        i+=1
      config['key-combo']=seq
      self.keyComboSelect.setKeySequence(QKeySequence(seq))
      save_config()
    def clipLengthUpdate(self,val):
      config['clip-length'] = int(val)
      save_config()
    def clipNotifUpdate(self,val):
      config['clip-notif'] = val
      save_config()
    def errorNotifUpdate(self,val):
      config['error-notif'] = val
      save_config()
    def trayOnStartupUpdate(self,val):
      config['tray-on-startup'] = val
      save_config()
    # Create window
    def __init__(self):
        super().__init__()

        # Main window layout
        self.appIcon = QIcon("icon.png")
        self.resize(360,320)
        self.setWindowTitle("Stream Clipping Utility")
        self.setWindowIcon(self.appIcon)
        self.mainLayout = QVBoxLayout(self)
        self.setLayout(self.mainLayout)

        # Login label
        self.mainLayout.addWidget(QLabel("<b>Step 1:</b> Twitch Login",self))
        # Login layout
        self.loginStatus = QLabel("Please wait...",self)
        self.loginLayout = QHBoxLayout(self)
        self.mainLayout.addWidget(self.loginStatus)
        self.mainLayout.addLayout(self.loginLayout)
        # Login options
        self.retryButton = QPushButton("Retry",self)
        self.loginButton = QPushButton("Login",self)
        self.retryButton.setEnabled(False)
        self.loginButton.setEnabled(False)
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
        self.clipLength.setRange(5,60)
        self.clipNotif = QCheckBox("Show notification on successful clip",self)
        self.errorNotif = QCheckBox("Show notification on error",self)
        self.trayOnStartup = QCheckBox("Minimize to tray on startup",self)
        self.optionsLayout.addRow(self.tr("Key Combination Trigger:"),self.keyComboSelect)
        self.optionsLayout.addRow(self.tr("Clip length (seconds):"),self.clipLength)
        self.optionsLayout.addRow(self.clipNotif)
        self.optionsLayout.addRow(self.errorNotif)
        self.optionsLayout.addRow(self.trayOnStartup)

        # Button Layout
        self.buttonLayout = QHBoxLayout(self)
        self.mainLayout.addStretch()
        self.mainLayout.addLayout(self.buttonLayout)
        # Buttons
        self.statusButton = QPushButton("Start",self)
        self.hideButton = QPushButton("Minimize to Tray",self)
        self.statusButton.setEnabled(False)
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.statusButton)
        self.buttonLayout.addWidget(self.hideButton)
        
        # System tray icon
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(self.appIcon)
        self.trayMenu = QMenu(self)
        
        # Config error message dialog
        self.configErrorDialog = QErrorMessage(self)
        
        # Slots
        self.keyComboSelect.editingFinished.connect(self.keySequenceUpdate)
        self.clipLength.textChanged.connect(self.clipLengthUpdate)
        self.clipNotif.toggled.connect(self.clipNotifUpdate)
        self.errorNotif.toggled.connect(self.errorNotifUpdate)
        self.trayOnStartup.toggled.connect(self.trayOnStartupUpdate)
        
        self.hideButton.released.connect(self.trayIcon.show)
        self.hideButton.released.connect(self.hide)
        
        self.trayIcon.activated.connect(self.show)
        self.trayIcon.activated.connect(self.trayIcon.hide)


# Function that loads a config file, and changes appropriate widgets on the main window to match the current configuration
def load_config(path):
  # Check if file exists before loading
  if os.path.exists(path):
    try:
      with open(path,'r') as config_file:
        print("Loading config file")
        # Go through each line, separate key from value, and store them in the config variable
        for line in config_file.readlines():
          separator_pos = line.find('=')
          # Skip invalid lines
          if separator_pos==-1:
            continue
          key = line[0:separator_pos].strip()
          value = line[separator_pos+1:].strip()
          config[key] = value
    except:
      # Show error dialog when there's an error loading the config file
      print("Error loading config file. Using default config.")
      window.configErrorDialog.showMessage("Error encountered while reading configuration info. Defaults will be used instead.")
  
  # Load default values for invalid or unset options
  if "client-id" in config:
    if config["client-id"] == "":
      config["client-id"] = default_client_id
  else:
    config["client-id"] = default_client_id
  if ("token" in config) == False:
    config["token"] = ""
  if ("key-combo" in config) == False:
    config["key-combo"] = ""
  if "clip-length" in config:
    try:
      config["clip-length"] = int(config["clip-length"])
    except:
      config["clip-length"] = 60
  else:
    config["clip-length"] = 60
  if "clip-notif" in config:
    if config["clip-notif"].lower() == "false":
      config["clip-notif"] = False
    else:
      config["clip-notif"] = True
  else:
    config["clip-notif"] = True
  if "error-notif" in config:
    if config["error-notif"].lower() == "false":
      config["error-notif"] = False
    else:
      config["error-notif"] = True
  else:
    config["error-notif"] = True
  if "tray-on-startup" in config:
    if config["tray-on-startup"].lower() == "true":
      config["tray-on-startup"] = True
    else:
      config["tray-on-startup"] = False
  else:
    config["tray-on-startup"] = False
  
  # Print config
  print("Loaded values:")
  for item in config.items():
    if item[0]=="token":
      print("token=%s"%('*'*len(item[1])))
    else:
      print("%s=%s"%(item[0],item[1]))
  print()
  
  # Change GUI elements to match loaded config
  window.keyComboSelect.setKeySequence(QKeySequence(config["key-combo"]))
  window.clipLength.setValue(config["clip-length"])
  window.clipNotif.setChecked(config["clip-notif"])
  window.errorNotif.setChecked(config["error-notif"])
  window.trayOnStartup.setChecked(config["tray-on-startup"])

# Main function
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    load_config("app.config")
    if config["tray-on-startup"]:
      window.trayIcon.show()
      window.trayIcon.showMessage("Stream Clipping Utility","Application has started hidden in tray.",window.appIcon)
    else:
      window.show()
    sys.exit(app.exec_())
