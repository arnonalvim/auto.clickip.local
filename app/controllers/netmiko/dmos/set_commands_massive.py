import os
from dotenv import load_dotenv
from netmiko import ConnectHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

load_dotenv()

# Thread-local será como um armazenamento local de thread
thread_local = threading.local()


def execute_commands_on_single_olt(hostname, hostname_display, username, password, commands_list):
    """Executa comandos em uma única OLT"""
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
        output_lines = [f"=== Conectado em {hostname_display} ({hostname}) ===\n"]

        for command in commands_list:
            if command.strip():  # Ignora linhas vazias
                try:
                    prompt = ssh.find_prompt()
                    command_output = ssh.send_command(command.strip(), expect_string=r'#', read_timeout=30)

                    output_lines.append(f"{prompt} {command.strip()}")
                    output_lines.append(command_output)
                    output_lines.append("-" * 50)

                except Exception as cmd_error:
                    output_lines.append(f"ERRO ao executar '{command.strip()}': {str(cmd_error)}")
                    output_lines.append("-" * 50)

        result['output'] = '\n'.join(output_lines)
        result['success'] = True

    except Exception as e:
        result['error'] = f'Erro de conexão: {str(e)}'
        result['output'] = f"=== ERRO em {hostname_display} ({hostname}) ===\n{str(e)}"

    finally:
        try:
            ssh.disconnect()
        except Exception:
            pass

    return result


def execute_commands_massive(hostnames_data, username, password, commands):
    """
    Executa comandos em múltiplas OLTs em paralelo

    Args:
        hostnames_data: Lista de tuplas (ip, hostname_display)
        username: Nome de usuário
        password: Senha
        commands: String com comandos separados por quebra de linha

    Returns:
        Lista de resultados para cada OLT
    """
    # Separa os comandos por linha
    commands_list = [cmd.strip() for cmd in commands.split('\n') if cmd.strip()]

    if not commands_list:
        return [{'error': 'Nenhum comando válido foi fornecido'}]

    results = []

    # Executa em paralelo com ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Executa as tarefas
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

        # Coleta os resultados conforme completam
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

    # Ordena os resultados por hostname para consistência, assim o usuário vê equiapmento que deu erro e qual não deu
    results.sort(key=lambda x: x['hostname'])

    return results
