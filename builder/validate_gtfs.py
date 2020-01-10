import os
import subprocess

class ValidateGtfs:
  @staticmethod
  def validate(fileDest, logger):
    logger.info(f'--> verifying {fileDest}')
    verifiedFilePath = os.path.join(os.path.split(fileDest)[0], '_VERIFIED')
    logger.info(f'looking for {verifiedFilePath}')
    if os.path.exists(verifiedFilePath):
      logger.info(f'already verified')
    else:
      logger.info(f'running gtfs verification')
      reportPath = fileDest + '-validate-report.html'
      cmd = f'python2 transitfeed/feedvalidator.py -n -o {reportPath} {fileDest}'
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

    logger.info(f'verficiation successed, writing sentinel {verifiedFilePath}')
    open(verifiedFilePath, 'w').close()
    return True