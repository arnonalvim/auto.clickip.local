import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()


def execute_vlan_config(hostname, username, password, vlan_id, description, interface, tagoruntag):
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
        f'dot1q vlan {vlan_id} name "{description}" interface {interface} {tagoruntag}',
    ]

    # Adicionar comando adicional se for untagged
    if tagoruntag == 'untagged':
        commands.append(f'switchport interface {interface} native-vlan vlan-id {vlan_id}')

    # Adicionar commit e show
    commands.extend([
        'commit',
        f'show dot1q vlan {vlan_id}',
    ])

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
