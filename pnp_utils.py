import logging
import hashlib
from logging.handlers import RotatingFileHandler
from sys import stdout


PNP_STATE_LIST = [
    'NONE',
    'NEW_DEVICE',
    'CONFIG_REG',
    'CHECK_IMAGE_VER',
    'UPGRADE_NEEDED',
    'UPGRADE_INPROGRESS',
    'UPGRADE_RELOAD_NEEDED',
    'UPGRADE_RELOADING',
    'UPGRADE_DONE',
    'GS_TARBALL_TRANSFER',
    'PY_SCRIPT_TRANSFER',
    'CONFIG_START',
    'CONFIG_SAVE_STARTUP',
    'CHECK_BOOTFLASH_SIZE',
    'BOOTFLASH_NO_SPACE',
    'RUN_EVENT_MANAGER',
    'WAIT_FOR_GUESTSHELL',
    'CHECK_GUESTSHELL',
    'RUN_PY_SCRIPT',
    'FINISHED'
]
PNP_STATE = {STR:IDX for IDX,STR in enumerate(PNP_STATE_LIST)}


class SoftwareImage:
    def __init__(self, image: str):
        self.image: str = image
        self.md5: str = ''


class Device:
    def __init__(self, udi: str, platform: str, hw_rev: str, serial_number: str, first_seen: str, last_contact: str,
                 src_address: str):
        self.udi: str = udi
        self.platform: str = platform
        self.hw_rev: str = hw_rev
        self.serial_number: str = serial_number
        self.ip_address: str = src_address
        self.first_seen: str = first_seen
        self.last_contact: str = last_contact
        
        self.pnp_state: int = PNP_STATE['NONE']
        self.version: str = ''
        self.image: str = ''
        self.target_image: SoftwareImage = None
        self.is_configured: bool = False
        self.has_GS_tarball: bool = False
        self.has_PY_script: bool = False

def configure_logger(path: str, log_to_console: bool):
    # # Disable FLASK console output
    logging.getLogger("werkzeug").disabled = True
    
    # Define our own logger
    log_formatter = logging.Formatter('%(asctime)s :: %(name)s :: %(message)s\n')
    log = logging.getLogger('pnp_server')
    log.setLevel(logging.INFO)

    log_file = path
    # Write logs to a file, rotate it when it reaches 5MB
    log_handler_file = RotatingFileHandler(
        log_file,
        mode='a',
        maxBytes=5 * 1024 * 1024,
        backupCount=10
    )

    log_handler_file.setFormatter(log_formatter)
    log_handler_file.setLevel(logging.INFO)
    log.addHandler(log_handler_file)

    if log_to_console:
        log_handler_console = logging.StreamHandler(stdout)
        log_handler_console.setFormatter(log_formatter)
        log_handler_console.setLevel(logging.INFO)
        log.addHandler(log_handler_console)


def log_info(message: str):
    log = logging.getLogger('pnp_server')
    log.info(message)


def calculate_md5(filepath):
    try:
        with open(filepath, mode='rb') as file:
            md5_hash = hashlib.md5()
            while chunk := file.read(8192):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except FileNotFoundError:
        print(f"The file '{filepath}' does not exist!")
        exit(1)
