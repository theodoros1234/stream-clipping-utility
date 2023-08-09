import os, logging, time, webbrowser
from PySide2.QtGui import QKeySequence

default_client_id = "2ya1fhz3io1xhy9ao03ull3k8wwqff"
apr1link = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


class configManager():
  def __init__(self,loc="app.config"):
    self.values = {}
    if type(loc) != str:
      raise Exception("Location argument is not a string.")
    self.fileLocation = loc 
    self.loadTrigger = None
    self.apr1trigger = False
  # Function that loads a config file, and changes appropriate widgets on the main window to match the current configuration
  def load(self):
    # Check if file exists before loading
    if os.path.exists(self.fileLocation):
      try:
        with open(self.fileLocation,'r') as config_file:
          logging.info("Loading config file")
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
        logging.error("Error loading config file. Using default config.")
        self.configErrorDialog.showMessage("Error encountered while reading configuration info. Defaults will be used instead.")
    
    # Load default values for invalid or unset options
    if "client-id" in self.values:
      if self.values["client-id"] == str():
        self.values["client-id"] = default_client_id
    else:
      self.values["client-id"] = default_client_id
    
    if ("token" in self.values) == False:
      self.values["token"] = str()

    # if ("key-combo" in self.values) == False:
    #   self.values["key-combo"] = str()
    # self.values["key-combo"] = QKeySequence(self.values["key-combo"]).toString().lower()
    
    if "key-combo-v2" in self.values and self.values["key-combo-v2"] != "":
      try:
        key_combo_v2 = self.values["key-combo-v2"].split(',')
        self.values["key-combo-v2"] = (key_combo_v2[0:-1], int(key_combo_v2[-1]))
      except:
        self.values["key-combo-v2"] = ([], 0)
    else:
      self.values["key-combo-v2"] = ([], 0)

    if ("clips-file-path" in self.values) == False:
      self.values["clips-file-path"] = str()
    
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
    
    if "clips-enabled" in self.values:
      if self.values['clips-enabled'].lower() == "true":
        self.values['clips-enabled'] = True
      else:
        self.values['clips-enabled'] = False
    else:
      self.values['clips-enabled'] = False
    
    if "markers-enabled" in self.values:
      if self.values['markers-enabled'].lower() == "true":
        self.values['markers-enabled'] = True
      else:
        self.values['markers-enabled'] = False
    else:
      self.values['markers-enabled'] = True

    if "last-opened-at" in self.values:
      try:
        self.values['last-opened-at'] = float(self.values['last-opened-at'])
      except:
        self.values['last-opened-at'] = time.time()
    else:
      self.values['last-opened-at'] = time.time()

    # Check if it's April 1st or if April 1st has passed since the last time the app was opened
    time_now = time.localtime()
    time_apr1 = time.mktime(time.strptime("1/4/" + str(time_now.tm_year), "%d/%m/%Y"))
    self.apr1trigger = (time_now.tm_mon==4 and time_now.tm_mday==1) or (self.values['last-opened-at'] <= time_apr1 and time_apr1 <= time.mktime(time_now))
    self.values['last-opened-at'] = time.time()

    # Launch rick roll if the check passed
    if self.apr1trigger:
      webbrowser.open(apr1link)

    # Save values
    self.save()

    # Print config
    logging.debug("Loaded values:")
    for item in self.values.items():
      if item[0]=="token":
        logging.debug("token=%s"%('*'*len(item[1])))
      else:
        logging.debug("%s=%s"%(item[0],item[1]))
    if self.loadTrigger != None:
      self.loadTrigger()

  # Function that saves config file
  def save(self):
    try:
      with open(self.fileLocation,'w') as config_file:
        for item in self.values.items():
          # Special case for key combo
          if item[0] == "key-combo-v2":
            config_file.write("%s=%s\n"%(item[0], ",".join(item[1][0] + [str(item[1][1])])))
          # Write each line to the config file
          else:
            config_file.write("%s=%s\n"%(item[0],item[1]))
      logging.info("Updated config file")
    except Exception as e:
      logging.warning("Could not save configuration.")
      # Show error message in case something goes wrong
      # self.configErrorDialog.showMessage("Could not save configuration.")
      raise e
