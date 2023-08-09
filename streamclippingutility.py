#!/bin/python3
# This Python file uses the following encoding: utf-8
import os, sys, threading, logging, time
from configmanager import configManager
from twitchintegration import twitchIntegration
from mainwindow import MainWindow
from keyboardsource import keyboardSource
from urloutput import urlOutput
from PySide2.QtWidgets import QApplication

# Starts all sources
def start():
  keyboard.start()
  if config.values['clips-enabled']:
    url_out.start()

# Stops all sources
def stop(blocking=False):
  keyboard.stop()
  twitch.busy.acquire()
  if config.values['clips-enabled']:
    url_out.stop()
  twitch.busy.release()


# Main function
if __name__ == "__main__":
  # Configure logging
  log_format = "%(asctime)s [%(levelname)s] %(message)s"
  log_handlers = []
  log_level = logging.DEBUG
  # Output to terminal, if not running in Windows non-console mode
  if sys.stderr!=None:
    log_handlers.append(logging.StreamHandler())
  try:
    # If possible, try outputting to log file in scu_logs folder
    if os.path.exists("scu_logs")==False:
      os.mkdir("scu_logs")
    log_handlers.append(logging.FileHandler(time.strftime("scu_logs/streamclippingutility_%Y%m%d_%H%M%S.log")))
    logging.basicConfig(handlers=log_handlers, format=log_format, level=log_level)
  except:
    # Otherwise, output to a log file in the same folder
    try:
      log_handlers.append(logging.FileHandler(time.strftime("streamclippingutility_%Y%m%d_%H%M%S.log")))
      logging.basicConfig(handlers=log_handlers, format=log_format, level=log_level)
    except:
      # If unable to output to a file and console output is available, output to console.
      if len(log_handlers)!=0:
        logging.basicConfig(handlers=log_handlers, format=log_format, level=log_level)
  
  logging.info("Initializing")
  # Create objects
  app = QApplication(sys.argv)
  config = configManager()
  window = MainWindow()
  twitch = twitchIntegration()
  keyboard = keyboardSource()
  url_out = urlOutput()
  
  # Assign config object to each object that uses it
  window.config = config
  twitch.config = config
  keyboard.config = config
  url_out.config = config
  # Connect trigger functions between objects
  config.loadTrigger = window.onConfigLoad
  config.configErrorDialog = window.configErrorDialog
  window.twitch = twitch
  window.startOthers = start
  window.stopOthers = stop
  window.getNewHotkey = keyboard.newHotkey
  window.cancelHotkey = keyboard.cancelHotkey
  window.hotkeyToString = keyboard.hotkeyToString
  twitch.raiseWindow = window.raiseTrigger
  twitch.updateWindow = window.updateLoginStatus
  twitch.notif = window.addStatusItem
  twitch.exportUrl = url_out.push
  keyboard.trigger = twitch.create
  url_out.stopExternal = window.stopExternal
  keyboard.stopExternal = window.stopExternal

  # Load configuration
  config.load()

  # Connect slots and signals
  window.initSlots()

  # If application was started in tray, show notification
  if config.values["tray-on-startup"]:
    window.trayIcon.showMessage("Stream Clipping Utility","Application has started hidden in tray.",window.appIcon)
  else:
    window.show()
  threading.Thread(target=twitch.checkStatus,daemon=True).start()
  sys.exit(app.exec_())
