pnp_server_ip = '10.24.9.17'
service_port = '80'
image_url = 'http://' + pnp_server_ip + '/images'
config_url = 'http://' + pnp_server_ip + '/configs'
default_cfg_exists = True
default_cfg_filename = 'default.cfg'
device_status_filename = 'DEVICE_STATUS.csv'

# Logging
log_file = 'logs/pnp_debug.log'
log_to_console = True

time_format = '%Y-%m-%dT%H:%M:%S'