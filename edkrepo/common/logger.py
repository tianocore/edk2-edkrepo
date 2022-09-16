import re
import logging

from colorama import init, Fore


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
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            if hasattr(record, 'verbose') and record.verbose:
                stream.write(msg)
            if hasattr(record, 'normal') and record.normal:
                stream.write(msg)
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


logFormatter = logging.Formatter("%(message)s\n")
logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)


fileHandler = logging.FileHandler("log.log")

formatter = fileFormatter("%(asctime)s.%(msecs)03d %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

consoleHandler = CustomHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
