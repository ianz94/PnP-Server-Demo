from time import strftime
from flask import Flask, request, send_from_directory, render_template, Response
from apscheduler.schedulers.background import BackgroundScheduler
from requests import head
import xmltodict
import pnp_env
from pnp_utils import PNP_STATE_LIST, PNP_STATE, Device, SoftwareImage, configure_logger, log_info, log_error, calculate_md5
from csv_file_utils import read_device_status_from_csv_file, update_device_status_to_csv_file
from db_utils import init_db, read_device_status_from_db, write_device_status_into_db, save_device_status

def pnp_device_info(udi: str, correlator: str, info_type: str) -> str:
    # info_type can be one of:
    # image, hardware, filesystem, udi, profile, all
    jinja_context = {
        'udi': udi,
        'correlator': correlator,
        'info_type': info_type
    }
    _template = render_template('device_info.xml', **jinja_context)
    log_info(_template)
    return _template


def pnp_install_image(udi: str, correlator: str) -> str:
    device = devices[udi]
    response = head(f'http://localhost/images/{target_image.image}')
    if response.status_code == 200:
        device.pnp_state = PNP_STATE['UPGRADE_INPROGRESS']
        jinja_context = {
            'udi': udi,
            'correlator': correlator,
            'base_url': pnp_env.image_url,
            'image_name': target_image.image,
            'md5': target_image.md5.lower(),
            'destination': 'bootflash'
        }
        _template = render_template('image_install.xml', **jinja_context)
        log_info(_template)
        return _template
    else:
        log_error(f'Image file {pnp_env.image_url}/{target_image.image} does not exist')
        return ''


def pnp_config_upgrade(udi: str, correlator: str) -> str:
    device = devices[udi]
    cfg_file = f'{device.serial_number}.cfg'
    response = head(f'http://localhost/configs/{cfg_file}')
    if response.status_code != 200:  # SERIAL.cfg not found
        if pnp_env.default_cfg_exists:
            cfg_file = pnp_env.default_cfg_filename
            response = head(f'http://localhost/configs/{cfg_file}')
            if response.status_code != 200:  # default.cfg also not found
                log_error(f'Config file {pnp_env.config_url}/{cfg_file} does not exist')
                return ''
        else:
            log_error(f'Config file {pnp_env.config_url}/{cfg_file} does not exist')
            return ''
    device.pnp_state = PNP_STATE['CONFIG_START']
    jinja_context = {
        'udi': udi,
        'correlator': correlator,
        'base_url': pnp_env.config_url,
        'config_filename': cfg_file,
    }
    _template = render_template('config_upgrade.xml', **jinja_context)
    log_info(_template)
    return _template


def pnp_cli_config(udi: str, correlator: str, command: str) -> str:
    jinja_context = {
        'udi': udi,
        'correlator': correlator,
        'command': command
    }
    _template = render_template('cli_config.xml', **jinja_context)
    log_info(_template)
    return _template


def pnp_cli_exec(udi: str, correlator: str, command: str) -> str:
    jinja_context = {
        'udi': udi,
        'correlator': correlator,
        'command': command
    }
    _template = render_template('cli_exec.xml', **jinja_context)
    log_info(_template)
    return _template


def pnp_transfer_file(udi: str, file_name: str, correlator: str, destination='bootflash:') -> str:
    response = head(f'http://localhost/files/{file_name}')
    if response.status_code == 200:
        jinja_context = {
            'udi': udi,
            'correlator': correlator,
            'base_url': pnp_env.file_url,
            'file_name': file_name,
            'destination': destination
        }
        _template = render_template('file_transfer.xml', **jinja_context)
        log_info(_template)
        return _template
    else:
        log_error(f'File {pnp_env.file_url}/{file_name} does not exist')
        return ''


