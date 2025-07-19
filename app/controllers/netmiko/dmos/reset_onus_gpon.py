import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()


def execute_reset_onus_gpon(hostname, username, password, chassis, slot, port_id):
    """Executa reset de ONUs para uma única OLT e porta"""
    device = {
        'device_type': 'cisco_ios',
        'host': hostname,
        'username': username,
        'password': password,
        'port': os.getenv('PORT'),
        'timeout': os.getenv('TIMEOUT'),
        'session_timeout': os.getenv('SESSION_TIMEOUT'),
    }

    # Gera comandos
    reset_commands = f"config\ninterface gpon {chassis}/{slot}/{port_id}\n"
    # Gera ONUs 0-127
    for onu_id in range(128):
        reset_commands += f"onu-reset onu {onu_id}\nyes\n"
    reset_commands += "top\nexit\n"
    try:
        ssh = ConnectHandler(**device)
        output = ssh.send_command_timing(reset_commands, read_timeout=0)
        final_output = [
            ssh.find_prompt(),
            output
        ]
        ssh.disconnect()
        if final_output:
            formatted_output = ''.join(final_output)
        return {
            'success': True,
            'output': formatted_output,
            'hostname': hostname,
            'port': f"{chassis}/{slot}/{port_id}"
        }

    except Exception as e:
        print(f'Error to execute commands on {hostname}: {e}')
        return {
            'success': False,
            'error': str(e),
            'hostname': hostname,
            'port': f"{chassis}/{slot}/{port_id}"
        }


def execute_bulk_reset_onus_gpon(hostnames, username, password, chassis, slot, port_ids):
    """Executa reset de ONUs para múltiplas OLTs e portas"""
    results = []
    for hostname in hostnames:
        for port_id in port_ids:
            result = execute_reset_onus_gpon(
                hostname=hostname,
                username=username,
                password=password,
                chassis=chassis,
                slot=slot,
                port_id=port_id
            )
            results.append(result)
    return results
