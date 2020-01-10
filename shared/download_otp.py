#!/usr/bin/env python
import requests
import os
import sys

CURRENT_OTP_JAR_URL = 'https://repo1.maven.org/maven2/org/opentripplanner/otp/1.4.0/otp-1.4.0-shaded.jar'
CURRENT_OTP_JAR = CURRENT_OTP_JAR_URL.split('/')[-1]


def download():
  url = CURRENT_OTP_JAR_URL
  fileDest = CURRENT_OTP_JAR
  if not os.path.exists(fileDest):
    print(f'downloading {CURRENT_OTP_JAR_URL} to {fileDest}')
    r = requests.get(url)
    with open(fileDest, 'wb') as f:
      f.write(r.content)
  else:
    print(f'already had {CURRENT_OTP_JAR_URL} at {fileDest}')

if __name__ == "__main__":
    if sys.argv[-1] == 'name':
        print(CURRENT_OTP_JAR)
    else:
        download()

