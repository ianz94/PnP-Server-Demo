# PnP device states
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
    'INSTALL_GUESTSHELL',
    'ENABLE_GUESTSHELL',
    'RUN_PY_SCRIPT',
    'FINISHED'
]

PNP_STATE = {state: idx for idx, state in enumerate(PNP_STATE_LIST)}


class SoftwareImage:
    """Represents a Cisco IOS-XE software image"""
    def __init__(self, image: str):
        self.image: str = image
        self.md5: str = ''


class Device:
    """Represents a Cisco network device being provisioned"""
    def __init__(self, udi: str, platform: str, hw_rev: str, serial_number: str, 
                 first_seen: str, last_contact: str, src_address: str):
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
        self.is_configured: bool = False
        self.has_GS_tarball: bool = False
        self.has_PY_script: bool = False

    def get_state_name(self) -> str:
        """Return the textual representation of the current device state"""
        return PNP_STATE_LIST[self.pnp_state]
