import os, logging
from PySide2.QtGui import QKeySequence

default_client_id = "2ya1fhz3io1xhy9ao03ull3k8wwqff"


class configManager():
  def __init__(self,loc="app.config"):
    self.values = {}
    if type(loc) != str:
      raise Exception("Location argument is not a string.")
    self.fileLocation = loc 
    self.loadTrigger = None
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
        window.configErrorDialog.showMessage("Error encountered while reading configuration info. Defaults will be used instead.")
    
    # Load default values for invalid or unset options
    if "client-id" in self.values:
      if self.values["client-id"] == str():
        self.values["client-id"] = default_client_id
    else:
      self.values["client-id"] = default_client_id
    
    if ("token" in self.values) == False:
      self.values["token"] = str()
    
    if ("key-combo" in self.values) == False:
      self.values["key-combo"] = str()
    self.values["key-combo"] = QKeySequence(self.values["key-combo"]).toString().lower()
    
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
      config_file = open(self.fileLocation,'w')
      for item in self.values.items():
        # Write each line to the config file
        config_file.write("%s=%s\n"%(item[0],item[1]))
      config_file.close()
      logging.info("Updated config file")
    except:
      logging.warning("Could not save configuration.")
      # Show error message in case something goes wrong
      window.configErrorDialog.showMessage("Could not save configuration.")
