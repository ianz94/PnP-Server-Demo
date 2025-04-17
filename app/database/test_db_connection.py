import mariadb
from pnp_env import db_config

try:
    conn = mariadb.connect(**db_config)
    print("MariaDB connection is successful!")
    conn.close()
except mariadb.Error as e:
    print(f"Error connecting to MariaDB: {e}")
