import os
import subprocess
import sys
import requests
import xml.etree.ElementTree as ET
from utils import downloadFile
from constants import SCRIPT_DIR

class ValidateGtfs:
  @staticmethod
  def checkAndDownloadJar():
    url = 'https://repo1.maven.org/maven2/com/conveyal/gtfs-lib/maven-metadata.xml'
    document = requests.get(url).content.decode('utf-8')
    tree = ET.fromstring(document)
    lst = tree.find('./versioning/latest')
    latestVersion = lst.text

    expectedJar = f'gtfs-lib-{latestVersion}-shaded.jar'
    if not os.path.exists(expectedJar):
      print(f'downloading {expectedJar}')
      downloadFile(
        f'https://repo1.maven.org/maven2/com/conveyal/gtfs-lib/{latestVersion}/{expectedJar}',
        expectedJar)
      print(f'downloaded {expectedJar}')
    else:
      print(f'already had {expectedJar}')
    
    return expectedJar

  @staticmethod
  def downloadDeps():
    latestJar = ValidateGtfs.checkAndDownloadJar()

  @staticmethod
  def validate(fileDest, logger):
    logger.info(f'--> verifying {fileDest}')
    verifiedFilePath = os.path.join(os.path.split(fileDest)[0], '_VERIFIED')
    logger.info(f'looking for {verifiedFilePath}')
    if os.path.exists(verifiedFilePath):
      logger.info(f'already verified')
    else:
      logger.info(f'running gtfs verification')
      reportPath = fileDest + '-validate-report.html'
      cmd = f'python2 {SCRIPT_DIR}/transitfeed/feedvalidator.py -n -o {reportPath} {fileDest}'
      try:
        validatorOutput = subprocess.check_output(cmd,
          stderr=subprocess.STDOUT,
          shell=True).decode()
        logger.info(validatorOutput)
      except subprocess.CalledProcessError as e:
        validatorOutput = e.output.decode()
      
      logger.info(f'validatorOutput: {validatorOutput}')
      if 'errors found' in validatorOutput:
        logger.error('errors found')
        return False

    logger.info(f'verficiation successed, writing sentinel {verifiedFilePath}')
    open(verifiedFilePath, 'w').close()
    return True