def pnp_backoff(udi: str, correlator: str, minutes: int) -> str:
    seconds = 0
    hours = 0
    jinja_context = {
        'udi': udi,
        'correlator': correlator,
        'seconds': seconds,
        'minutes': minutes,
        'hours': hours,
    }
    _template = render_template('backoff.xml', **jinja_context)
    log_info(_template)
    return _template


def pnp_bye(udi: str, correlator: str) -> str:
    jinja_context = {
        'udi': udi,
        'correlator': correlator,
    }
    _template = render_template('bye.xml', **jinja_context)
    log_info(_template)
    return _template


def create_new_device(udi: str, src_addr: str):
    # sample udi="PID:C1131-8PWB,VID:V01,SN:FGL2548L0AW"
    _udi = udi.split(',')
    platform = _udi[0].split(':')[1]
    hw_rev = _udi[1].split(':')[1]
    serial_number = _udi[2].split(':')[1]

    devices[udi] = Device(
        udi=udi,
        first_seen=strftime(pnp_env.time_format),
        last_contact=strftime(pnp_env.time_format),
        src_address=src_addr,
        serial_number=serial_number,
        platform=platform,
        hw_rev=hw_rev
    )
    devices[udi].pnp_state = PNP_STATE['NEW_DEVICE']


def update_device_info(data: dict):
    try:
        udi = data['pnp']['@udi']
        device = devices[udi]
        
        if ('imageInfo' in data['pnp']['response'] and 
            'versionString' in data['pnp']['response']['imageInfo'] and
            'imageFile' in data['pnp']['response']['imageInfo']):
            device.version = data['pnp']['response']['imageInfo']['versionString'].strip()
            device.image = data['pnp']['response']['imageInfo']['imageFile'].split(':')[1]
            
        device.last_contact = strftime(pnp_env.time_format)
        # Save to database immediately
        save_device_status(device)
    except (KeyError, AttributeError) as e:
        log_error(f"Error updating device info: {e}")


def check_update(udi: str):
    device = devices[udi]
    if device.image == target_image.image:
        device.pnp_state = PNP_STATE['UPGRADE_DONE']
    else:
        device.pnp_state = PNP_STATE['UPGRADE_NEEDED']


def check_bootflash_freespace(response: dict) -> bool:
    if ('fileSystemList' in response and
        'fileSystem' in response['fileSystemList'] and
        '@freespace' in response['fileSystemList']['fileSystem'] and
        int(response['fileSystemList']['fileSystem']['@freespace']) < 1026107392):
        log_error(f'Not enough space in bootflash: {response["fileSystemList"]["fileSystem"]["@freespace"]} bytes, need 1026107392 bytes')
        return False
    else:
        log_info(f'Sufficient space in bootflash to install Guestshell')
        return True


app = Flask(__name__, template_folder='templates')

@app.route('/')
@app.route('/index')
def root():
    return 'Hello World!'


@app.route('/configs/<path:file>')
def serve_configs(file):
    return send_from_directory('configs', file, mimetype='text/plain')


@app.route('/images/<path:file>')
def serve_sw_images(file):
    return send_from_directory('images', file, mimetype='application/octet-stream')


@app.route('/files/<path:file>')
def serve_files(file):
    return send_from_directory('files', file, mimetype='application/octet-stream')


@app.route('/pnp/HELLO')
def pnp_hello():
    return '', 200


