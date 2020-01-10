#!/usr/bin/env python

import os
import subprocess
import traceback
import pathlib # python 3.5
import requests
import sys
import shutil
import datetime
import concurrent.futures
import multiprocessing
from termcolor import colored

class SubLogger:
  def __init__(self, logger, name):
    self.name = name
    self.logger = logger
    self.lines = []

  def __del__(self):
    self.logger.write('\n'.join(self.lines))
  
  def info(self, line):
    self.lines.append(f'[{self.name}] - INFO - {line}')

  def error(self, line):
    print(colored(line, 'red'))
    self.lines.append(f'[{self.name}] - ERROR - {line}')

class MyWeirdLogger:
  def __init__(self, filename):
    self.filename = filename
    m = multiprocessing.Manager()
    self.writeLock = m.Lock()
    self.file = open(filename, 'w')

  def write(self, data):
    with self.writeLock:
      self.file.write(data)
      print(data)

  def getWriter(self, name):
    return SubLogger(self, name)


from api import transitfeeds
from constants import get_feeds, FEED_DIR, OTP_INPUT_DIR, OTP_OUTPUT_DIR, DEFAULT_GRAPH_NAME
from utils import downloadFile

sys.path.append('..')
from shared import download_otp
from shared.download_otp import CURRENT_OTP_JAR

globalLogger = None

