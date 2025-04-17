import logging
from logging.handlers import RotatingFileHandler
from sys import stdout

def configure_logger(path: str, log_to_console: bool):
    """Configure the application logger"""
    # Disable FLASK console output
    logging.getLogger("werkzeug").disabled = True
    
    # Define our own logger
    log_formatter = logging.Formatter('%(asctime)s :: %(name)s :: %(message)s\n')
    log = logging.getLogger('pnp_server')
    log.setLevel(logging.INFO)

    # Write logs to a file, rotate it when it reaches 5MB
    log_handler_file = RotatingFileHandler(
        path,
        mode='a',
        maxBytes=5 * 1024 * 1024,
        backupCount=10
    )

    log_handler_file.setFormatter(log_formatter)
    log_handler_file.setLevel(logging.INFO)
    log.addHandler(log_handler_file)

    if log_to_console:
        log_handler_console = logging.StreamHandler(stdout)
        log_handler_console.setFormatter(log_formatter)
        log_handler_console.setLevel(logging.INFO)
        log.addHandler(log_handler_console)


def log_info(message: str):
    """Log an informational message"""
    log = logging.getLogger('pnp_server')
    log.info(message)


def log_error(message: str):
    """Log an error message"""
    log = logging.getLogger('pnp_server')
    log.error(message)
    # Also print error message to console to raise attention
    print(f'ERROR: {message}')