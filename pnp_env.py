#1. Write here the IP address of this server
#   For example pnp_server_ip = '10.2.3.4'
pnp_server_ip = ''
service_port = '80'

#2. Write the filename of the new image you want your ISR1k devices upgrade to
#   For example image_filename = 'c1100-universalk9.17.14.01a.SPA.bin'
#   And then please copy the image file to the ./images folder.
image_url = 'http://' + pnp_server_ip + '/images'
image_filename = ''

#3. Put the day-0 configuration files under ./configs folder.
#   Name the config file with the device serial number, e.g. 'FGL2548L0AW.cfg'
#   Then each device will fetch its own config.
#   However if it cannot find a .cfg named by its serial number,
#   it will simply fetch the default.cfg in ./configs folder.
#   So make sure you edit the default.cfg to match your needs.
config_url = 'http://' + pnp_server_ip + '/configs'
default_cfg_exists = True
default_cfg_filename = 'default.cfg'
#   Name of the event manager applet that will be run
#   Change this if not correct
EEM_event_name = 'InstallGuestShell'

#4. Put the file which you want to transfer under ./files folder
#   Write its filename. For example file_name = 'guestshell.17.09.01a.tar'
file_url = 'http://' + pnp_server_ip + '/files'
guestshell_tarball_filename = ''
python_script_filename      = ''

# Name of the status panel which you can check out the progress of each device
device_status_filename = 'DEVICE_STATUS.csv'

# Set the config-reg to be 0x2102 so ISR1k device will have normal boot behaviors
isr1k_config_register = '0x2102'

# Name & path of the logging file
log_file = 'logs/pnp_debug.log'
# You can turn this on if you want to see the log in console at runtime
log_to_console = False
time_format = '%Y-%m-%dT%H:%M:%S'

# Database Configuration
db_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'pnp_user',
    'password': 'pnp_password',
    'database': 'pnp_db'
}
