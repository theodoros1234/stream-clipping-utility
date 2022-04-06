import os, platform, time


# Determine separator character depending on host OS
if platform.system() == "Windows":
  SEP = '\\'
else:
  SEP = '/'


# URL Output class
class urlOutput():
  def __init__(self):
    self.f = None
    self.f_path = None
    self.config = None
  
  # Moved temporary output file into a formatted file
  #def finalizeOutput(self):
    #if self.f_path == None:
      #self.f_path = self.config.values['clips-file-path']+SEP+"streamclippingutility_temp.txt"
    #if os.path.exists(f"{self.f_path}{SEP}streamclippingutility_temp.txt"):
      #if self.f == None or self.f.closed:
        #self.f = open(self.f_path,'r')
      #timestamp = self.f.readline()[:-1]
      #self.f.close()
      #dst = f"{self.config.values['clips-file-path']}{SEP}{clipstimestamp}.txt"
      #os.rename(self.f_path,dst)
  
  # Creates and opens file
  def start(self):
    self.f_path = self.config.values['clips-file-path'] + SEP + time.strftime("SCU_clip_output_%Y%m%d_%H%M%S.html")
    try:
      self.f = open(self.f_path,'w')
      self.f.write('<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
      self.f.write("<h1>Stream Clipping Utility</h1>\n")
      self.f.write("<h3>Clip edit links:</h3>\n")
      self.f.flush()
    except BaseException as e:
      self.exp(e)
  
  # Handles exceptions
  def exp(self, e):
    print(type(e).__name__,e)
    self.stopExternal("Clip URL Output: "+str(e))
  
  # Closes file
  def stop(self):
    self.f.close()
  
  # Adds a URL to the list
  def push(self,url):
    try:
      self.f.write(f'{time.asctime()} <a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a><br/>\n')
      self.f.flush()
    except BaseException as e:
      self.exp(e)
