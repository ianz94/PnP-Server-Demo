"""
PnP Server Configuration File

This file contains all the configuration parameters for your Cisco PnP Server.
Edit the values below to match your environment before running the server.
"""

#######################
# SERVER CONFIGURATION
#######################

# The IP address of this PnP server (required)
# This should be an IP address that is reachable by your devices
pnp_server_ip = ''

# HTTP service port (default: 80)
service_port = '80'

#############################
# DEVICE IMAGE CONFIGURATION
#############################

# Base URL for serving image files
image_url = 'http://' + pnp_server_ip + '/images'

# Target IOS-XE image filename for device upgrade
# For example image_filename = 'c1100-universalk9.17.14.01a.SPA.bin'
# Make sure this file exists in the ./images folder
image_filename = ''

#######################
# CONFIG CONFIGURATION
#######################

# Base URL for serving configuration files to Cisco devices
config_url = 'http://' + pnp_server_ip + '/configs'

# Configuration files should be stored in the ./configs directory with the following naming convention:
# - Device-specific configs: Use device serial numbers (e.g., 'FGL2548L0AW.cfg')
# - Fallback config: A default configuration ('default.cfg') will be used if no
#   device-specific configuration is found for a given serial number
# 
# Note: Ensure the default.cfg contains appropriate settings as it serves as the
# fallback configuration for all devices without a dedicated config file.

# Default configuration options
default_cfg_exists = True     # Set to False if you don't have a default.cfg
default_cfg_filename = 'default.cfg'

# Name of the event manager applet that installs Guestshell
# Must match the name in your configuration files
EEM_event_name = 'InstallGuestShell'

#######################
# FILES CONFIGURATION
#######################

# Base URL for serving other files
file_url = 'http://' + pnp_server_ip + '/files'

# Guestshell tarball filename (must exist in ./files folder)
# For example guestshell_tarball_filename = 'guestshell.17.09.01a.tar'
guestshell_tarball_filename = ''

# Python script to run in Guestshell (must exist in ./files folder)
python_script_filename = ''

#######################
# DEVICE CONFIGURATION
#######################

# Configuration register for ISR1k devices
# 0x2102 - normal boot from flash with config loading
isr1k_config_register = '0x2102'

########################
# LOGGING CONFIGURATION
########################

# Log file location
log_file = 'logs/pnp_debug.log'

# Set to True to see logs in console at runtime
log_to_console = False

# Time format for logging timestamps
time_format = '%Y-%m-%dT%H:%M:%S'  # ISO 8601 format

#########################
# DATABASE CONFIGURATION
#########################

# MariaDB connection parameters
db_config = {
    'host': '127.0.0.1',  # Database server address
    'port': 3306,         # Default MariaDB port
    'user': 'pnp_user',   # Database username
    'password': 'pnp_password',  # Database password
    'database': 'pnp_db'  # Database name
}
