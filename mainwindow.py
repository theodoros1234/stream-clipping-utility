from PySide2.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel, QPushButton, QKeySequenceEdit, QSpinBox, QCheckBox, QSystemTrayIcon, QMenu, QErrorMessage
from PySide2.QtGui import QKeySequence, QIcon, Qt

# Main window class
class MainWindow(QWidget):
  # When closing window, 
  def closeEvent(self,event):
    self.trayIcon.hide()
  # Toggle window visibility
  def toggleWindow(self):
    self.setVisible(self.isHidden())
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
    self.config.values['key-combo']=seq
    self.keyComboSelect.setKeySequence(QKeySequence(seq))
    self.config.saveConfig()
    self.checkStartConditions()
  def clipLengthUpdate(self,val):
    self.config.values['clip-length'] = val
    self.config.saveConfig()
  def clipNotifUpdate(self,val):
    self.config.values['clip-notif'] = val
    self.config.saveConfig()
  def errorNotifUpdate(self,val):
    self.config.values['error-notif'] = val
    self.config.saveConfig()
  def trayOnStartupUpdate(self,val):
    self.config.values['tray-on-startup'] = val
    self.config.saveConfig()
  # Enables 'Start' button when appropriate conditions are met
  def checkStartConditions(self):
    self.startButton.setEnabled(self.config.values['key-combo']!="" and self.twitch.status==4)
  # Updates login status label
  def updateLoginStatus(self):
    retryEnable = False
    loginEnable = False
    cancelEnable = False
    logoutEnable = False
    loginText = ""
    if self.twitch.status==0:
      msg = "Not logged in"
      self.loginButton.setText("Login")
      loginEnable = True
    elif self.twitch.status==1:
      msg = "Logging in..."
      cancelEnable = True
    elif self.twitch.status==2:
      msg = "Waiting for response from browser..."
      cancelEnable = True
    elif self.twitch.status==3:
      self.loginButton.setText("Switch user")
      retryEnable = True
      loginEnable = True
      logoutEnable = True
      if self.twitch.error==0:
        msg = "Could not connect to Twitch servers, check your internet connection."
      elif self.twitch.error==1:
        msg = "Invalid response received from server."
      elif self.twitch.error==2:
        msg = "Connection cancelled."
      else:
        msg = "Unknown error occured."
    elif self.twitch.status==4:
      msg = "Logged in as " + self.twitch.username
      self.loginButton.setText("Switch user")
      loginEnable = True
      logoutEnable = True
    self.loginStatus.setText(msg)
    self.retryButton.setEnabled(retryEnable)
    self.loginButton.setEnabled(loginEnable)
    self.cancelButton.setEnabled(cancelEnable)
    self.logoutButton.setEnabled(logoutEnable)
    self.checkStartConditions()
  
  # Raises window
  def raiseTrigger(self):
    self.raise_()
    self.activateWindow()
  
  # Create window
  def __init__(self):
      super().__init__()
      self.config = None
      self.twitch = None
      
      # Main window layout
      self.appIcon = QIcon("icon.png")
      self.resize(380,420)
      self.setWindowTitle("Stream Clipping Utility")
      self.setWindowIcon(self.appIcon)
      self.mainLayout = QVBoxLayout(self)
      self.setLayout(self.mainLayout)

      # Login label
      self.mainLayout.addStretch()
      self.mainLayout.addWidget(QLabel("<b>Step 1:</b> Twitch Login",self))
      # Login layout
      self.loginStatus = QLabel("Please wait...",self)
      self.loginStatus.setWordWrap(True)
      self.loginLayout = QHBoxLayout(self)
      self.mainLayout.addWidget(self.loginStatus)
      self.mainLayout.addLayout(self.loginLayout)
      # Login options
      self.loginButton = QPushButton("Login",self)
      self.logoutButton = QPushButton("Logout",self)
      self.retryButton = QPushButton("Retry",self)
      self.cancelButton = QPushButton("Cancel",self)
      self.loginButton.setEnabled(False)
      self.logoutButton.setEnabled(False)
      self.retryButton.setEnabled(False)
      self.cancelButton.setEnabled(False)
      self.loginLayout.addWidget(self.loginButton)
      self.loginLayout.addWidget(self.logoutButton)
      self.loginLayout.addWidget(self.retryButton)
      self.loginLayout.addWidget(self.cancelButton)
      self.loginLayout.addStretch()

      # Options label
      self.mainLayout.addStretch()
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
      self.startButton = QPushButton("Start",self)
      self.hideButton = QPushButton("Minimize to Tray",self)
      self.startButton.setEnabled(False)
      self.buttonLayout.addStretch()
      self.buttonLayout.addWidget(self.startButton)
      self.buttonLayout.addWidget(self.hideButton)
      
      # System tray icon
      self.trayIcon = QSystemTrayIcon(self)
      self.trayIcon.setIcon(self.appIcon)
      self.trayIcon.show()
      
      # System tray menu
      self.trayMenu = QMenu(self)
      
      # Config error message dialog
      self.configErrorDialog = QErrorMessage(self)
  
  # Slots and signals
  def initSlots(self):
    self.loginButton.released.connect(self.twitch.login)
    self.logoutButton.released.connect(self.twitch.logout)
    self.retryButton.released.connect(self.twitch.retry)
    self.cancelButton.released.connect(self.twitch.cancel)
    
    self.keyComboSelect.editingFinished.connect(self.keySequenceUpdate)
    self.clipLength.valueChanged.connect(self.clipLengthUpdate)
    self.clipNotif.toggled.connect(self.clipNotifUpdate)
    self.errorNotif.toggled.connect(self.errorNotifUpdate)
    self.trayOnStartup.toggled.connect(self.trayOnStartupUpdate)
    
    self.hideButton.released.connect(self.hide)
    self.trayIcon.activated.connect(self.toggleWindow)

  # Updates GUI when configuration file is loaded
  def onConfigLoad(self):
    self.keyComboSelect.setKeySequence(QKeySequence(self.config.values["key-combo"]))
    self.clipLength.setValue(self.config.values["clip-length"])
    self.clipNotif.setChecked(self.config.values["clip-notif"])
    self.errorNotif.setChecked(self.config.values["error-notif"])
    self.trayOnStartup.setChecked(self.config.values["tray-on-startup"])
