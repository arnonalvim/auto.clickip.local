import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()


def execute_mpls_l2vpn(hostname, username, password, vlan_id, description, neib, interfaces):
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
        'mpls ldp',
        ' lsr-id loopback-0',
        'top',
        'mpls l2vpn',
        f' vpls-group tunnel-{vlan_id}',
        f'  vpn "{description}"',
        f'   description "{description}"',
        '   vfi',
        '    pw-type vlan',
        f'     neighbor {neib}',
        f'     pw-id {vlan_id}',
        '     pw-mtu 1600',
        '     split-horizon enable',
        '     pw-load-balance',
        '      flow-label both',
        '     !',
        '    !',
        '   !',
        '   bridge-domain',
        f'   dot1q {vlan_id}',
    ]

    # Adicionar múltiplas interfaces
    for interface in interfaces:
        if interface.strip():  # Verificar se a interface não está vazia
            commands.append(f'        access-interface {interface.strip()}')

    # Finalizar comandos
    commands.extend([
        'top',
        'commit and-quit',
        f'show mpls l2vpn vpls-group brief | include {vlan_id}',
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
