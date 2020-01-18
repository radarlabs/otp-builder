import json
import os
import sys
import termcolor

FEED_FILE = 'feeds.json'
FEED_DIR = 'feeds'
OTP_INPUT_DIR = 'input'
OTP_OUTPUT_DIR = 'graphs'
DEFAULT_GRAPH_NAME = 'default'
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


def get_feeds():
  if os.path.exists(FEED_FILE): 
    return json.loads(open(FEED_FILE).read())
  elif os.path.exists(os.path.join(SCRIPT_DIR, FEED_FILE)):
    return json.loads(open(os.path.join(SCRIPT_DIR, FEED_FILE)).read())
  else:
      print(colored(f'Missing feed file {FEED_FILE}', 'red'))
      sys.exit(1)
