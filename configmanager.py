import os


default_client_id = "2ya1fhz3io1xhy9ao03ull3k8wwqff"


class configManager():
  def __init__(self,loc="app.config"):
    self.values = {}
    if type(loc) != str:
      raise Exception("Location argument is not a string.")
    self.fileLocation = loc 
    self.loadTrigger = None
  # Function that loads a config file, and changes appropriate widgets on the main window to match the current configuration
  def loadConfig(self):
    # Check if file exists before loading
    if os.path.exists(self.fileLocation):
      try:
        with open(self.fileLocation,'r') as config_file:
          print("Loading config file")
          # Go through each line, separate key from value, and store them in the config variable
          for line in config_file.readlines():
            separator_pos = line.find('=')
            # Skip invalid lines
            if separator_pos==-1:
              continue
            key = line[0:separator_pos].strip()
            value = line[separator_pos+1:].strip()
            self.values[key] = value
      except:
        # Show error dialog when there's an error loading the config file
        print("Error loading config file. Using default config.")
        window.configErrorDialog.showMessage("Error encountered while reading configuration info. Defaults will be used instead.")
    
    # Load default values for invalid or unset options
    if "client-id" in self.values:
      if self.values["client-id"] == "":
        self.values["client-id"] = default_client_id
    else:
      self.values["client-id"] = default_client_id
    if ("token" in self.values) == False:
      self.values["token"] = ""
    if ("key-combo" in self.values) == False:
      self.values["key-combo"] = ""
    if "clip-length" in self.values:
      try:
        self.values["clip-length"] = int(self.values["clip-length"])
      except:
        self.values["clip-length"] = 60
    else:
      self.values["clip-length"] = 60
    if "clip-notif" in self.values:
      if self.values["clip-notif"].lower() == "false":
        self.values["clip-notif"] = False
      else:
        self.values["clip-notif"] = True
    else:
      self.values["clip-notif"] = True
    if "error-notif" in self.values:
      if self.values["error-notif"].lower() == "false":
        self.values["error-notif"] = False
      else:
        self.values["error-notif"] = True
    else:
      self.values["error-notif"] = True
    if "tray-on-startup" in self.values:
      if self.values["tray-on-startup"].lower() == "true":
        self.values["tray-on-startup"] = True
      else:
        self.values["tray-on-startup"] = False
    else:
      self.values["tray-on-startup"] = False
    
    # Print config
    print("Loaded values:")
    for item in self.values.items():
      if item[0]=="token":
        print("token=%s"%('*'*len(item[1])))
      else:
        print("%s=%s"%(item[0],item[1]))
    print()
    if self.loadTrigger != None:
      self.loadTrigger()

  # Function that saves config file
  def saveConfig(self):
    try:
      config_file = open(self.fileLocation,'w')
      for item in self.values.items():
        # Write each line to the config file
        config_file.write("%s=%s\n"%(item[0],item[1]))
      config_file.close()
      print("Updated config file")
    except:
      # Show error message in case something goes wrong
      window.configErrorDialog.showMessage("Could not save configuration.")
