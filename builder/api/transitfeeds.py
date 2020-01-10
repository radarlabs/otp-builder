import sys
import os
import json
import requests

from dotenv import load_dotenv
load_dotenv()

from utils import getJson

TRANSITFEEDS_API_KEY = os.getenv("TRANSITFEEDS_API_KEY")
if not TRANSITFEEDS_API_KEY:
  print('TRANSITFEEDS_API_KEY not specified in .env or shell env')
  sys.exit(1)


def getFeedVersions(feedId):
  api_url = f'https://api.transitfeeds.com/v1/getFeedVersions?key={TRANSITFEEDS_API_KEY}&feed={feedId}&page=1&limit=10&err=1&warn=1'
  print(api_url)
  return getJson(api_url)

def getLocation(location):
  api_url = f'https://api.transitfeeds.com/v1/getFeeds?key={TRANSITFEEDS_API_KEY}&location={location}&descendants=1&page=1&limit=100'
  return getJson(api_url)