import http.client, http.server, string, random, json, urllib.parse, threading, webbrowser


# Twitch integration class
class twitchIntegration():
  # Login response from browser received
  def receivedLoginResponse(self):
    print("Stopping server and returning to application")
    self.loginServer.server_close()
    if self.raiseWindow != None:
      self.raiseWindow()
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
            self.parent.cancel()
            if self.parent.raiseWindow != None:
              self.parent.raiseWindow()
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
          self.parent.config.values['token'] = data[key][0].decode()
          self.send_response(200)
          threading.Thread(target=self.parent.receivedLoginResponse,daemon=True).start()
          self.parent.config.saveConfig()
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
    self.config = None
    self.raiseWindow = None
    # status 0: Not logged in
    # status 1: Validating token/login status
    # status 2: Waiting to receive login token from web browser
    # status 3: Server connection error
    # status 4: Logged in
    
  # Changes login status and triggers everything that also needs to be updated
  def changeStatus(self,new):
    self.status = int(new)
    print("Updated login status to",new)
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
    self.config.saveConfig()
  
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
        print("Invalid characters found in token")
        self.changeStatus(0)
        return
      # Try connecting to twitch for verification
      try:
        print("Verifying twitch access token")
        hd = {"Authorization": "Bearer " + self.config.values['token']}
        self.authComm.request('GET',"/oauth2/validate",headers=hd)
        response = self.authComm.getresponse()
        print("Received response from Twitch server")
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
        self.loginServer.RequestHandlerClass.parent = self
        setup_success = True
        break
      except:
        pass
    self.stateToken = ''.join(random.choices(string.ascii_letters+string.digits,k=32))
    params = {
      "client_id": self.config.values['client-id'],
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