@app.route('/pnp/WORK-REQUEST', methods=['POST'])
def pnp_work_request():
    data = xmltodict.parse(request.data)
    log_info(f'Receiving pnp request msg:\n{xmltodict.unparse(data, full_document=False, pretty=True)}')
    correlator = data['pnp']['info']['@correlator']
    udi = data['pnp']['@udi']
    log_info(f'Responding to device {udi} -')
    if udi in devices.keys():
        device = devices[udi]
        if device.pnp_state == PNP_STATE['NEW_DEVICE']:
            log_info(f'{udi} - New device showing up, set its config register')
            _response = pnp_cli_config(udi, correlator, f'config-register {pnp_env.isr1k_config_register}')
        elif device.pnp_state == PNP_STATE['CONFIG_REG']:
            log_info(f'{udi} - Save config register & pnp config')
            _response = pnp_cli_exec(udi, correlator, 'write memory')
        elif device.pnp_state in [PNP_STATE['CHECK_IMAGE_VER'], PNP_STATE['UPGRADE_RELOADING'], PNP_STATE['CHECK_BOOTFLASH_SIZE']]:
            log_info(f'{udi} - Check its device info')
            _response = pnp_device_info(udi, correlator, 'all')
        elif device.pnp_state == PNP_STATE['UPGRADE_NEEDED']:
            log_info(f'{udi} - Need upgrading, now transfer new image to device')
            device.pnp_state = PNP_STATE['UPGRADE_INPROGRESS']
            _response = pnp_install_image(udi, correlator)
        elif device.pnp_state == PNP_STATE['UPGRADE_RELOAD_NEEDED']:
            log_info(f'{udi} - New image has been transferred, now backoff & reload yourself before contacting server')
            device.pnp_state = PNP_STATE['UPGRADE_RELOADING']
            _response = pnp_backoff(udi, correlator, 2)
        elif device.pnp_state == PNP_STATE['UPGRADE_DONE']:
            if not device.has_GS_tarball:
                log_info(f'{udi} - Now start transferring guestshell tarball into device bootflash')
                device.pnp_state = PNP_STATE['GS_TARBALL_TRANSFER']
                _response = pnp_transfer_file(udi, pnp_env.guestshell_tarball_filename, correlator)
            elif not device.has_PY_script:
                log_info(f'{udi} - Now start transferring python script into device bootflash:guest-share/')
                device.pnp_state = PNP_STATE['PY_SCRIPT_TRANSFER']
                _response = pnp_transfer_file(udi, pnp_env.python_script_filename, correlator, 'bootflash:guest-share/')
            else:
                device.pnp_state = PNP_STATE['CONFIG_START']
                log_info(f'{udi} - Update the running configuration')
                _response = pnp_config_upgrade(udi, correlator)
        elif device.pnp_state == PNP_STATE['PY_SCRIPT_TRANSFER']:
            log_info(f'{udi} - Now start transferring python script into device bootflash:guest-share/')
            _response = pnp_transfer_file(udi, pnp_env.python_script_filename, correlator, 'bootflash:guest-share/')
        elif device.pnp_state == PNP_STATE['CONFIG_START']:
            log_info(f'{udi} - Update the running configuration')
            _response = pnp_config_upgrade(udi, correlator)
        elif device.pnp_state == PNP_STATE['CONFIG_SAVE_STARTUP']:
            log_info(f'{udi} - Save running-config as startup-config')
            _response = pnp_cli_exec(udi, correlator, 'write memory')
        elif device.pnp_state == PNP_STATE['RUN_EVENT_MANAGER']:
            log_info(f'{udi} - Activate guestshell environment via EEM')
            _response = pnp_cli_exec(udi, correlator, f'event manager run {pnp_env.EEM_event_name}')
        elif device.pnp_state == PNP_STATE['WAIT_FOR_GUESTSHELL']:
            log_info(f'{udi} - Wait 1 min for guestshell to be enabled')
            _response = pnp_backoff(udi, correlator, 1)
        elif device.pnp_state == PNP_STATE['CHECK_GUESTSHELL']:
            log_info(f'{udi} - Check if the guestshell env is running')
            _response = pnp_cli_exec(udi, correlator, 'show app-hosting list')
        elif device.pnp_state == PNP_STATE['INSTALL_GUESTSHELL']:
            log_info(f'{udi} - Install guestshell')
            _response = pnp_cli_exec(udi, correlator, f'app-hosting install appid guestshell package bootflash:{pnp_env.guestshell_tarball_filename}')
        elif  device.pnp_state == PNP_STATE['ENABLE_GUESTSHELL']:
            log_info(f'{udi} - Enable guestshell')
            _response = pnp_cli_exec(udi, correlator, 'guestshell enable')
        elif device.pnp_state == PNP_STATE['RUN_PY_SCRIPT']:
            log_info(f'{udi} - Start guestshell python script')
            _response = pnp_cli_exec(udi, correlator, f'guestshell run python3 bootflash:guest-share/{pnp_env.python_script_filename}')
        elif device.pnp_state == PNP_STATE['BOOTFLASH_NO_SPACE']:
            log_error(f'{udi} - Fail to install guestshell due to not enough space in the disk, need 1GB')
            _response = pnp_backoff(udi, correlator, 10)
        elif device.pnp_state == PNP_STATE['FINISHED']:
            log_info(f'{udi} - All done')
            _response = pnp_backoff(udi, correlator, 20)
    else:
        src_addr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        create_new_device(udi, src_addr)
        log_info(f'{udi} - New device showing up, set its config register')
        _response = pnp_cli_config(udi, correlator, f'config-register {pnp_env.isr1k_config_register}')
    return Response(_response, mimetype='text/xml')

