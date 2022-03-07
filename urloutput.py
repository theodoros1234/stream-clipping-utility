import os, platform, time

if platform.system() == "Windows":
  SEP = '\\'
else:
  SEP = '/'

class urlOutput():
  def __init__(self):
    self.f = None
    self.config = None
  
  def finalize_output(self):
    if os.path.exists(f"{self.f_path}{SEP}streamclippingutility_temp.txt"):
      self.f = open(self.f_path)
      timestamp = self.f.readline()[:-1]
      self.f.close()
      dst = f"{self.config.values['clips-file-path']=}{SEP=}{clipstimestamp=}.txt"
      os.rename(self.f_path,dst)
  
  def start(self):
    self.f_path = self.config.values['clips-file-path']+SEP+"streamclippingutility_temp.txt"
    self.finalize_output()
  
  def stop(self):
    pass
  
  def push(self,url):
    pass
