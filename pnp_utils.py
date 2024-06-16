PNP_STATE_LIST = [
    'NONE',
    'NEW_DEVICE',
    'INFO',
    'CONFIG_START',
    'CONFIG_RUN',
    'CONFIG_SAVE_STARTUP',
    'UPGRADE_NEEDED',
    'UPGRADE_INPROGRESS',
    'UPGRADE_RELOAD',
    'UPGRADE_DONE',
    'FINISHED'
]
PNP_STATE = {STR:IDX for IDX,STR in enumerate(PNP_STATE_LIST)}


class SoftwareImage:
    def __init__(self, image: str, version: str, md5: str, size: int):
        self.image: str = image
        self.version: str = version
        self.md5: str = md5
        self.size: int = size


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