@app.route('/pnp/WORK-RESPONSE', methods=['POST'])
def pnp_work_response():
    src_addr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    data = xmltodict.parse(request.data)
    log_info(f'Received pnp response msg:\n{xmltodict.unparse(data, full_document=False, pretty=True)}')
    
    # Parse PnP response
    try:
        correlator = data['pnp']['response']['@correlator']
        udi = data['pnp']['@udi']
        job_type = data['pnp']['response']['@xmlns']
    except (KeyError, TypeError) as e:
        log_error(f"Error parsing PnP response: {e}")
        return Response('')
    
    if udi not in devices.keys():
        create_new_device(udi, src_addr)
    device = devices[udi]
    device.ip_address = src_addr
    device.last_contact = strftime(pnp_env.time_format)
    if job_type == 'urn:cisco:pnp:fault':
        log_error(f'{udi} - Received fault response')
        return Response('')
    else:
        correlator = data['pnp']['response']['@correlator']
        job_status = int(data['pnp']['response']['@success'])
        if job_status == 1:
            if job_type == 'urn:cisco:pnp:cli-config':
                device.pnp_state = PNP_STATE['CONFIG_REG']
            elif job_type == 'urn:cisco:pnp:device-info':
                update_device_info(data)
                if device.pnp_state in [PNP_STATE['CHECK_IMAGE_VER'], PNP_STATE['UPGRADE_RELOAD_NEEDED'], PNP_STATE['UPGRADE_RELOADING']]:                    
                    check_update(udi)
                elif device.pnp_state == PNP_STATE['CHECK_BOOTFLASH_SIZE']:
                    if check_bootflash_freespace(data['pnp']['response']) == True:
                        device.pnp_state = PNP_STATE['RUN_EVENT_MANAGER']
                    else:
                        device.pnp_state = PNP_STATE['BOOTFLASH_NO_SPACE']
            elif job_type == 'urn:cisco:pnp:image-install':
                device.pnp_state = PNP_STATE['UPGRADE_RELOAD_NEEDED']
            elif job_type == 'urn:cisco:pnp:file-transfer':
                if not device.has_GS_tarball:
                    device.has_GS_tarball = True
                    device.pnp_state = PNP_STATE['PY_SCRIPT_TRANSFER']
                else:
                    device.has_PY_script = True
                    if not device.is_configured:
                        device.pnp_state = PNP_STATE['CONFIG_START']
                    else:
                        device.pnp_state = PNP_STATE['RUN_EVENT_MANAGER']
            elif job_type == 'urn:cisco:pnp:config-upgrade':
                device.pnp_state = PNP_STATE['CONFIG_SAVE_STARTUP']
            elif job_type == 'urn:cisco:pnp:cli-exec':
                if device.pnp_state == PNP_STATE['CONFIG_REG']:
                    device.pnp_state = PNP_STATE['CHECK_IMAGE_VER']
                elif device.pnp_state == PNP_STATE['CONFIG_SAVE_STARTUP']:
                    device.is_configured = True
                    device.pnp_state = PNP_STATE['CHECK_BOOTFLASH_SIZE']
                elif device.pnp_state == PNP_STATE['RUN_EVENT_MANAGER']:
                    device.pnp_state = PNP_STATE['WAIT_FOR_GUESTSHELL']
                elif device.pnp_state == PNP_STATE['CHECK_GUESTSHELL']:
                    if ('execLog' in data['pnp']['response'] and
                        'dialogueLog' in data['pnp']['response']['execLog'] and
                        'received' in data['pnp']['response']['execLog']['dialogueLog'] and
                        'text' in data['pnp']['response']['execLog']['dialogueLog']['received']):
                        if 'RUNNING' in data['pnp']['response']['execLog']['dialogueLog']['received']['text']:
                            device.pnp_state = PNP_STATE['RUN_PY_SCRIPT']
                        elif 'DEPLOYED' in data['pnp']['response']['execLog']['dialogueLog']['received']['text']:
                            device.pnp_state = PNP_STATE['ENABLE_GUESTSHELL']
                        elif 'No App found' in data['pnp']['response']['execLog']['dialogueLog']['received']['text']:
                            device.pnp_state = PNP_STATE['INSTALL_GUESTSHELL']
                        else:
                            device.pnp_state = PNP_STATE['WAIT_FOR_GUESTSHELL']
                elif device.pnp_state in (PNP_STATE['ENABLE_GUESTSHELL'], PNP_STATE['INSTALL_GUESTSHELL']):
                    device.pnp_state = PNP_STATE['CHECK_GUESTSHELL']
                elif device.pnp_state == PNP_STATE['RUN_PY_SCRIPT']:
                    device.pnp_state = PNP_STATE['FINISHED']
            elif job_type == 'urn:cisco:pnp:backoff':
                if device.pnp_state == PNP_STATE['WAIT_FOR_GUESTSHELL']:
                    device.pnp_state = PNP_STATE['CHECK_GUESTSHELL']
                else:
                    pass
        else:
            if job_type == 'urn:cisco:pnp:image-install':
                # If failed to the install the image,
                # we should check the device info again,
                # in case it has already be done
                device.pnp_state = PNP_STATE['UPGRADE_RELOADING']
        _response = pnp_bye(udi, correlator)
        return Response(_response, mimetype='text/xml')


