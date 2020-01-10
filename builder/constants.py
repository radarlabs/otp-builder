FEED_FILE = 'feeds.json'
FEED_DIR = 'feeds'
OTP_INPUT_DIR = 'input'
OTP_OUTPUT_DIR = 'graphs'
DEFAULT_GRAPH_NAME = 'default'

import json

def get_feeds():
  return json.loads(open(FEED_FILE).read())