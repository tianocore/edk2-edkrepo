import errno
import os
import re
import logging

from datetime import date
from colorama import init, Fore

from edkrepo.common.humble import DISK_SPACE_ERROR
from edkrepo.config.config_factory import GlobalUserConfig

init(autoreset=True)

class ColorFormatter(logging.Formatter):
    COLORS = {
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        if color:
            record.asctime = color + record.asctime
            record.msg = color + record
        return logging.Formatter.format(self, record)


class CustomHandler(logging.StreamHandler):
    def write(self, stream, msg):
        try:
            stream.write(msg)
        except OSError as e:
            if e.errno == errno.ENOSPC:
                logger.info(DISK_SPACE_ERROR.format(path))

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            if hasattr(record, 'verbose') and record.verbose:
                self.write(stream, msg)
            if hasattr(record, 'normal') and record.normal:
                self.write(stream, msg)
        except:
            self.handleError(record)

class fileFormatter(logging.Formatter):
    def format(self, record):
        if record.msg != "":
            msg = logging.Formatter.format(self, record)
            colorCodeEscape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            plainMsg = colorCodeEscape.sub('', msg)
            return plainMsg
        return ""


def get_logger():
    return logger

config = GlobalUserConfig()

logFormatter = logging.Formatter("%(message)s\n")
logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)

folder_name = date.today().strftime("%Y/%m/%d_logs").split('/')
folder_name = '-'.join(folder_name)
path = os.path.join(config.logs_path, folder_name)

try:
    os.makedirs(path, exist_ok=True)
    fileHandler = logging.FileHandler("{}/log.log".format(path))
except OSError as e:
        if e.errno == errno.ENOSPC:
            logger.info(DISK_SPACE_ERROR.format(path))

formatter = fileFormatter("%(asctime)s.%(msecs)03d %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

consoleHandler = CustomHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)