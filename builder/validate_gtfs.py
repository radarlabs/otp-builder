import os
import subprocess
import sys
import requests
import xml.etree.ElementTree as ET
from utils import downloadFile
from constants import SCRIPT_DIR
import tempfile


class ValidateGtfs:
    onebusawayJar = ''

    @staticmethod
    def checkAndDownloadMostRecentJar(prefix, path):
        url = f'{prefix}{path}/maven-metadata.xml'
        document = requests.get(url).content.decode('utf-8')
        tree = ET.fromstring(document)
        lst = tree.find('./versioning/release')
        latestVersion = lst.text

        artifactId = tree.find('./artifactId').text

        expectedJar = f'{artifactId}-{latestVersion}.jar'
        if not os.path.exists(expectedJar):
            downloadUrl = f'{prefix}{path}/{latestVersion}/{expectedJar}'
            print(f'downloading {expectedJar} @ {downloadUrl}')
            downloadFile(downloadUrl,
                         expectedJar)
            print(f'downloaded {expectedJar}')
        else:
            print(f'already had {expectedJar}')

        return expectedJar

    @staticmethod
    def checkAndDownloadJar():
        # ValidateGtfs.checkAndDownloadMostRecentJar(
        #     'https://repo1.maven.org/maven2/', 'com/conveyal/gtfs-lib')
        ValidateGtfs.onebusawayJar = ValidateGtfs.checkAndDownloadMostRecentJar(
            'http://nexus.onebusaway.org/nexus/content/repositories/public/',
            'org/onebusaway/onebusaway-gtfs-transformer-cli')
        print(ValidateGtfs.onebusawayJar)

    @staticmethod
    def checkForTransitFeed():
        # check if we've checked out transitfeed
        if not os.path.isdir('transitfeed'):
            print('Don\'t have transitfeed, checking out from git')
            subprocess.run([
                'git', 'clone', 'https://github.com/google/transitfeed',
                os.path.join(SCRIPT_DIR, 'transitfeed')
            ])  # doesn't capture output
        else:
            print('great, you have transitfeed')

    @staticmethod
    def downloadDeps():
        # ValidateGtfs.checkForTransitFeed()
        ValidateGtfs.checkAndDownloadJar()

    @staticmethod
    def validateWithTransitFeed(fileDest, logger):
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
        return True

    @staticmethod
    def validateWithOneBusAway(fileDest, logger):
        tmpFileName = ''
        with tempfile.NamedTemporaryFile(suffix='.zip') as tmp:
          tempFileName = tmp.name

        cmd = f'java -jar {ValidateGtfs.onebusawayJar} {fileDest} {tempFileName}'
        print(cmd)
        try:
            validatorOutput = subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, shell=True).decode()
            logger.info(validatorOutput)
            if os.path.exists(tempFileName):
              os.remove(tempFileName)
            return True
        except subprocess.CalledProcessError as e:
            validatorOutput = e.output.decode()
            import traceback
            traceback.print_exc()
            print(e)
            print(validatorOutput)
            return False

    @staticmethod
    def validate(fileDest, logger):
        logger.info(f'--> verifying {fileDest}')
        verifiedFilePath = os.path.join(
            os.path.split(fileDest)[0], '_VERIFIED')
        logger.info(f'looking for {verifiedFilePath}')
        if os.path.exists(verifiedFilePath):
            logger.info(f'already verified')
        else:
            logger.info(f'running gtfs verification')
            if not ValidateGtfs.validateWithOneBusAway(fileDest, logger):
                return False

        logger.info(
            f'verficiation successed, writing sentinel {verifiedFilePath}')
        open(verifiedFilePath, 'w').close()
        return True
