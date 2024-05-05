from flask import Flask, request, send_from_directory, render_template, Response, send_file
# from pathlib import Path
import re
import xmltodict
import pnp_env

SERIAL_NUM_RE = re.compile(r'PID:(?P<product_id>[\w|\/|-]+),VID:(?P<hw_version>\w+),SN:(?P<serial_number>\w+)')

app = Flask(__name__, template_folder="templates")
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
    correlator_id = data['pnp']['info']['@correlator']
    udi = data['pnp']['@udi']
    if 'reason' in data['pnp']['info']:
        udi_match = SERIAL_NUM_RE.match(udi)
        serial_number = udi_match.group('serial_number')
        config_filename = serial_number + '.cfg'
        jinja_context = {
            "udi": udi,
            "correlator_id": correlator_id,
            "http_server": pnp_env.pnp_server,
            "config_filename": config_filename,
        }
        result_data = render_template('load_config.xml', **jinja_context)
    else:
        print('Ignore this request because config has already been sent')
        jinja_context = {
            "udi": udi,
            "correlator_id": correlator_id,
        }
        result_data = render_template('bye.xml', **jinja_context)
    print(xmltodict.unparse(xmltodict.parse(result_data), full_document=False, pretty=True))
    print('==============================================')
    return Response(result_data, mimetype='text/xml')

@app.route('/pnp/WORK-RESPONSE', methods=['POST'])
def pnp_work_response():
    print('\n\n\n==============================================')
    print('From PnP Agent to PnP Server:')
    client_ip = request.remote_addr
    data = xmltodict.parse(request.data)
    print(xmltodict.unparse(data, full_document=False, pretty=True))
    print('From PnP Server to PnP Agent:')
    correlator_id = data['pnp']['response']['@correlator']
    udi = data['pnp']['@udi']
    jinja_context = {
        "udi": udi,
        "correlator_id": correlator_id,
    }
    result_data = render_template('bye.xml', **jinja_context)
    print(xmltodict.unparse(xmltodict.parse(result_data), full_document=False, pretty=True))
    print('==============================================')
    return Response(result_data, mimetype='text/xml')

@app.route('/configs/ztp.py', methods=['GET'])
def send_ztp_script():
    script_path = './configs/ztp.py'
    return send_file(script_path)

if __name__ == "__main__":
    app.run(host= '0.0.0.0', port=pnp_env.service_port, debug=pnp_env.debug_mode)