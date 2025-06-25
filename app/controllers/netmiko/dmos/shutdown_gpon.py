import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()


def execute_shutdown_gpon(hostname, username, password, chassis, slot, port_id, dmos_command):
    device = {
        'device_type': 'cisco_ios',
        'host': hostname,
        'username': username,
        'password': password,
        'port': os.getenv('PORT'),
        'timeout': os.getenv('TIMEOUT'),
        'session_timeout': os.getenv('SESSION_TIMEOUT'),
    }

    commands = [
        'config',
        f'interface gpon {chassis}/{slot}/{port_id} ; {dmos_command}',
        'commit and-quit label site comment "auto.clickip.local" | suppress-validate-warning-prompt',
        'show config comm chan 0',
    ]

    try:
        ssh = ConnectHandler(**device)

        for command in commands:
            output = [
                ssh.find_prompt(),
                ssh.send_command(command, expect_string=r'#', read_timeout=15),
            ]

    except Exception as e:
        print(f'Error to execute commands: {e}')
        output = None

    finally:
        ssh.disconnect()

    if output:
        formatted_output = ''.join(output)

    return formatted_output
