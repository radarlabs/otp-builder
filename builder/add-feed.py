#!/usr/bin/env python
from api import transitfeeds
from constants import FEED_FILE
from utils import getJson
from urllib.parse import urlparse

# http://transitfeeds.com/p/mta/79

import sys
import json

def addEntry(entry):
  feeds = json.load(open(FEED_FILE))
  feeds['feeds'].append(entry)
  open(FEED_FILE, 'w').write(json.dumps(feeds, indent=4))

def addUrl_TransitFeeds_FeedId(url):
  feedId = '/'.join(url.split('/')[-2:])
  print(feedId)

  feedResponse = transitfeeds.getFeedVersions(feedId)
  title = feedResponse['results']['versions'][0]['f']['t']
  addEntry({
    'id': feedId,
    'title': title,
    'source': 'transitfeeds',
    'originalUrl': url
  })

def addUrl_TransitFeeds_Location(url):
  location = url.split('/')[-1]
  print(location)

  # just to make sure it exists for now
  feedResponse = transitfeeds.getLocation(location)

  addEntry({
    'location': location,
    # 'title': title,
    'source': 'transitfeeds',
    'originalUrl': url
  })

def addUrl_TransitFeeds(url):
  url = url.replace('http:', 'https:')
  path = urlparse(url).path
  pathParts = path.split('/')[1:]
  print(pathParts)
  # http://transitfeeds.com/p/mta/86
  if pathParts[0] == 'p':
    if len(pathParts) == 2:
      print("can't parse agencies yet")
      sys.exit(1)
    elif len(pathParts) == 3:
      addUrl_TransitFeeds_FeedId(url)
    else:
      print(f"no idea why there are so many parts here, exiting {pathParts}")
      sys.exit(1)
  elif pathParts[0] == 'l':
    addUrl_TransitFeeds_Location(url)
  else:
    print('Only know how to parse transitfeeds/openmobility feeds by operator')
    sys.exit(1)

def addUrl_TransitLand_Operator(url):
  operator = url.split('/')[-1]

  operatorResponse = getJson(f'https://api.transit.land/api/v1/operators/{operator}')
  onestopIds = operatorResponse['represented_in_feed_onestop_ids']
  addEntry({
    'operator': operator,
    'title': operatorResponse['name'],
    'onestopIds': onestopIds,
    'source': 'transitland'
  })


def addUrl_TransitLand(url):
  url = url.replace('http:', 'https:')
  if 'https://www.transit.land/feed-registry/operators/' in url:
    addUrl_TransitLand_Operator(url)
  else:
    print('Only know how to parse transitland feeds by operator')
    sys.exit(1)


def main():
  url = sys.argv[-1]
  print('got url', url)
  url = url.replace('openmobilitydata.org', 'transitfeeds.com')
  if 'transitfeeds.com' in url:
    addUrl_TransitFeeds(url)
  elif 'transit.land' in url:
    addUrl_TransitLand(url)
  else:
    print(f'unknown domain in {url} only know about transitfeeds.com/openmobilitydata.org and transit.land')
  

if __name__ == "__main__":
  main()