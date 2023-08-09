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
    self.looking_for_hotkey = False
    self.__stop_sign = None
  
  def hotkeyToString(self, scan_code, modifiers, hotkey_changing=False):
    string = []

    for modifier in modifiers:
      modifier = modifier.split(" ")
      for i in range(len(modifier)):
        modifier[i] = modifier[i].capitalize()
      string.append(" ".join(modifier))

    if scan_code != 0:
      if platform.system() == "Windows":
        string.append(list(keyboard._os_keyboard.get_event_names(scan_code, 0, False, []))[0])
      elif platform.system() == "Linux":
        if len(keyboard._os_keyboard.to_name)==0:
          keyboard._os_keyboard.init()
        string.append(keyboard._os_keyboard.to_name[(scan_code, ())][0])
    elif hotkey_changing:
      string.append("...")

    if not hotkey_changing and len(string)==0:
      return "Not set"
    return " + ".join(string)

  # Gets hotkey from user, informs the UI about the hotkey and saves to config file
  def newHotkey(self, setLabel, finish):
    if self.looking_for_hotkey == True:
      logging.error("keyboardSource.newHotkey triggered when there was already a hotkey being set")
      finish()
      return
    event, modifiers = None, None
    self.looking_for_hotkey = True
    setLabel("...")

    while self.looking_for_hotkey:
      event = keyboard.read_event()
      logging.debug("Hotkey: " + event.to_json())
      if self.looking_for_hotkey:
        modifiers = []
        if keyboard.is_pressed("win"):
          modifiers.append("win")
        if keyboard.is_pressed("ctrl"):
          modifiers.append("ctrl")
        if keyboard.is_pressed("alt"):
          modifiers.append("alt")
        if keyboard.is_pressed("shift"):
          modifiers.append("shift")

        if event.event_type == keyboard.KEY_DOWN and not keyboard.is_modifier(event.scan_code):
          self.config.values["key-combo-v2"] = (modifiers, event.scan_code)
          finish()
          self.looking_for_hotkey = False
          self.config.save()
        else:
          setLabel(self.hotkeyToString(0, modifiers, True))

  # Cancels getting a new hotkey
  def cancelHotkey(self):
    self.looking_for_hotkey = False

  # Listens for the hotkey being pressed
  def __hotkey_listener(self, hotkey, stop_sign):
    modifier_win = "win" in hotkey[0]
    modifier_ctrl = "ctrl" in hotkey[0]
    modifier_alt = "alt" in hotkey[0]
    modifier_shift = "shift" in hotkey[0]

    while stop_sign[0]:
      event = keyboard.read_event()
      if stop_sign[0]:
        if event.event_type == keyboard.KEY_DOWN and \
           event.scan_code == hotkey[1] and \
           keyboard.is_pressed("win") == modifier_win and \
           keyboard.is_pressed("ctrl") == modifier_ctrl and \
           keyboard.is_pressed("alt") == modifier_alt and \
           keyboard.is_pressed("shift") == modifier_shift:
             self.trigger()


  # Converts string returned from QKeySequence to a string that the keyboard library can use, and sets the hotkey
  # def setHotkey(self,key_seq):
  #   key_seq = str(key_seq)
  #   # Replace comma and plus symbols with whole words
  #   prev_plus = False
  #   i=0
  #   while i<len(key_seq):
  #     c = key_seq[i]
  #     # This is a key
  #     if prev_plus:
  #       prev_plus = False
  #       if c=='+':
  #         key_seq = key_seq[0:i] + "plus" + key_seq[i+1:]
  #         i+=3
  #       elif c==',':
  #         key_seq = key_seq[0:i] + "comma" + key_seq[i+1:]
  #         i+=4
  #     # This is a separator
  #     else:
  #       if c=='+':
  #         prev_plus = True
  #     i+=1
  #   self.__hotkey = key_seq
  
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
  def start(self, custom_combo=None):
    self.__proc_dead = False
    self.__stopping = False

    # Override key combo from config if one is given as an argument (done when called as an external process)
    if custom_combo == None:
      key_combo = self.config.values["key-combo-v2"]
    elif type(custom_combo) == tuple and len(custom_combo) == 2 and type(custom_combo[0]) == list and type(custom_combo[1]) == int:
      key_combo = custom_combo
    else:
      print("ERROR: Invalid key combination given.")
      os.exit(1)

    # Get hotkey from config
    if self.__linux_root:
      # Launch another instance of the script as root
      self.__child_proc = subprocess.Popen(["pkexec", sys.executable, "%s/keyboardsource.py"%(os.getcwd())] + key_combo[0] + [str(key_combo[1])], stdin=subprocess.PIPE,stdout=subprocess.PIPE)
      # Monitor stdout of the child process
      threading.Thread(target=self.__monitor_child).start()
    else:
      # Start hotkey listener
      self.__stop_sign = [True]
      threading.Thread(target=self.__hotkey_listener, args=(key_combo, self.__stop_sign), daemon=True).start()
      # self.__h_handle = keyboard.add_hotkey(self.__hotkey, self.trigger, suppress=True)
  
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
      # Stop hotkey listener
      self.__stop_sign[0] = False
      #keyboard.remove_hotkey(self.__h_handle)
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
  #source.setHotkey(sys.argv[1])
  key_combo_v2 = (sys.argv[1:-1], int(key_combo_v2[-1]))
  source.trigger = __trigger_handler
  source.started_from_cmd = True
  source.start(key_combo_v2)
  
  __input_handler()
