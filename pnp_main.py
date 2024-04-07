from flask import Flask, request, send_from_directory, render_template, Response
from pathlib import Path
import re
import xmltodict
import env

SERIAL_NUM_RE = re.compile(r'PID:(?P<product_id>[\w|\/|-]+),VID:(?P<hw_version>\w+),SN:(?P<serial_number>\w+)')

app = Flask(__name__, template_folder="templates")
current_dir = Path(__file__)

@app.route('/')
@app.route('/index')
def root():
    return 'Hello Stream!'


@app.route('/configs/<path:path>')
def serve_configs(path):
    return send_from_directory('configs', path)


@app.route('/images/<path:path>')
def serve_sw_images(path):
    return send_from_directory('images', path)


@app.route('/pnp/HELLO')
def pnp_hello():
    return '', 200


@app.route('/pnp/WORK-REQUEST', methods=['POST'])
def pnp_work_request():
    print('\n\n\n==============================================')
    print('From PnP Agent to PnP Server:')
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
            "http_server": env.pnp_server,
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

if __name__ == "__main__":
    app.run(host= '0.0.0.0', port=env.service_port, debug=env.debug_mode)