if __name__ == '__main__':

    devices = {}
    images  = {}

    target_image = SoftwareImage(pnp_env.image_filename)
    target_image.md5 = calculate_md5(f'images/{pnp_env.image_filename}')
    images[target_image.image] = target_image


    if pnp_env.pnp_server_ip == '':
        print(f'pnp server ip address not set yet, check pnp_env.py')
        exit(1)

    configure_logger(pnp_env.log_file, pnp_env.log_to_console)
    log_info('Start Logging:')

    scheduler = BackgroundScheduler()

    # if  usedb:
    
    # Initialize database before using it
    if not init_db():
        print("Failed to initialize database")
        exit(1)

    read_device_status_from_db(devices)
    scheduler.add_job(write_device_status_into_db, 'interval', minutes=0.5, args=[devices])
    
    # else:
    #     read_device_status_from_csv_file(pnp_env.device_status_filename, devices, images)
    #     scheduler.add_job(update_device_status_to_csv_file, 'interval', minutes=0.5, args=[pnp_env.device_status_filename, devices])
    
    scheduler.start()

    print()
    print(f'Running PnP server. Stop with ctrl+c')
    print()
    print(f'Bind to IP-address      : {pnp_env.pnp_server_ip}')
    print(f'Listen on port          : {pnp_env.service_port}')
    print(f'Image file(s) base URL  : {pnp_env.image_url}')
    print(f'Config file(s) base URL : {pnp_env.config_url}')
    print()

    app.run(host= '0.0.0.0', port=pnp_env.service_port)