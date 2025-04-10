import mariadb
from pnp_env import db_config
from pnp_utils import Device, SoftwareImage, PNP_STATE, PNP_STATE_LIST, log_info, log_error
from time import strftime

def get_db_connection():
    """Create a connection to the MariaDB database"""
    try:
        conn = mariadb.connect(**db_config)
        return conn
    except mariadb.Error as e:
        log_error(f"Error connecting to MariaDB: {e}")
        return None

def init_db():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                udi VARCHAR(100) UNIQUE,
                serial_number VARCHAR(20),
                platform VARCHAR(20),
                hw_rev VARCHAR(10),
                ip_address VARCHAR(20),
                first_seen VARCHAR(50),
                last_contact VARCHAR(50),
                current_version VARCHAR(50),
                current_image VARCHAR(100),
                has_gs_tarball BOOLEAN DEFAULT FALSE,
                has_py_script BOOLEAN DEFAULT FALSE,
                is_configured BOOLEAN DEFAULT FALSE,
                device_state INT
            )
        """)
        
        conn.commit()
        return True
    except mariadb.Error as e:
        log_error(f"Error creating database tables: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def save_device_status(device):
    """Save device status to database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO devices (
                udi, serial_number, platform, hw_rev, ip_address, 
                first_seen, last_contact, current_version, current_image,
                has_gs_tarball, has_py_script, is_configured, device_state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
                serial_number=?, platform=?, hw_rev=?, ip_address=?,
                last_contact=?, current_version=?, current_image=?,
                has_gs_tarball=?, has_py_script=?, is_configured=?, device_state=?
        """, (
            device.udi, device.serial_number, device.platform, device.hw_rev,
            device.ip_address, device.first_seen, device.last_contact,
            device.version, device.image,
            device.has_GS_tarball, device.has_PY_script, device.is_configured,
            device.pnp_state,
            # For ON DUPLICATE KEY UPDATE:
            device.serial_number, device.platform, device.hw_rev,
            device.ip_address, device.last_contact, device.version,
            device.image,
            device.has_GS_tarball, device.has_PY_script, device.is_configured,
            device.pnp_state
        ))
        conn.commit()
        return True
    except mariadb.Error as e:
        log_error(f"Error saving device status: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def read_device_status_from_db(devices):
    """Read device status from database and populate the devices dictionary"""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM devices")
        rows = cursor.fetchall()
        for row in rows:
            # Create device object
            device = Device(
                udi=row['udi'],
                platform=row['platform'],
                hw_rev=row['hw_rev'],
                serial_number=row['serial_number'],
                first_seen=row['first_seen'],
                last_contact=row['last_contact'],
                src_address=row['ip_address']
            )
            
            # Set additional properties
            device.pnp_state = row['device_state']
            device.version = row['current_version'] or ''
            device.image = row['current_image'] or ''
            
            # Set boolean flags
            device.has_GS_tarball = bool(row['has_gs_tarball'])
            device.has_PY_script = bool(row['has_py_script'])
            device.is_configured = bool(row['is_configured'])
            
            # Add to devices dictionary
            devices[device.udi] = device
            
    except mariadb.Error as e:
        log_error(f"Error reading device status from database: {e}")
    finally:
        cursor.close()
        conn.close()

def write_device_status_into_db(devices):
    """Write all devices to the database"""
    for device in devices.values():
        save_device_status(device)
