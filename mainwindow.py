from PySide2.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel, QPushButton, QKeySequenceEdit, QSpinBox, QCheckBox, QSystemTrayIcon, QMenu, QErrorMessage, QLineEdit, QFileDialog, QListWidget, QListWidgetItem
from PySide2.QtGui import QKeySequence, QIcon, QBrush, Qt
from queue import Queue
import random, time, threading, io, multiprocessing

# Main window class
class MainWindow(QWidget):
  # When closing window, 
  def closeEvent(self,event):
    self.trayIcon.hide()
    if self.started:
      self.start_stop()
  
  # Toggle window visibility
  def toggleWindow(self):
    self.setVisible(self.isHidden())
  
  # Update config value of key sequence when changed through the GUI
  def keySequenceUpdate(self):
    seq = self.keyComboSelect.keySequence().toString().lower()
    self.config.values['key-combo']=seq
    self.keyComboSelect.setKeySequence(QKeySequence(seq))
    self.config.save()
    self.checkStartConditions()
  
  # Updates config values when changed through the GUI
  def clipsEnabledUpdate(self,val):
    self.config.values['clips-enabled'] = val
    self.clipsFilePath.setEnabled(val)
    self.clipsFilePathBrowse.setEnabled(val)
    self.config.save()
    self.checkStartConditions()
  def markersEnabledUpdate(self,val):
    self.config.values['markers-enabled'] = val
    self.config.save()
    self.checkStartConditions()
  def clipLengthUpdate(self,val):
    self.config.values['clip-length'] = val
    self.config.save()
  def clipNotifUpdate(self,val):
    self.config.values['clip-notif'] = val
    self.config.save()
  def errorNotifUpdate(self,val):
    self.config.values['error-notif'] = val
    self.config.save()
  def trayOnStartupUpdate(self,val):
    self.config.values['tray-on-startup'] = val
    self.config.save()
  
  # Saves selected path to config and changes the appropriate GUI elements
  def clipsFilePathOpen(self,f):
    self.clipsFilePath.setText(f)
    self.config.values['clips-file-path'] = f
    self.config.save()
    self.checkStartConditions()
  
  # Enables 'Start' button when appropriate conditions are met
  def checkStartConditions(self):
    cnd_met = True
    
    if self.config.values['key-combo']=="" or self.twitch.status!=4:
      cnd_met = False
    if self.config.values['clips-enabled']==False and self.config.values['markers-enabled']==False:
      cnd_met = False
    
    self.startButton.setEnabled(cnd_met)
  
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
  
  def setStatus(self,label):
    self.status.setText(f"<b>Status:</b> {label}")
  
  def addStatusItem(self,label,color=None):
    item = QListWidgetItem(time.asctime()+' '+label, listview=self.statusList)
    if color != None:
      item.setForeground(QBrush(color))
    self.statusList.addItem(item)
    item.setSelected(True)
    time.sleep(0.016)
    max_pos = self.statusList.verticalScrollBar().maximum()
    self.statusList.verticalScrollBar().setValue(max_pos)
  
  # Updates status label with appropriate message.
  def updateStatus(self,event=0,data=""):
    # event=0: No special event
    # event=1: Clip is being created
    # event=2: Clip has successfully been created
    # event=3: Error while creating clip
    # event=4: Can't write to output folder
    message = None
    color = None
    if event==0:
      if self.started:
        message = "Listening for input."
      else:
        message = "Idle."
      self.setStatus(message)
    elif event==1:
      message = "Creating clip... "
      if self.config.values['clip-notif']:
        self.trayIcon.showMessage("Stream Clipping Utility","Creating clip...")
    elif event==2:
      message = 'Clip was created!'
      color = Qt.green
      if self.config.values['clip-notif']:
        self.trayIcon.showMessage("Stream Clipping Utility",message)
    elif event==3:
      message = 'Could not create clip.'
      color = Qt.red
      if self.config.values['error-notif']:
        self.trayIcon.showMessage("Stream Clipping Utility",message)
    elif event==4:
      message = 'Channel is offline.'
      color = Qt.red
      if self.config.values['error-notif']:
        self.trayIcon.showMessage("Stream Clipping Utility",message)
    elif event==5:
      self.setStatus("The folder that was selected for saving clip links doesn't exist.")
    elif event==6:
      self.setStatus("Insufficient write permissions for the folder that was selected for saving clip links.")
    elif event==7:
      self.setStatus("The folder that was selected for saving clip links is full.")
    elif event==8:
      message = "Creating marker..."
      if self.config.values['clip-notif']:
        self.trayIcon.showMessage("Stream Clipping Utility",message)
    elif event==9:
      message = f'Marker was created at {data}.'
      color = Qt.green
      if self.config.values['clip-notif']:
        self.trayIcon.showMessage("Stream Clipping Utility",message)
    elif event==10:
      message = 'Could not create marker.'
      color = Qt.red
      if self.config.values['error-notif']:
        self.trayIcon.showMessage("Stream Clipping Utility",message)
    elif event==11:
      message = 'Can\'t create marker due to VODs being disabled or private.'
      if self.config.values['error-notif']:
        self.trayIcon.showMessage("Stream Clipping Utility",message)
    else:
      raise Exception("Invalid event code.")
    
    if message != None:
      self.addStatusItem(message,color)
  
  # Raises window
  def raiseTrigger(self):
    self.raise_()
    self.activateWindow()
  
  # Enables/disabled most GUI elements
  def guiSetEnable(self,val):
    if val:
      self.updateLoginStatus()
    else:
      self.loginButton.setEnabled(val)
      self.logoutButton.setEnabled(val)
      self.retryButton.setEnabled(val)
      self.cancelButton.setEnabled(val)
    self.keyComboSelect.setEnabled(val)
    self.clipsEnabled.setEnabled(val)
    self.clipsFilePath.setEnabled(val and self.config.values['clips-enabled'])
    self.clipsFilePathBrowse.setEnabled(val and self.config.values['clips-enabled'])
    self.markersEnabled.setEnabled(val)
    self.clipNotif.setEnabled(val)
    self.errorNotif.setEnabled(val)
    self.trayOnStartup.setEnabled(val)
  
  def start_stop(self):
    # Stops if already started
    if self.started:
      print("Stopping")
      self.started = False
      # Re-enables most GUI elements
      self.guiSetEnable(True)
      # Changes button text
      self.startButton.setText("Start")
      # Stops sources
      self.stopOthers()
    # Starts if not already started
    else:
      print("Starting")
      self.started = True
      # Disables most GUI elements
      self.guiSetEnable(False)
      # Changes button text
      self.startButton.setText("Stop")
      # Starts sources
      self.startOthers()
    
    # Updates status label
    self.updateStatus()
  
  # Create window
  def __init__(self):
    super().__init__()
    self.config = None
    self.twitch = None
    self.started = False
    self.__status_msg = {'main':'Please wait...'}
    
    # Main window layout
    self.appIcon = QIcon("icon.png")
    self.resize(420,520)
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
    self.clipsEnabled = QCheckBox("Create clips")
    self.clipsFilePathLayout = QHBoxLayout(self)
    self.clipsFilePath = QLineEdit(self)
    self.clipsFilePath.setReadOnly(True)
    self.clipsFilePathBrowse = QPushButton("Browse",self)
    self.clipsFilePathLayout.addWidget(self.clipsFilePath)
    self.clipsFilePathLayout.addWidget(self.clipsFilePathBrowse)
    self.markersEnabled = QCheckBox("Create markers")
    self.clipNotif = QCheckBox("Show notification on successful clip/marker",self)
    self.errorNotif = QCheckBox("Show notification on error",self)
    self.trayOnStartup = QCheckBox("Minimize to tray on startup",self)
    
    self.optionsLayout.addRow("Key Combination Trigger:",self.keyComboSelect)
    self.optionsLayout.addRow(self.clipsEnabled)
    self.optionsLayout.addRow("Save clip links to (folder):",self.clipsFilePathLayout)
    self.optionsLayout.addRow(self.markersEnabled)
    self.optionsLayout.addRow(self.clipNotif)
    self.optionsLayout.addRow(self.errorNotif)
    self.optionsLayout.addRow(self.trayOnStartup)
    
    # Status display
    self.status = QLabel("<b>Status</b>",self)
    self.statusList = QListWidget(self)
    self.status.setTextFormat(Qt.RichText)
    self.mainLayout.addStretch()
    self.mainLayout.addWidget(self.status)
    self.mainLayout.addWidget(self.statusList)
    self.updateStatus()
    
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
    
    # File dialog
    self.clipsFilePathDialog = QFileDialog(self)
    self.clipsFilePathDialog.setFileMode(QFileDialog.Directory)
    
    # System tray icon
    self.trayIcon = QSystemTrayIcon(self)
    self.trayIcon.setIcon(self.appIcon)
    self.trayIcon.show()
    
    # System tray menu
    self.trayMenu = QMenu(self)
    
    # Config error message dialog
    self.configErrorDialog = QErrorMessage(self)
    self.keyboardSourceErrorDialog = QErrorMessage(self)
  
  # Slots and signals
  def initSlots(self):
    self.loginButton.clicked.connect(self.twitch.login)
    self.logoutButton.clicked.connect(self.twitch.logout)
    self.retryButton.clicked.connect(self.twitch.retry)
    self.cancelButton.clicked.connect(self.twitch.cancel)
    
    self.keyComboSelect.editingFinished.connect(self.keySequenceUpdate)
    self.clipsEnabled.toggled.connect(self.clipsEnabledUpdate)
    self.clipsFilePathBrowse.clicked.connect(self.clipsFilePathDialog.show)
    self.clipsFilePathDialog.fileSelected.connect(self.clipsFilePathOpen)
    self.markersEnabled.toggled.connect(self.markersEnabledUpdate)
    self.clipNotif.toggled.connect(self.clipNotifUpdate)
    self.errorNotif.toggled.connect(self.errorNotifUpdate)
    self.trayOnStartup.toggled.connect(self.trayOnStartupUpdate)
    
    self.startButton.clicked.connect(self.start_stop)
    self.hideButton.clicked.connect(self.hide)
    self.trayIcon.activated.connect(self.toggleWindow)

  # Updates GUI when configuration file is loaded
  def onConfigLoad(self):
    v = self.config.values
    self.keyComboSelect.setKeySequence(QKeySequence(v["key-combo"]))
    self.clipsEnabled.setChecked(v['clips-enabled'])
    self.clipsFilePath.setEnabled(v['clips-enabled'])
    self.clipsFilePath.setText(v['clips-file-path'])
    self.clipsFilePathBrowse.setEnabled(v['clips-enabled'])
    self.markersEnabled.setChecked(v['markers-enabled'])
    self.clipNotif.setChecked(v["clip-notif"])
    self.errorNotif.setChecked(v["error-notif"])
    self.trayOnStartup.setChecked(v["tray-on-startup"])
