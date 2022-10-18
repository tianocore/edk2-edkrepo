import os
import re
import git
import sys
import time
import errno
import string
import logging

from colorama import init
from datetime import date

from edkrepo.common.humble import LINE_BREAK, REMOVE_LOG_FAILED, DISK_SPACE_ERROR
from edkrepo.common.pathfix import expanduser
from edkrepo.common.edkrepo_exception import EdkrepoLogsRemoveException
from edkrepo.config.config_factory import GlobalUserConfig

init(autoreset=True)

class CustomFormatter(logging.Formatter):
    yellow = "\x1b[33;1m"
    red = "\x1b[31;20m"
    white = "\x1b[37;10m"
    FORMATS = {
        logging.INFO: white,
        logging.WARNING: yellow,
        logging.ERROR: red
    }

    def format(self, record):
        format_ = "%(message)s\n"
        if not hasattr(record, 'normal') and not hasattr(record, 'verbose'):
            record.normal = True

        if hasattr(record, 'safe') and record.safe:
            safe_str = ''
            for char in record.msg:
                if char not in string.printable:
                    char = '?'
                safe_str = ''.join((safe_str, str(char)))
            record.msg = safe_str if safe_str != '' else record.msg

        if hasattr(record,'header') and record.header:
            format_ = "%(levelname)s: %(message)s\n"

        color = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter("{}{}".format(color, format_))
        return formatter.format(record)

class CustomHandler(logging.StreamHandler):
    def write(self, stream, msg):
        try:
            stream.write(msg)
        except OSError as e:
            if e.errno == errno.ENOSPC:
                logger.info(DISK_SPACE_ERROR.format(os.path.join(config.logs_path, file_name)) + ".log")

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
            if record.msg == LINE_BREAK:
                return record.msg
            msg = logging.Formatter.format(self, record)
            colorCodeEscape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            plainMsg = colorCodeEscape.sub('', msg)
            return plainMsg
        return record.msg

def clear_logs():
    SECONDS_IN_A_DAY = 86400
    if os.path.exists(config.logs_path):
        for file in os.listdir(config.logs_path):
            file_path = os.path.join(config.logs_path, file)
            if os.stat(file_path).st_mtime < time.time() - config.logs_retention_period * SECONDS_IN_A_DAY:
                try:
                    os.remove(file_path)
                except EdkrepoLogsRemoveException as e:
                    logger.info(REMOVE_LOG_FAILED.format(file_path), extra={'normal': False})

def get_logger():
    return logger


def get_formatted_git_output(output_data, verbose=False):
    """
    Displays output from GitPython git commands

    output_data - Output from the git.execute method
    verbose     - Enable verbose messages
    """
    out, verbose_out = "", []
    if verbose and output_data[0]:
        verbose_out.append(output_data[0])
    if output_data[1]:
        out += output_data[1]
    if verbose and output_data[2]:
        verbose_out.append(output_data[2])
    return out, verbose_out

def init_color_console(force_color_output):
    config = git.GitConfigParser(os.path.normpath(expanduser("~/.gitconfig")))
    config_color = config.get("color", "ui", fallback="auto")
    strip = not sys.stdout.isatty()
    convert = sys.stdout.isatty()
    if force_color_output or config_color == "always":
        strip = False
    elif config_color == "false":
        strip = True
        convert = False
    if os.name == 'posix':
        # Never convert on Linux.  Setting it to False seems to cause problems.
        convert=None
    init(strip=strip, convert=convert, autoreset=True)
    return strip, convert

config = GlobalUserConfig()
clear_logs()
logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)

file_name = date.today().strftime("%Y/%m/%d_logs").split('/')
file_name = '-'.join(file_name)

fileHandler = logging.FileHandler("{}/{}.log".format(config.logs_path, file_name))

formatter = fileFormatter("%(asctime)s.%(msecs)03d %(levelname)s: %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

consoleHandler = CustomHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)