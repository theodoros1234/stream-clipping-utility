import http.client, http.server, string, random, json, urllib.parse, threading, webbrowser, logging


# Twitch integration class
class twitchIntegration():
  
  # Login response from browser received
  def receivedLoginResponse(self):
    logging.info("Stopping server and returning to application")
    self.loginServer.shutdown()
    self.loginServer.server_close()
    if self.raiseWindow != None:
      self.raiseWindow()
    self.checkStatus()
  
  # Login server request handler
  class requestHandler(http.server.BaseHTTPRequestHandler):
    # GET method
    def do_GET(self):
      # Get URL data
      parsed = urllib.parse.urlparse(self.path)
      query = urllib.parse.parse_qs(parsed.query)
      # Redirect page
      if parsed.path == "/auth_redirect":
        self.send_response(200)
        self.send_header("Content-type","text/html")
        self.end_headers()
        self.wfile.write(bytes(open("auth_redirect.html","r").read(),'utf-8'))
        # Check if login was cancelled from the Twitch page
        try:
          # Only cancel if state value is set correctly
          if query['error'][0] == 'access_denied' and query['state'][0] == self.parent.stateToken:
            self.parent.cancel()
            if self.parent.raiseWindow != None:
              self.parent.raiseWindow()
        except:
          pass
      # Data receiver page (POST method should be used, so this responds with an error)
      elif parsed.path == "/submit_info":
        self.send_response(401)
        self.end_headers()
      # Invalid page
      else:
        self.send_response(404)
        self.end_headers()
    
    # POST method
    def do_POST(self):
      # Parse data from URL
      parsed = urllib.parse.urlparse(self.path)
      # Data receiver page
      if parsed.path == "/submit_info":
        # Parse data from request body
        content_length = int(self.headers['Content-Length'])
        data = urllib.parse.parse_qs(self.rfile.read(content_length))
        key = "access_token".encode('utf-8')
        try:
          # Interrupt communication if state value doesn't match
          if 'state'.encode('utf-8') in data:
            if data['state'.encode('utf-8')][0] != self.parent.stateToken.encode('utf-8'):
              self.send_response(401)
              self.end_headers()
              return
          else:
            self.send_response(401)
            self.end_headers()
            return
          self.send_response(200)
          self.end_headers()
          # Store token, save config and verify login
          self.parent.config.values['token'] = data[key][0].decode()
          threading.Thread(target=self.parent.receivedLoginResponse,daemon=True).start()
          self.parent.config.save()
        except:
          # Request was missing required parameters
          self.end_headers()
          self.send_response(401)
          self.end_headers()
      # Invalid page requested
      else:
        self.send_response(401)
        self.end_headers()
    
    # Logging method
    def log_message(self, format, *args):
      message = f"{self.client_address[0]}:{str(self.client_address[1])}> " + format%args
      logging.debug(message)
  
  # Init function
  def __init__(self):
    self.authComm = http.client.HTTPSConnection("id.twitch.tv",timeout=10)
    self.apiComm = http.client.HTTPSConnection("api.twitch.tv")
    self.loginServer = None
    self.status = 1
    self.error = 0
    self.cancelling = False
    self.username = ""
    self.user_id = ""
    self.config = None
    self.raiseWindow = None
    self.notif = None
    self.busy = threading.Lock()
    # status 0: Not logged in
    # status 1: Validating token/login status
    # status 2: Waiting to receive login token from web browser
    # status 3: Server connection error
    # status 4: Logged in
    
  # Changes login status and triggers everything that also needs to be updated
  def changeStatus(self,new):
    self.status = int(new)
    logging.debug("Updated login status to "+str(new))
    if self.updateWindow != None:
      self.updateWindow()
    
  # Receives an error code and sets the appropriate error message and status code
  def loginError(self,errcode):
    # 0: Could not connect to server
    # 1: Invalid response from server
    # 2: Cancelled by user
    # 3: Could not set up local server for listening to browser response for token id
    self.error = errcode
    self.changeStatus(3)
  
  # Cancels current action
  def cancel(self):
    self.cancelling = True
    if self.status==1:
      self.authComm.close()
    elif self.status==2:
      self.loginServer.server_close()
      self.checkStatus()
  
  # Retries action that caused an error
  def retry(self):
    if self.error==3:
      self.login()
    else:
      self.checkStatus()
  
  # Logs user out by removing token from local configuration
  def logout(self):
    self.config.values['token'] = ""
    self.checkStatus()
    self.config.save()
  
  # Check login status
  def checkStatus(self):
    self.cancelling = False
    self.changeStatus(1)
    if self.config.values['token']=="":
      self.changeStatus(0)
    else:
      # Verify that token doesn't contain any invalid characters
      invalid=False
      for i in self.config.values['token']:
        if (i in string.ascii_lowercase+string.digits)==False:
          invalid=True
          break
      # If token is invalid, assume the user is not logged in and halt function execution
      if invalid:
        logging.error("Invalid characters found in token")
        self.changeStatus(0)
        return
      # Try connecting to twitch for verification
      try:
        logging.info("Verifying twitch access token")
        self.authComm = http.client.HTTPSConnection("id.twitch.tv",timeout=10)
        hd = {"Authorization": "Bearer " + self.config.values['token']}
        self.authComm.request('GET',"/oauth2/validate",headers=hd)
        response = self.authComm.getresponse()
        logging.debug("Received response from Twitch server")
        # Status indicates verification success
        if response.status == 200:
          try:
            data = json.loads(response.read())
            # Store username
            self.username = data['login']
            self.user_id = data['user_id']
            # Verify that the appropriate scopes are allowed, otherwise consider user as not logged in
            if 'clips:edit' in data['scopes'] and 'channel:manage:broadcast' in data['scopes']:
              logging.info("Valid token with sufficient permissions")
              self.changeStatus(4)
            else:
              logging.warning("Valid token, but with insufficient permissions")
              self.changeStatus(0)
          except:
            # Response is invalid
            logging.error("Invalid response received")
            self.loginError(1)
        # Status indicates invalid token, which means user is not logged in
        elif response.status == 401:
          logging.warning("Invalid token")
          self.changeStatus(0)
        # Response is invalid if reponse status is unexpected
        else:
          logging.error("Invalid response status received")
          self.loginError(1)
      # Error connecting to the server
      except:
        if self.cancelling:
          logging.info("Cancelled")
          self.loginError(2)
        else:
          logging.warning("Could not connect to server")
          self.loginError(0)
  
  # Log into a twitch account
  def login(self):
    self.cancelling = False
    self.changeStatus(2)
    port = 59490
    setup_success = False
    # Attempt to start a server (to retrieve token from browser after being redirected to Twitch)
    for port in range(59490,59500):
      try:
        self.authComm = http.client.HTTPSConnection("id.twitch.tv",timeout=10)
        self.loginServer = http.server.HTTPServer(('127.0.0.1',port),self.requestHandler)
        self.loginServer.RequestHandlerClass.parent = self
        setup_success = True
        break
      except:
        pass
    # Set state token
    self.stateToken = ''.join(random.choices(string.ascii_letters+string.digits,k=32))
    # Construct URL for Twitch login 
    params = {
      "client_id": self.config.values['client-id'],
      "redirect_uri": "http://localhost:%i/auth_redirect"%(port),
      "response_type": "token",
      "scope": "clips:edit channel:manage:broadcast",
      "force_verify": "true",
      "state": self.stateToken
    }
    link = "https://id.twitch.tv/oauth2/authorize?" + urllib.parse.urlencode(params)
    # Open the link on the default web browser
    webbrowser.open(link)
    # Start server thread
    threading.Thread(target=self.loginServer.serve_forever,daemon=True).start()
    logging.info("Listening for response on port "+str(port))
  
  # Create clip or marker, according to config
  def create(self):
    self.busy.acquire()
    try:
      self.apiComm = http.client.HTTPSConnection("api.twitch.tv")
      # Change status message
      if self.config.values['clips-enabled']:
        self.createClip()
      if self.config.values['markers-enabled']:
        self.createMarker()
    except BaseException as e:
      logging.error("Exception while creating clip/marker: "+str(e))
    self.busy.release()
  
  # Create clip
  def createClip(self):
    # Try to create a clip, retry up to 4 times
    self.notif("Creating clip...",kind="creation_start")
    retries = 4
    error_r = True
    logging.info("Creating clip")
    while retries and error_r:
      error_r = False
      try:
        hd = {
          "Authorization": "Bearer " + self.config.values['token'],
          "Client-Id": self.config.values['client-id'],
          "Content-Type": "application/x-www-form-urlencoded"
        }
        params = {
          'broadcaster_id': self.user_id,
          'has_delay': 'true'
        }
        self.apiComm.request('POST',"/helix/clips",urllib.parse.urlencode(params).encode(),hd)
        response = self.apiComm.getresponse()
        data = json.loads(response.read())
        if response.status == 202:
          url = data['data'][0]['edit_url']
          logging.info("Clip created: "+url)
          self.exportUrl(url)
          self.notif("<font color='green'>Clip was created!</font>",kind="creation_success")
        elif response.status == 404:
          logging.info(f"{str(response.status)} {response.reason}")
          error_msg = data['message']
          logging.info(error_msg)
          self.notif("<font color='red'>Could not create clip: </font>Channel is offline.",kind="creation_error")
        else:
          logging.warning(f"{str(response.status)} {response.reason}")
          try:
            logging.warning(data['error'])
          except:
            pass
          error_r = True
          retries -= 1
      except BaseException as exp:
        logging.error("Error while taking clip: "+str(exp))
        error_r = True
        retries -= 1
    if retries == 0:
      self.notif("<font color='red'>Could not create clip.</font>",kind="creation_error")

  # Create clip
  def createMarker(self):
    # Try to create a marker, retry up to 4 times
    self.notif("Creating marker...",kind="creation_start")
    retries = 4
    error_r = True
    logging.info("Creating marker")
    while retries and error_r:
      error_r = False
      try:
        hd = {
          "Authorization": "Bearer " + self.config.values['token'],
          "Client-Id": self.config.values['client-id'],
          "Content-Type": "application/x-www-form-urlencoded"
        }
        params = {'user_id': self.user_id}
        self.apiComm.request('POST',"/helix/streams/markers",urllib.parse.urlencode(params).encode(),hd)
        response = self.apiComm.getresponse()
        data = json.loads(response.read())
        if response.status == 200:
          seconds = int(data['data'][0]['position_seconds'])
          hours = str(seconds//3600)
          minutes = str((seconds//60)%60).zfill(2)
          seconds = str(seconds%60).zfill(2)
          timestamp = f"{hours}:{minutes}:{seconds}"
          logging.info("Marker created at "+timestamp)
          self.notif(f"<font color='green'>Marker was created at</font> {timestamp} <font color='green'>stream time.</font>",kind="creation_success")
        elif response.status == 404:
          logging.info(f"{str(response.status)} {response.reason}")
          error = data['error']
          error_msg = data['message']
          logging.info(error_msg)
          short_error_msg = error_msg[error_msg.find('message:"')+9:error_msg.find('"',-1)]
          self.notif(f"<font color='red'>Could not create marker:</font> {short_error_msg}",kind="creation_error")
        else:
          logging.warning(f"{str(response.status)} {response.reason}")
          try:
            logging.warning(data['error'])
          except:
            pass
          error_r = True
          retries -= 1
      except BaseException as err:
        logging.error("Error while creating marker: "+str(err))
        error_r = True
        retries -= 1
    if retries == 0:
      self.notif("<font color='red'>Could not create marker.</font>",kind="creation_error")
