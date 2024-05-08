from time import strftime
from flask import Flask, request, send_from_directory, render_template, Response
# from pathlib import Path
# import re
from requests import head
import xmltodict
import pnp_env
from pnp_utils import PNP_STATE, Device, SoftwareImage

# SERIAL_NUM_RE = re.compile(r'PID:(?P<product_id>[\w|\/|-]+),VID:(?P<hw_version>\w+),SN:(?P<serial_number>\w+)')

def pnp_device_info(udi: str, correlator: str, info_type: str) -> str:
    # info_type can be one of:
    # image, hardware, filesystem, udi, profile, all
    device = devices[udi]
    if device.current_job != 'urn:cisco:pnp:image-install':
        device.current_job = 'urn:cisco:pnp:device-info'
    jinja_context = {
        'udi': udi,
        'correlator': correlator,
        'info_type': info_type
    }
    return render_template('device_info.xml', **jinja_context)


def pnp_install_image(udi: str, correlator: str) -> str:
    device = devices[udi]
    response = head(f'{pnp_env.image_url}/{device.target_image.image}')
    if response.status_code == 200:
        device.current_job = 'urn:cisco:pnp:image-install'
        device.pnp_state = PNP_STATE['UPGRADE_INPROGRESS']
        # device.backoff = True
        # device.refresh_data = True
        jinja_context = {
            'udi': udi,
            'correlator': correlator,
            'base_url': pnp_env.image_url,
            'image_name': device.target_image.image,
            'md5': device.target_image.md5.lower(),
            'destination': 'bootflash',
            # 'delay': 0,  # reload in seconds
        }
        _template = render_template('image_install.xml', **jinja_context)
        # log_info(_template, SETTINGS.debug)
        return _template
    else:
        # device.error_code = ERROR.ERROR_NO_IMAGE_FILE
        # device.hard_error = True
        print('image does not exist!!!!!!')
        return ''


def pnp_config_upgrade(udi: str, correlator: str) -> str:
    device = devices[udi]
    cfg_file = f'{device.serial_number}.cfg'
    response = head(f'{pnp_env.config_url}/{cfg_file}')
    if response.status_code != 200:  # SERIAL.cfg not found
        # if not SETTINGS.no_default_cfg:
        #     cfg_file = SETTINGS.default_cfg
        #     response = head(f'{SETTINGS.config_url}/{cfg_file}')
        #     if response.status_code != 200:  # DEFAULT.cfg also not found
        #         device.error_code = ERROR.ERROR_NO_CFG_FILE
        #         device.hard_error = True
        #         return
        # else:
        #     device.error_code = ERROR.ERROR_NO_CFG_FILE
        #     device.hard_error = True
        #     return
        print('config does not exist!!!!!!')
        return ''

    device.current_job = 'urn:cisco:pnp:config-upgrade'
    device.pnp_state = PNP_STATE['CONFIG_START']
    jinja_context = {
        'udi': udi,
        'correlator': correlator,
        'base_url': pnp_env.config_url,
        # 'reload_delay': 30,  # reload in seconds
        'config_filename': cfg_file,
    }
    _template = render_template('config_upgrade.xml', **jinja_context)
    # log_info(_template, SETTINGS.debug)
    return _template


def pnp_bye(udi: str, correlator: str) -> str:
    jinja_context = {
        'udi': udi,
        'correlator': correlator,
    }
    _template = render_template('bye.xml', **jinja_context)
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
        hw_rev=hw_rev,
        current_job='urn:cisco:pnp:device-info'
    )
    devices[udi].pnp_state = PNP_STATE['NEW_DEVICE']
    devices[udi].target_image = test_image
    # device = devices[udi]
    # device.backoff = True
    # for image, image_data in IMAGES.images.items():
    #     if platform in image_data['models']:
    #         device.target_image = SoftwareImage(
    #             image=image,
    #             version=image_data['version'],
    #             md5=image_data['md5'],
    #             size=image_data['size']
    #         )
    # if not device.target_image:
    #     device.error_code = ERROR.ERROR_NO_PLATFORM
    #     device.hard_error = True


