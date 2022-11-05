#!/bin/python3
# This Python file uses the following encoding: utf-8
import sys, threading
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
def stop():
  keyboard.stop()
  url_out.stop()


# Main function
if __name__ == "__main__":
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
  window.twitch = twitch
  window.startOthers = start
  window.stopOthers = stop
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