def checkForTransitFeed():
  # check if we've checked out transitfeed
  if not os.path.isdir('transitfeed'):
    print('Don't have transitfeed, checkout out from git')
    subprocess.run(['git', 'clone', 'https://github.com/google/transitfeed'])  # doesn't capture output
  else:
    print('great, you have transitfeed')

def checkForPython2():
  try:
    subprocess.run('python2 --version', shell=True)
    print('great, you have python2')
  except:
    print(colored('transitfeed requires python2, stupid thing, which you don't have. gotta go get that. exiting', 'red'))
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

def downloadAndCheckFeedVersion_TransitFeeds(currentVersion, logger):
  print(logger)
  MISSING_VALUE = (False, None, None)
  title = currentVersion['f']['t']
  logger.info(f'looking at {title}')

  # no download url, return
  if 'url' not in currentVersion:
    logger.error('no download url, skipping')
    return MISSING_VALUE

  url = currentVersion['url']
  logger.info(url)
  errors = currentVersion['err']

  if len(errors) > 0:
    logger.error('This feed had errors, not processing')
    logger.error('\n'.join(['   ' + e for e in errors]))
    return MISSING_VALUE

  id = currentVersion['id']
  logger.info(id)
  feedDestDir = os.path.join(FEED_DIR, id)
  logger.info('--> downloading to %s' % feedDestDir)
  pathlib.Path(feedDestDir).mkdir(parents=True, exist_ok=True)

  DOWNLOAD_FILENAME = 'gtfs.zip'
  # download the file
  fileDest = os.path.join(feedDestDir, DOWNLOAD_FILENAME)
  expectedSize = currentVersion['size']

  shouldDownload = True

  if os.path.exists(fileDest):
    logger.info(f'{fileDest} already exists')
    currentSize = os.stat(fileDest).st_size
    if currentSize == expectedSize:
      logger.info(f'{fileDest} is the right size, not redownloading')
      shouldDownload = False
    else:
      logger.info(f'{fileDest} is the wrong size exp: {expectedSize} vs on-disk: {currentSize} - redownloading')

  if shouldDownload:
    try:
      downloadFile(url, fileDest)
      logger.info(f'downloaded fileDest')
    except:
      traceback.print_exc()
      print(colored(f'could not download {url}', 'red'))
      return MISSING_VALUE

  # verify feed
  logger.info(f'--> verifying {fileDest}')
  verifiedFilePath = os.path.join(feedDestDir, '_VERIFIED')
  logger.info(f'looking for {verifiedFilePath}')
  if os.path.exists(verifiedFilePath):
    logger.info(f'already verified {id}')
  else:
    logger.info(f'running gtfs verification')
    reportPath = fileDest + '-validate-report.html'
    cmd = f'python2 transitfeed/feedvalidator.py -n -o {reportPath} {fileDest}'
    try:
      validatorOutput = subprocess.check_output(cmd,
        stderr=subprocess.STDOUT,
        shell=True)
      logger.info(validatorOutput)
    except subprocess.CalledProcessError as e:
      validatorOutput = e.output.decode()
    
    logger.info(f'validatorOutput: {validatorOutput}')
    if 'errors found' in validatorOutput:
      logger.error('errors found')
      return MISSING_VALUE

  logger.info(f'verficiation successed, writing sentinel {verifiedFilePath}')
  open(verifiedFilePath, 'w').close()
  return (True, fileDest, id)

def downloadAndCheckFeed_TransitFeeds_FeedId(feedId):
  try:
    logger = globalLogger.getWriter('transitfeeds:%s' % feedId)

    feedResponse = transitfeeds.getFeedVersions(feedId)
    
    versions = feedResponse['results']['versions']
    title = ''
    
    if len(versions) == 0:
      logger.error(f'No feeds at all for {feedId}')
      return False
    
    for index, currentVersion in enumerate(versions):
      if not title:
        print('processing %s' % currentVersion['f']['t'])
      title = currentVersion['f']['t']
      (status, filepath, id) = downloadAndCheckFeedVersion_TransitFeeds(currentVersion, logger)
      if status:
        destFilename = id.replace('/', '-') + '-gtfs.zip'
        destPath = os.path.join(OTP_INPUT_DIR, destFilename)
        logger.info(f'got good version {id}, copying {filepath} to {destPath}')
        shutil.copyfile(filepath, destPath)
        return True
      if index > 5:
        logger.error(f'Not looking back more than five versions for {feedId}')

    print('feedid3')
    logger.error(f'No good versions for {feedId} - {title}')
    return False
  except:
    traceback.print_exc()
    

def downloadAndCheckFeed_TransitFeeds_Location(location):
  feeds = transitfeeds.getLocation(location)
  for f in feeds['results']['feeds']:
    downloadAndCheckFeed_TransitFeeds_FeedId(f['id'])

def downloadAndCheckFeed_TransitFeeds(feed):
  if 'location' in feed:
    downloadAndCheckFeed_TransitFeeds_Location(feed['location'])
  elif 'id' in feed:
    downloadAndCheckFeed_TransitFeeds_FeedId(feed['id'])
  else:
    print(colored(f'don't know how to parse transitfeeds feed {feed}', 'red'))
    sys.exit(1)

def checkOTP():
  download_otp.download()
      
def downloadFeed(feed):
  if feed['source'] == 'transitfeeds':
    downloadAndCheckFeed_TransitFeeds(feed)

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
    if os.path.exists(currentLinkPath):
      if os.path.islink(currentLinkPath):
        os.unlink(currentLinkPath)
        os.symlink(dateStr, currentLinkPath)
        print(f'linking to {currentLinkPath}')
        print(f'To check by hand run')
        print(f'  java -Xmx2G -jar {CURRENT_OTP_JAR} --router default --graphs graphs --server')
      else:
        print(colored(f'{currentLinkPath} is not a symlink, not removing and not updating', 'yellow'))
        print(f'To check by hand run')
        print(f'  java -Xmx2G -jar {CURRENT_OTP_JAR} --router {dateStr} --graphs graphs --server')
    
    print('check that it is working in nyc with')
    print('http://localhost:8080/otp/routers/default/plan?fromPlace=40.700853,-73.947738&toPlace=40.741524,%20-73.989330')

def main():
  # if we do this in the global scope there's a weird multiprocessing error, sorry, gross
  global globalLogger
  globalLogger = MyWeirdLogger('feed-import-%s.log' % datetime.datetime.now().strftime('%Y-%m-%d-%H-%M'))

  checkForTransitFeed()
  checkForPython2()
  checkDirectories()
  checkOTP()
  downloadFeeds()
  # runOTP(OTP_INPUT_DIR, OTP_OUTPUT_DIR)

if __name__ == '__main__':
    main()
