import requests
import json

def downloadFile(url, fileDest):
  r = requests.get(url)
  with open(fileDest, 'wb') as f:
    f.write(r.content)

def getJson(url):
  headers = {'Content-Type': 'application/json'}
  response = requests.get(url, headers=headers)
  if response.status_code == 200:
    return json.loads(response.content.decode('utf-8'))
  else:
    raise Exception(f'failed to fetch {url}')