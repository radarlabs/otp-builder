import multiprocessing
from termcolor import colored

Logger = None

class SubLogger:
  def __init__(self, name):
    self.name = name
    self.lines = []

  def toString(self):
    return '\n'.join(self.lines)
  
  def info(self, line):
    self.lines.append(f'[{self.name}] - INFO - {line}')

  def error(self, line):
    print(colored(line, 'red'))
    self.lines.append(f'[{self.name}] - ERROR - {line}')

class MyGlobalLogger:
  def __init__(self, filename):
    self.filename = filename
    m = multiprocessing.Manager()
    self.writeLock = m.Lock()
    self.file = open(filename, 'w')

  def write(self, data):
    with self.writeLock:
      self.file.write(data + '\n')
      print(data)
      self.file.flush()