def update_device_info(data: dict):
    # destination = {}

    udi = data['pnp']['@udi']
    device = devices[udi]

    device.version = data['pnp']['response']['imageInfo']['versionString'].strip()
    device.image = data['pnp']['response']['imageInfo']['imageFile'].split(':')[1]
    # device.refresh_data = False
    device.last_contact = strftime(pnp_env.time_format)
    # for filesystem in data['pnp']['response']['fileSystemList']['fileSystem']:
    #     if filesystem['@name'] in ['bootflash', 'flash']:
    #         destination = filesystem

    # device.platform = data['pnp']['response']['hardwareInfo']['platformName']
    # device.serial = data['pnp']['response']['hardwareInfo']['boardId']
    # device.destination_name = destination['@name']
    # device.destination_free = int(destination['@freespace'])


def check_update(udi: str):
    device = devices[udi]
    if device.version == device.target_image.version:
        device.pnp_state = PNP_STATE['UPGRADE_DONE']
    else:
        device.pnp_state = PNP_STATE['UPGRADE_NEEDED']
        # if device.destination_free < device.target_image.size:
        #     _mb = round(device.target_image.size / 1024 / 1024)
        #     device.error_code = ERROR.ERROR_NO_FREE_SPACE
        #     device.hard_error = True


app = Flask(__name__, template_folder='templates')
# current_dir = Path(__file__)

@app.route('/')
@app.route('/index')
def root():
    return 'Hello Stream!'


@app.route('/configs/<path:file>')
def serve_configs(file):
    return send_from_directory('configs', file, mimetype='text/plain')


@app.route('/images/<path:file>')
def serve_sw_images(file):
    return send_from_directory('images', file, mimetype='application/octet-stream')


@app.route('/pnp/HELLO')
def pnp_hello():
    return '', 200


@app.route('/pnp/WORK-REQUEST', methods=['POST'])
def pnp_work_request():
    print('\n\n\n==============================================')
    print('From PnP Agent to PnP Server:')
    src_addr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    data = xmltodict.parse(request.data)
    print(xmltodict.unparse(data, full_document=False, pretty=True))
    print('From PnP Server to PnP Agent:')
    correlator = data['pnp']['info']['@correlator']
    udi = data['pnp']['@udi']

    if udi in devices.keys():
        device = devices[udi]
        if device.pnp_state == PNP_STATE['NEW_DEVICE']:
            # log_info('PNPFLOW.NEW', SETTINGS.debug)
            device.pnp_state = PNP_STATE['INFO']
            _response = pnp_device_info(udi, correlator, 'all')
        elif device.pnp_state == PNP_STATE['UPGRADE_NEEDED']:
            # log_info('PNPFLOW.INFO', SETTINGS.debug)
            device.pnp_state = PNP_STATE['UPGRADE_INPROGRESS']
            _response = pnp_install_image(udi, correlator)
        elif device.pnp_state == PNP_STATE['UPGRADE_RELOAD']:
            # loginfo
            _response = pnp_device_info(udi, correlator, 'all')
        elif device.pnp_state == PNP_STATE['UPGRADE_DONE']:
            # loginfo
            _response = pnp_config_upgrade(udi, correlator)
    else:
        create_new_device(udi, src_addr)
        devices[udi].pnp_state = PNP_STATE['INFO']
        _response = pnp_device_info(udi, correlator, 'all')
    
    print(xmltodict.unparse(xmltodict.parse(_response), full_document=False, pretty=True))
    print('==============================================')
    return Response(_response, mimetype='text/xml')
    #  configuration register ???

    # print(xmltodict.unparse(xmltodict.parse(result_data), full_document=False, pretty=True))
    # print('==============================================')

