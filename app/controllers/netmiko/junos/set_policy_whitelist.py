from app import create_app
from netmiko import ConnectHandler


def set_policy_whitelist(hostname, username, password, prefix):
    app = create_app()

    router = {
        'device_type': 'juniper',
        'host': hostname,
        'username': username,
        'password': password,
        'port': app.config.get('NETMIKO_SSH_PORT', 22),
        'timeout': app.config.get('NETMIKO_TIMEOUT', 30),
        'session_timeout': app.config.get('NETMIKO_SESSION_TIMEOUT', 60),
    }

    ssh = ConnectHandler(**router)
    ssh.send_config_set(f'set policy-options prefix-list whitelist-dst {prefix}')
    ssh.commit()

    output = ssh.send_command(f'run show configuration policy-options prefix-list whitelist-dst | display set | match {prefix}')

    ssh.disconnect()
    return output


def get_policy_whitelist(hostname, username, password):
    app = create_app()

    router = {
        'device_type': 'juniper',
        'host': hostname,
        'username': username,
        'password': password,
        'port': app.config.get('NETMIKO_SSH_PORT', 22),
        'timeout': app.config.get('NETMIKO_TIMEOUT', 30),
        'session_timeout': app.config.get('NETMIKO_SESSION_TIMEOUT', 60),
    }

    ssh = ConnectHandler(**router)
    output = ssh.send_command('show configuration policy-options prefix-list whitelist-dst')

    ssh.disconnect()
    return output


def manage_policy_whitelist(hostname, username, password, prefix=None, action='get'):
    """
    Função unificada para gerenciar policy whitelist.
    
    Args:
        hostname: IP ou hostname do router
        username: Nome de usuário
        password: Senha
        prefix: Prefixo (obrigatório para action='set')
        action: 'get' ou 'set'
    
    Returns:
        str: Output do comando
    """
    app = create_app()

    router = {
        'device_type': 'juniper',
        'host': hostname,
        'username': username,
        'password': password,
        'port': app.config.get('NETMIKO_SSH_PORT', 22),
        'timeout': app.config.get('NETMIKO_TIMEOUT', 30),
        'session_timeout': app.config.get('NETMIKO_SESSION_TIMEOUT', 60),
    }

    ssh = ConnectHandler(**router)
    
    if action == 'set':
        if prefix:
            ssh.send_config_set(f'set policy-options prefix-list whitelist-dst {prefix}')
            ssh.commit()
            output = ssh.send_command(f'run show configuration policy-options prefix-list whitelist-dst | display set | match {prefix}')
        else:
            ssh.disconnect()
            raise ValueError("Prefix é obrigatório para action='set'")
    else:  # action == 'get'
        output = ssh.send_command('show configuration policy-options prefix-list whitelist-dst')

    ssh.disconnect()
    return output
