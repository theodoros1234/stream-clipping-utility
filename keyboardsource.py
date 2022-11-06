#!/bin/python3
import keyboard, os, sys, platform, threading, subprocess, logging

# Keyboard listener/source object
class keyboardSource():
  
  def __init__(self):
    # The keyboard library requires root privileges on Linux.
    # If running on Linux without root, this will set a flag to run the script on a separate process as root
    self.__linux_root = False
    # Check if running on Linux
    if platform.system() == "Linux":
      # Check if not running as root
      if os.geteuid() != 0:
        # Set the flag
        self.__linux_root = True
        pass
    self.__stopping = False
    self.__proc_dead = False
    self.started_from_cmd = False
    self.config = None
    self.stopExternal = None
  
  # Converts string returned from QKeySequence to a string that the keyboard library can use, and sets the hotkey
  def setHotkey(self,key_seq):
    key_seq = str(key_seq)
    # Replace comma and plus symbols with whole words
    prev_plus = False
    i=0
    while i<len(key_seq):
      c = key_seq[i]
      # This is a key
      if prev_plus:
        prev_plus = False
        if c=='+':
          key_seq = key_seq[0:i] + "plus" + key_seq[i+1:]
          i+=3
        elif c==',':
          key_seq = key_seq[0:i] + "comma" + key_seq[i+1:]
          i+=4
      # This is a separator
      else:
        if c=='+':
          prev_plus = True
      i+=1
    self.__hotkey = key_seq
  
  # Monitors output of child process
  def __monitor_child(self):
    while self.__child_proc.poll() == None:
      cmd = self.__child_proc.stdout.readline().decode()[:-1]
      if cmd=='trigger':
        self.trigger()
    if self.__stopping==False:
      logging.critical("Child process ended unexpectedly.")
      self.__proc_dead = True
      if self.stopExternal == None:
        self.stop()
      else:
        self.stopExternal("Child process for keyboard monitoring ended unexpectedly.",isError=True)
  
  # Start listening for hotkey
  def start(self):
    self.__proc_dead = False
    self.__stopping = False
    # Get hotkey from config
    if self.config != None:
      self.setHotkey(self.config.values['key-combo'])
    if self.__linux_root:
      # Launch another instance of the script as root
      self.__child_proc = subprocess.Popen(["pkexec", sys.executable, "%s/keyboardsource.py"%(os.getcwd()), self.__hotkey], stdin=subprocess.PIPE,stdout=subprocess.PIPE)
      # Monitor stdout of the child process
      threading.Thread(target=self.__monitor_child).start()
    else:
      # Create hotkey listener
      self.__h_handle = keyboard.add_hotkey(self.__hotkey, self.trigger, suppress=True)
  
  # Stop listening for hotkey
  def stop(self):
    self.__stopping = True
    if self.__linux_root:
      # Send stop signal to child processs
      if self.__proc_dead==False:
        try:
          self.__child_proc.communicate("stop".encode("utf-8"),10)
        except subprocess.TimeoutExpired:
          self.__child_proc.kill()
          logging.warning("Child process didn't stop after 10 seconds, so it was killed.")
    else:
      # Stop listening for the hotkey
      keyboard.remove_hotkey(self.__h_handle)
    # If started from command line, exit
    if self.started_from_cmd:
      os._exit(70)

####################################################
# Code to interface through stdin/stdout for cases #
# where the script was run as  a separate instance #
####################################################

# Trigger handler
def __trigger_handler():
  print("trigger")
  sys.stdout.flush()

# Input handler
def __input_handler():
  running = True
  while running:
    cmd = None
    try:
      cmd = input()
    except KeyboardInterrupt:
      cmd = 'stop'
      print(cmd)
    except EOFError:
      cmd = 'stop'
      print(cmd)
    # Stops source object and listening for input
    if cmd=='stop':
      running=False
      source.stop()

if __name__ == "__main__":
  # Set up keyboard source object and start
  source = keyboardSource()
  source.setHotkey(sys.argv[1])
  source.trigger = __trigger_handler
  source.started_from_cmd = True
  source.start()
  
  __input_handler()
