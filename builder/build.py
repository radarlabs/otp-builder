#!/usr/bin/env python

import os
import subprocess
import traceback
import datetime
import requests
import sys
import shutil
import concurrent.futures
from termcolor import colored

from api import transitfeeds
from constants import get_feeds, FEED_DIR, OTP_INPUT_DIR, OTP_OUTPUT_DIR, DEFAULT_GRAPH_NAME
from utils import downloadFile

sys.path.append('..')
from shared import download_otp
from shared.download_otp import CURRENT_OTP_JAR

from mylogger import MyGlobalLogger

globalLogger = None

def checkForTransitFeed():
  # check if we've checked out transitfeed
  if not os.path.isdir('transitfeed'):
    print('Don\'t have transitfeed, checking out from git')
    subprocess.run(['git', 'clone', 'https://github.com/google/transitfeed'])  # doesn't capture output
  else:
    print('great, you have transitfeed')

def checkForPython2():
  try:
    subprocess.run('python2 --version', shell=True)
    print('great, you have python2')
  except:
    print(colored('transitfeed requires python2, stupid thing, which you don\'t have. gotta go get that. exiting', 'red'))
    sys.exit(1)

def checkDirectories():
  if not os.path.isdir(FEED_DIR):
    print('making feeds dir %s' % FEED_DIR)
    os.mkdir(FEED_DIR)
  else:
    print('great you have feeds dir %s' % FEED_DIR)

  # clean out our last build dir
  if os.path.isdir(OTP_INPUT_DIR):
    print(f'cleaning {OTP_INPUT_DIR}')
    shutil.rmtree(OTP_INPUT_DIR)
  print(f'making {OTP_INPUT_DIR}')
  os.mkdir(OTP_INPUT_DIR)  

  if not os.path.isdir(OTP_OUTPUT_DIR):
    print(f'making {OTP_OUTPUT_DIR}')
    os.mkdir(OTP_OUTPUT_DIR)  


def checkOTP():
  download_otp.download()
      
def downloadFeed(feed):
  if feed['source'] == 'transitfeeds':
    try:
      (status, log) = transitfeeds.TransitFeedDownloader(OTP_INPUT_DIR).downloadAndCheckFeed(feed)
      globalLogger.write(log)
    except:
      traceback.print_exc()

def downloadFeeds():
  print(get_feeds())
  with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    executor.map(downloadFeed, get_feeds()['feeds'])

def runOTP(otpInputDir, otpOutputDir):
  otpJarName = CURRENT_OTP_JAR.rsplit('/', 1)[-1]
  completedProcess = subprocess.run(['java', '-Xmx10G', '-jar', otpJarName, '--build', otpInputDir])
  if completedProcess.returncode != 0:
    print(colored('****************', 'red'))
    print(colored('OTP BUILD FAILED', 'red'))
    print(colored('****************', 'red'))
    sys.exit(1)

  GraphFileName = 'Graph.obj'
  graphFilePath = os.path.join(otpInputDir, GraphFileName)
  if os.path.exists(graphFilePath):
    print(f'built index at {graphFilePath}')

    # copy graph from otpInputDir/Graph.obj to OTP_OUTPUT_DIR/date_str/Graph.obj
    dateStr = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
    outputDir = os.path.join(otpOutputDir, dateStr)
    outputPath = os.path.join(outputDir, GraphFileName)
    os.mkdir(outputDir)
    shutil.copy(graphFilePath, outputPath)

    print(colored(f'All done at {outputPath}', 'green'))
    # symlink OTP_OUTPUT_DIR/datestr/ to OTP_OUTPUT_DIR/default/
    currentLinkPath = os.path.join(otpOutputDir, DEFAULT_GRAPH_NAME)
    if os.path.exists(currentLinkPath) and os.path.islink(currentLinkPath):
      os.unlink(currentLinkPath)

    print(f'To check by hand run')
    print(f'  java -Xmx10G -jar {CURRENT_OTP_JAR} --router {dateStr} --graphs graphs --server')    
    print('check that it is working in nyc with')
    print(f'http://localhost:8080/otp/routers/{dateStr}/plan?fromPlace=40.700853,-73.947738&toPlace=40.741524,%20-73.989330')

def main():
  global globalLogger
  globalLogger = MyGlobalLogger('feed-import-%s.log' % datetime.datetime.now().strftime('%Y-%m-%d-%H-%M'))
  checkForTransitFeed()
  checkForPython2()
  checkDirectories()
  checkOTP()
  downloadFeeds()
  runOTP(OTP_INPUT_DIR, OTP_OUTPUT_DIR)

if __name__ == '__main__':
    main()
