import hashlib

def calculate_md5(filepath):
    """Calculate the MD5 checksum of a file"""
    try:
        with open(filepath, mode='rb') as file:
            md5_hash = hashlib.md5()
            chunk = file.read(8192)
            while chunk:
                md5_hash.update(chunk)
                chunk = file.read(8192)
        return md5_hash.hexdigest()
    except FileNotFoundError:
        print(f"The file '{filepath}' does not exist!")
        exit(1)
