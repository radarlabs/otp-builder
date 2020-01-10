import sys
import os
import json
import requests
import traceback
import pathlib
import shutil

from dotenv import load_dotenv
load_dotenv()

from utils import getJson, downloadFile

from termcolor import colored

from constants import get_feeds, FEED_DIR, OTP_INPUT_DIR, OTP_OUTPUT_DIR, DEFAULT_GRAPH_NAME

from mylogger import SubLogger
from validate_gtfs import ValidateGtfs
from termcolor import colored


TRANSITFEEDS_API_KEY = os.getenv("TRANSITFEEDS_API_KEY")
if not TRANSITFEEDS_API_KEY:
  print(colored('TRANSITFEEDS_API_KEY not specified in .env or shell env', 'red'))
  sys.exit(1)

def getFeedVersions(feedId):
  api_url = f'https://api.transitfeeds.com/v1/getFeedVersions?key={TRANSITFEEDS_API_KEY}&feed={feedId}&page=1&limit=10&err=1&warn=1'
  return getJson(api_url)

def getLocation(location):
  api_url = f'https://api.transitfeeds.com/v1/getFeeds?key={TRANSITFEEDS_API_KEY}&location={location}&descendants=1&page=1&limit=100'
  return getJson(api_url)

class TransitFeedDownloader:
  def __init__(self, destDir):
    self.destDir = destDir

  def downloadAndCheckFeed(self, feed):
    if 'location' in feed:
      subfeedResponses = self.downloadAndCheckFeed_Location(feed['location'])
      logString = '\n'.join([r[1] for r in subfeedResponses])
      retVal = True in [r[0] for r in subfeedResponses]
      return (retVal, logString)
    elif 'id' in feed:
      return self.downloadAndCheckFeed_FeedId(feed['id'])
    else:
      print(colored(f'don\'t know how to parse transitfeeds feed {feed}', 'red'))
      sys.exit(1)

  def downloadAndCheckFeed_Location(self, location):
    feeds = getLocation(location)
    
    gtfsFeeds = [f for f in feeds['results']['feeds'] if f['ty'] == 'gtfs']

    return [self.downloadAndCheckFeed_FeedId(f['id']) for f in gtfsFeeds]

  def downloadAndCheckFeed_FeedId(self, feedId):
    try:
      logger = SubLogger('transitfeeds:%s' % feedId)

      feedResponse = getFeedVersions(feedId)
      
      versions = feedResponse['results']['versions']
      title = ''
      
      if len(versions) == 0:
        logger.error(f'No feeds at all for {feedId}')
        return (False, logger.toString())
      
      for index, currentVersion in enumerate(versions):
        if not title:
          print('processing %s' % currentVersion['f']['t'])
        title = currentVersion['f']['t']
        (status, filepath, id) = self.downloadAndCheckFeedVersion(currentVersion, logger)
        if status:
          destFilename = id.replace('/', '-') + '-gtfs.zip'
          destPath = os.path.join(self.destDir, destFilename)
          logger.info(f'got good version {id}, copying {filepath} to {destPath}')
          shutil.copyfile(filepath, destPath)
          return (True, logger.toString())
        if index > 5:
          logger.error(f'Not looking back more than five versions for {feedId}')

      logger.error(f'No good versions for {feedId} - {title}')
      return (False, logger.toString())
    except:
      traceback.print_exc()
      return (False, traceback.print_exc())
    

  def downloadAndCheckFeedVersion(self, currentVersion, logger):
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
      logger.error(f'Feed {title} @ {url} had errors according to transitfeeds, not processing')
      logger.error('\n'.join([f'   {e}' for e in errors]))
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
    if not ValidateGtfs.validate(fileDest, logger):
        return MISSING_VALUE

    return (True, fileDest, id)