@app.route('/pnp/WORK-RESPONSE', methods=['POST'])
def pnp_work_response():
    print('\n\n\n==============================================')
    print('From PnP Agent to PnP Server:')
    src_addr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    data = xmltodict.parse(request.data)
    print(xmltodict.unparse(data, full_document=False, pretty=True))
    print('From PnP Server to PnP Agent:')
    correlator = data['pnp']['response']['@correlator']
    udi = data['pnp']['@udi']
    job_type = data['pnp']['response']['@xmlns']
    if udi not in devices.keys():
        create_new_device(udi, src_addr)

    device = devices[udi]
    device.ip_address = src_addr
    device.last_contact = strftime(pnp_env.time_format)

    if job_type == 'urn:cisco:pnp:fault':  # error without job info (correlator):-(
        device.error = data['pnp']['response']['fault']['detail']['XSVC-ERR:error']['XSVC-ERR:details']
    else:
        correlator = data['pnp']['response']['@correlator']
        job_status = int(data['pnp']['response']['@success'])
        if job_status == 1:  # success
            # if job_type not in ['urn:cisco:pnp:backoff']:
            #     device.backoff = True
            # device.error_count = 0
            if job_type == 'urn:cisco:pnp:device-info':
                if device.pnp_state in [PNP_STATE['INFO'], PNP_STATE['UPGRADE_RELOAD']]:
                    update_device_info(data)
                    check_update(udi)
                else:
                    update_device_info(data)
            elif job_type == 'urn:cisco:pnp:image-install':
                device.pnp_state = PNP_STATE['UPGRADE_RELOAD']
            elif job_type == 'urn:cisco:pnp:config-upgrade':
                # device.pnp_flow = PNPFLOW.CONFIG_DOWN  # we don't reach this as we remove PNP before via EEM
                device.pnp_state = PNP_STATE['FINISHED']
                # device.status = 'Finished. You can remove the device from the list :-)'
            elif job_type == 'urn:cisco:pnp:backoff':
                # device.pnp_flow = PNPFLOW.INFO
                pass
            # _response = pnp_bye(udi, correlator)
            # # log_info(_response, SETTINGS.debug)
            # print(xmltodict.unparse(xmltodict.parse(_response), full_document=False, pretty=True))
            # print('==============================================')
            # return Response(_response, mimetype='text/xml')
        # elif job_status == 0:
            # error_code = int(data['pnp']['response']['errorInfo']['errorCode'].split(' ')[-1])
            # device.error_count += 1
            # device.error_message = data['pnp']['response']['errorInfo']['errorMessage']
            # device.error_code = error_code
            # if error_code in [ERROR.PNP_ERROR_BAD_CHECKSUM, ERROR.PNP_ERROR_FILE_NOT_FOUND]:
            #     device.hard_error = True
            # return Response(pnp_bye(udi, correlator), mimetype='text/xml')
        _response = pnp_bye(udi, correlator)
        # log_info(_response, SETTINGS.debug)
        print(xmltodict.unparse(xmltodict.parse(_response), full_document=False, pretty=True))
        print('==============================================')
        return Response(_response, mimetype='text/xml')
    device.current_job = 'none'
    return Response('')



    # print(xmltodict.unparse(xmltodict.parse(result_data), full_document=False, pretty=True))
    # print('==============================================')
    # return Response(result_data, mimetype='text/xml')

# @app.route('/configs/ztp.py', methods=['GET'])
# def send_ztp_script():
#     script_path = './configs/ztp.py'
#     return send_file(script_path)

if __name__ == '__main__':

    devices = {}
    test_image = SoftwareImage(
        image='c1100-universalk9.17.14.01a.SPA.bin',
        version='17.14.1a',
        md5='ac8c06a8431d26b723c92f0aa245bfe7',
        size = 716699088
    )

    app.run(host= '0.0.0.0', port=pnp_env.service_port) #debug=pnp_env.debug_mode)