#!/usr/bin/env python3
"""
Cisco PnP Server Demo
Entry point script that starts the PnP server
"""
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from app import app
from app.utils.device import SoftwareImage
from app.utils.logger import configure_logger, log_info
from app.utils.helpers import calculate_md5
from app.database.models import init_db, read_device_status_from_db, write_device_status_into_db
import settings

def main():
    """Main function that starts the PnP server"""
    # Initialize global variables
    devices = {}
    
    # Create target image object
    target_image = SoftwareImage(settings.image_filename)
    target_image.md5 = calculate_md5(f'images/{settings.image_filename}')
    
    # Verify server IP is set
    if settings.pnp_server_ip == '':
        print(f'PnP server IP address not set yet, check settings.py')
        sys.exit(1)

    # Configure logging
    configure_logger(settings.log_file, settings.log_to_console)
    log_info('Starting PnP Server Logging:')

    # Setup scheduler for background tasks
    scheduler = BackgroundScheduler()

    # Initialize database and read device status
    if not init_db():
        print("Failed to initialize database")
        sys.exit(1)

    read_device_status_from_db(devices)
    scheduler.add_job(write_device_status_into_db, 'interval', minutes=0.5, args=[devices])
    scheduler.start()

    # Display server information
    print()
    print(f'Running PnP server. Stop with ctrl+c')
    print()
    print(f'Bind to IP-address      : {settings.pnp_server_ip}')
    print(f'Listen on port          : {settings.service_port}')
    print(f'Image file(s) base URL  : {settings.image_url}')
    print(f'Config file(s) base URL : {settings.config_url}')
    print()

    # Make global variables available to handlers
    app.config['DEVICES'] = devices
    app.config['TARGET_IMAGE'] = target_image
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=settings.service_port)

if __name__ == '__main__':
    main()
