#!/bin/python3
# This Python file uses the following encoding: utf-8
import sys, os, http.client, http.server, urllib.parse, json, string, random, threading, webbrowser
from PySide2.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel, QPushButton, QKeySequenceEdit, QSpinBox, QCheckBox, QSystemTrayIcon, QMenu, QErrorMessage
from PySide2.QtGui import QKeySequence, QIcon, Qt


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


# Twitch integration class
class twitchIntegration():
  # Login response from browser received
  def receivedLoginResponse(self):
    print("Stopping server and returning to application")
    self.loginServer.server_close()
    window.raise_()
    window.activateWindow()
    self.checkStatus()
  # Login server request handler
  class requestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
      parsed = urllib.parse.urlparse(self.path)
      query = urllib.parse.parse_qs(parsed.query)
      if parsed.path == "/auth_redirect":
        self.send_response(200)
        self.send_header("Content-type","text/html")
        self.end_headers()
        self.wfile.write(bytes(open("auth_redirect.html","r").read(),'utf-8'))
        try:
          if query['error'][0] == 'access_denied':
            twitch.cancel()
            window.raise_()
            window.activateWindow()
        except:
          pass
      elif parsed.path == "/submit_info":
        self.send_response(401)
        self.end_headers()
      else:
        self.send_response(404)
        self.end_headers()
    def do_POST(self):
      parsed = urllib.parse.urlparse(self.path)
      if parsed.path == "/submit_info":
        content_length = int(self.headers['Content-Length'])
        data = urllib.parse.parse_qs(self.rfile.read(content_length))
        key = "access_token".encode('utf-8')
        try:
          config['token'] = data[key][0].decode()
          self.send_response(200)
          threading.Thread(target=twitch.receivedLoginResponse,daemon=True).start()
          save_config()
        except:
          self.end_headers()
          self.send_response(401)
          self.end_headers()
      else:
        self.send_response(401)
        self.end_headers()
  
  # Init function
  def __init__(self):
    self.authComm = http.client.HTTPSConnection("id.twitch.tv",timeout=10)
    self.loginServer = None
    self.status = 1
    self.error = 0
    self.cancelling = False
    self.username = ""
    # status 0: Not logged in
    # status 1: Validating token/login status
    # status 2: Waiting to receive login token from web browser
    # status 3: Server connection error
    # status 4: Logged in
    
  # Changes login status and triggers everything that also needs to be updated
  def changeStatus(self,new):
    self.status = int(new)
    print("Updated login status to",new)
    window.updateLoginStatus()
    
  # Receives an error code and sets the appropriate error message and status code
  def loginError(self,errcode):
    # 0: Could not connect to server
    # 1: Invalid response from server
    # 2: Cancelled by user
    # 3: Could not set up local server for listening to browser response for token id
    self.error = errcode
    self.changeStatus(3)
  
  def cancel(self):
    self.cancelling = True
    if self.status==1:
      self.authComm.close()
    elif self.status==2:
      self.loginServer.server_close()
      self.checkStatus()
  
  def retry(self):
    if self.error==3:
      self.login()
    else:
      self.checkStatus()
  
  # Check login status
  def checkStatus(self):
    self.cancelling = False
    self.changeStatus(1)
    if config['token']=="":
      self.changeStatus(0)
    else:
      # Verify that token doesn't contain any invalid characters
      invalid=False
      for i in config['token']:
        if (i in string.ascii_lowercase+string.digits)==False:
          invalid=True
          break
      # If token is invalid, assume the user is not logged in and halt function execution
      if invalid:
        print("Invalid characters found in token")
        self.changeStatus(0)
        return
      # Try connecting to twitch for verification
      try:
        print("Verifying twitch access token")
        hd = {"Authorization": "Bearer " + config['token']}
        self.authComm.request('GET',"/oauth2/validate",headers=hd)
        response = self.authComm.getresponse()
        print("Received response")
        # Status indicates verification success
        if response.status == 200:
          try:
            data = json.loads(response.read())
            # Store username
            self.username = data['login']
            # Verify that the appropriate scopes are allowed, otherwise consider user as not logged in
            if 'clips:edit' in data['scopes']:
              print("Valid token with sufficient permissions")
              self.changeStatus(4)
            else:
              print("Valid token, but with insufficient permissions")
              self.changeStatus(0)
          except:
            # Response is invalid
            print("Invalid response received")
            self.loginError(1)
        # Status indicates invalid token, which means user is not logged in
        elif response.status == 401:
          print("Invalid token")
          self.changeStatus(0)
        # Response is invalid if reponse status is unexpected
        else:
          print("Invalid response status received")
          self.loginError(1)
      # Error connecting to the server
      except:
        if self.cancelling:
          print("Cancelled")
          self.loginError(2)
        else:
          print("Could not connect to server")
          self.loginError(0)
  
  def login(self):
    self.cancelling = False
    self.changeStatus(2)
    port = 59490
    setup_success = False
    for port in range(59490,59500):
      try:
        self.loginServer = http.server.HTTPServer(('127.0.0.1',port),self.requestHandler)
        setup_success = True
        break
      except:
        pass
    self.stateToken = ''.join(random.choices(string.ascii_letters+string.digits,k=32))
    params = {
      "client_id": config['client-id'],
      "redirect_uri": "http://localhost:%i/auth_redirect"%(port),
      "response_type": "token",
      "scope": "clips:edit",
      "force_verify": "true",
      "state": self.stateToken
    }
    link = "https://id.twitch.tv/oauth2/authorize?" + urllib.parse.urlencode(params)
    webbrowser.open(link)
    threading.Thread(target=self.loginServer.serve_forever,daemon=True).start()
    print("Listening for response on port",port)


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
    config['key-combo']=seq
    self.keyComboSelect.setKeySequence(QKeySequence(seq))
    save_config()
    check_start_requirements()
  def clipLengthUpdate(self,val):
    config['clip-length'] = val
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
  # Updates login status label
  def updateLoginStatus(self):
    retryEnable = False
    loginEnable = False
    cancelEnable = False
    loginText = ""
    if twitch.status==0:
      msg = "Not logged in"
      self.loginButton.setText("Login")
      loginEnable = True
    elif twitch.status==1:
      msg = "Logging in..."
      cancelEnable = True
    elif twitch.status==2:
      msg = "Waiting for response from browser..."
      cancelEnable = True
    elif twitch.status==3:
      self.loginButton.setText("Switch user")
      retryEnable = True
      loginEnable = True
      if twitch.error==0:
        msg = "Could not connect to Twitch servers, check your internet connection."
      elif twitch.error==1:
        msg = "Invalid response received from server."
      elif twitch.error==2:
        msg = "Connection cancelled."
      else:
        msg = "Unknown error occured."
    elif twitch.status==4:
      msg = "Logged in as " + twitch.username
      self.loginButton.setText("Switch user")
      loginEnable = True
    self.loginStatus.setText(msg)
    self.retryButton.setEnabled(retryEnable)
    self.loginButton.setEnabled(loginEnable)
    self.cancelButton.setEnabled(cancelEnable)
    #self.loginButton.repaint()
    #self.retryButton.repaint()
    #self.cancelButton.repaint()
  # Create window
  def __init__(self):
      super().__init__()

      # Main window layout
      self.appIcon = QIcon("icon.png")
      self.resize(360,400)
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
      self.retryButton = QPushButton("Retry",self)
      self.loginButton = QPushButton("Login",self)
      self.cancelButton = QPushButton("Cancel",self)
      self.retryButton.setEnabled(False)
      self.loginButton.setEnabled(False)
      self.cancelButton.setEnabled(False)
      self.loginLayout.addWidget(self.retryButton)
      self.loginLayout.addWidget(self.loginButton)
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

  def initSlots(self):
    # Slots
    self.retryButton.released.connect(twitch.retry)
    self.loginButton.released.connect(twitch.login)
    self.cancelButton.released.connect(twitch.cancel)
    
    self.keyComboSelect.editingFinished.connect(self.keySequenceUpdate)
    self.clipLength.valueChanged.connect(self.clipLengthUpdate)
    self.clipNotif.toggled.connect(self.clipNotifUpdate)
    self.errorNotif.toggled.connect(self.errorNotifUpdate)
    self.trayOnStartup.toggled.connect(self.trayOnStartupUpdate)
    
    self.hideButton.released.connect(self.hide)
    self.trayIcon.activated.connect(self.toggleWindow)


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
    twitch = twitchIntegration()
    window.initSlots()
    
    load_config("app.config")
    window.trayIcon.show()
    if config["tray-on-startup"]:
      window.trayIcon.showMessage("Stream Clipping Utility","Application has started hidden in tray.",window.appIcon)
    else:
      window.show()
    threading.Thread(target=twitch.checkStatus,daemon=True).start()
    sys.exit(app.exec_())
