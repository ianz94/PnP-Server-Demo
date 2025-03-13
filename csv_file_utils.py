import csv
from pnp_main import devices, images
from pnp_utils import PNP_STATE_LIST, PNP_STATE, Device

def read_device_status_from_csv_file(filename: str):
    with open(filename, 'r') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter='|')
        # skip the top row of fieldnames
        next(csv_reader)
        devices.clear()
        for row in csv_reader:
            
            serial_number = row[0].strip()
            platform      = row[1].strip()
            hw_rev        = row[2].strip()
            src_addr      = row[3].strip()
            first_seen    = row[4].strip()
            last_contact  = row[5].strip()
            current_ver   = row[6].strip()
            target_image  = row[7].strip()
            has_GS_tarball= row[8].strip()
            has_PY_script = row[9].strip()
            is_configured = row[10].strip()
            pnp_state     = row[11].strip()

            # sample udi="PID:C1131-8PWB,VID:V01,SN:FGL2548L0AW"
            udi = f'PID:{platform},VID:{hw_rev},SN:{serial_number}'
            device = Device(
                udi=udi,
                first_seen=first_seen,
                last_contact=last_contact,
                src_address=src_addr,
                serial_number=serial_number,
                platform=platform,
                hw_rev=hw_rev
            )
            device.pnp_state = PNP_STATE[pnp_state]
            device.version = current_ver
            device.target_image = images[target_image]
            device.has_GS_tarball = (has_GS_tarball == 'Done')
            device.has_PY_script = (has_PY_script == 'Done')
            device.is_configured = (is_configured == 'Done')
            devices[udi] = device


def update_device_status_to_csv_file(filename: str):
    # Fixed width for each column
    column_widths = [15, 16, 9, 16, 24, 24, 22, 40, 20, 15, 15, 20]

    # Write CSV file with fixed-width formatting
    with open(filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter='|')
        csv_writer.writerow(format_fixed_width(['Serial Number',
                                                'Platform',
                                                'HW rev.',
                                                'IP Address',
                                                'First Seen',
                                                'Last Contact',
                                                'Current Version',
                                                'Target Image',
                                                'Guestshell Tarball',
                                                'Python Script',
                                                'Config Update',
                                                'Device State'],
                                                column_widths))
        for device in devices.values():
            formatted_row = format_fixed_width([device.serial_number,
                                                device.platform,
                                                device.hw_rev,
                                                device.ip_address,
                                                device.first_seen,
                                                device.last_contact,
                                                device.version,
                                                device.target_image.image,
                                                'Done' if device.has_GS_tarball else 'Not yet',
                                                'Done' if device.has_PY_script else 'Not yet',
                                                'Done' if device.is_configured else 'Not yet',
                                                PNP_STATE_LIST[device.pnp_state]],
                                                column_widths)
            csv_writer.writerow(formatted_row)


# Function to format each element centered within fixed width
def format_fixed_width(data, widths):
    formatted_data = []
    for i, element in enumerate(data):
        formatted_data.append(f"{element:^{widths[i]}}")
    return formatted_data
