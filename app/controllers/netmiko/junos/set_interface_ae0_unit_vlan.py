from app import create_app
from netmiko import ConnectHandler


def set_interface_unit(
    hostname, username, password, unit, description,
    bandwidth, ipv4_gw, ipv6_gw, ipv6_cli, ipv6_48
):
    app = create_app()
    router = {
        'device_type': 'juniper',
        'host': hostname,
        'username': username,
        'password': password,
        'port': app.config.get('NETMIKO_SSH_PORT'),
        'timeout': app.config.get('NETMIKO_TIMEOUT'),
        'session_timeout': app.config.get('NETMIKO_SESSION_TIMEOUT'),
    }

    commands = [
        f'set interfaces ae0 unit {unit} description "{description}"',
        f'set interfaces ae0 unit {unit} vlan-id {unit}',
        f'set interfaces ae0 unit {unit} family inet filter output PROTECT-CLIENTES',
        f'set interfaces ae0 unit {unit} family inet policer input {bandwidth}mb-filter output {bandwidth}mb-filter',
        f'set interfaces ae0 unit {unit} family inet sampling input output',
        f'set interfaces ae0 unit {unit} family inet address {ipv4_gw}',  # /30
        f'set interfaces ae0 unit {unit} family inet6 policer input {bandwidth}mb-filter output {bandwidth}mb-filter',
        f'set interfaces ae0 unit {unit} family inet6 sampling input output',
        f'set interfaces ae0 unit {unit} family inet6 address {ipv6_gw}',  # /126
        f'set routing-options rib inet6.0 static route {ipv6_48} next-hop {ipv6_cli}',
    ]

    try:
        ssh = ConnectHandler(**router)
        ssh.send_config_set(commands)
        ssh.commit()
        output = [
            ssh.send_command(f'run show configuration interfaces ae0 unit {unit}'),
            ssh.send_command(f'run show configuration | display set | match {ipv6_cli}'),
        ]

    except Exception as e:
        print(f'Error to execute commands: {e}')
        output = None

    finally:
        ssh.disconnect()

    if output:
        formatted_output = "\n".join(output)

    return formatted_output
