import os
from dotenv import load_dotenv
from netmiko import ConnectHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

load_dotenv()

thread_local = threading.local()


def execute_commands_on_single_olt(hostname, hostname_display, username, password, commands_list):
    """Executa comandos em uma única OLT - VERSÃO CORRIGIDA"""
    device = {
        'device_type': 'cisco_ios',
        'host': hostname,
        'username': username,
        'password': password,
        'port': os.getenv('PORT'),
        'timeout': os.getenv('TIMEOUT'),
        'session_timeout': os.getenv('SESSION_TIMEOUT'),
    }

    result = {
        'hostname': hostname_display,
        'ip': hostname,
        'success': False,
        'output': '',
        'error': None
    }

    try:
        ssh = ConnectHandler(**device)

        # Converte a lista de comandos em uma string única
        commands_string = '\n'.join(commands_list)

        # Envia todos os comandos de uma vez
        output = ssh.send_command_timing(commands_string, read_timeout=60)

        # Formata a saída
        prompt = ssh.find_prompt()
        final_output = f"=== Conectado em {hostname_display} ({hostname}) ===\n\n{prompt}\n{output}"
        result['output'] = final_output
        result['success'] = True

    except Exception as e:
        result['error'] = f'Erro de conexão: {str(e)}'
        result['output'] = f"=== ERRO em {hostname_display} ({hostname}) ===\n{str(e)}"

    finally:
        try:
            if 'ssh' in locals():
                ssh.disconnect()
        except Exception:
            pass

    return result


def execute_commands_massive(hostnames_data, username, password, commands):
    """
    Executa comandos em múltiplas OLTs em paralelo
    """
    commands_list = [cmd.strip() for cmd in commands.split('\n') if cmd.strip()]

    if not commands_list:
        return [{'error': 'Nenhum comando válido foi fornecido'}]

    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_host = {
            executor.submit(
                execute_commands_on_single_olt,
                ip,
                hostname_display,
                username,
                password,
                commands_list
            ): (ip, hostname_display)
            for ip, hostname_display in hostnames_data
        }

        for future in as_completed(future_to_host):
            ip, hostname_display = future_to_host[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                results.append({
                    'hostname': hostname_display,
                    'ip': ip,
                    'success': False,
                    'output': f"=== ERRO FATAL em {hostname_display} ({ip}) ===\n{str(exc)}",
                    'error': str(exc)
                })

    results.sort(key=lambda x: x['hostname'])
    return results
