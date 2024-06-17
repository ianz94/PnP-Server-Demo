pnp_server_ip = ''
pnp_server_ip = '10.82.194.80'
service_port = '80'
image_url = 'http://' + pnp_server_ip + '/images'
config_url = 'http://' + pnp_server_ip + '/configs'
default_cfg_exists = True
default_cfg_filename = 'default.cfg'

file_url = 'http://' + pnp_server_ip + '/files'
file_name = 'ISR1K WLAN SDWAN Integration.mp4'

device_status_filename = 'DEVICE_STATUS.csv'

# Logging
log_file = 'logs/pnp_debug.log'
log_to_console = False

time_format = '%Y-%m-%dT%H:%M:%S'