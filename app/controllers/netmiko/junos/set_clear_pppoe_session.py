from app import create_app
from netmiko import ConnectHandler
import re
import time


def clear_pppoe_session(hostname, username, password, user_name):
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

    try:
        ssh = ConnectHandler(**router)
        # Primeiro comando: buscar a sessão PPPoE
        show_command = f'show subscribers user-name {user_name} | match pp0'
        initial_output = ssh.send_command(show_command)
        # Extrair o pp0 usando regex
        pp0_match = re.search(r'(pp0\.\d+)', initial_output)
        if not pp0_match:
            return f"Erro: Nenhuma sessão PPPoE encontrada para o usuário '{user_name}'\n\nSaída do comando:\n{initial_output}"
        pp0 = pp0_match.group(1)
        # Comando para limpar a sessão
        clear_command = f'clear pppoe sessions {pp0}'
        clear_output = ssh.send_command(clear_command)
        # Aguardar 10 segundos
        time.sleep(10)
        # Verificar novamente após a limpeza
        final_check = ssh.send_command(f'show subscribers user-name {user_name}')
        # Formatação da saída
        formatted_output = f"""=== RESULTADO DA LIMPEZA DE SESSÃO PPPoE ===

Usuário: {user_name}
Sessão encontrada: {pp0}

=== ANTES DA LIMPEZA ===
{initial_output}

=== COMANDO EXECUTADO ===
{clear_command}

=== RESULTADO DO CLEAR ===
Sessão pppoe limpa

=== VERIFICAÇÃO APÓS 10 SEGUNDOS ===
{final_check}

=== STATUS ===
Operação concluída com sucesso!"""

        return formatted_output

    except Exception as e:
        return f'Erro ao executar comandos: {e}'

    finally:
        if 'ssh' in locals():
            ssh.disconnect()
