import os
import json
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()


def get_onus_info(hostname, username, password, chassis, slot, port_id):
    """
    Executa o comando para obter informações das ONUs em formato JSON
    Suporta wildcard "*" para chassis, slot e port_id
    """
    device = {
        'device_type': 'cisco_ios',
        'host': hostname,
        'username': username,
        'password': password,
        'port': os.getenv('PORT'),
        'timeout': os.getenv('TIMEOUT'),
        'session_timeout': os.getenv('SESSION_TIMEOUT'),
    }

    # Construir comando com suporte a wildcards
    chassis_param = chassis if chassis != '*' else '*'
    slot_param = slot if slot != '*' else '*'
    port_param = port_id if port_id != '*' else '*'
    command = f"show interface gpon {chassis_param}/{slot_param}/{port_param} onu | display json | nomore"

    try:
        ssh = ConnectHandler(**device)
        output = ssh.send_command(command, read_timeout=1600)
        ssh.disconnect()
        try:
            json_data = json.loads(output)
            return {"success": True, "data": json_data}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Erro ao parsear JSON: {str(e)}", "raw_output": output}
    except Exception as e:
        return {"success": False, "error": f"Erro na conexão SSH: {str(e)}"}


def execute_firmware_update(hostname, username, password, selected_onus, firmware_file):
    """
    Executa TODOS os comandos de uma vez - VERSÃO OTIMIZADA!
    Já que os comandos não retornam resposta útil, podemos enviar em lote
    """
    device = {
        'device_type': 'cisco_ios',
        'host': hostname,
        'username': username,
        'password': password,
        'port': os.getenv('PORT'),
        'timeout': os.getenv('TIMEOUT'),
        'session_timeout': os.getenv('SESSION_TIMEOUT'),
    }

    # Preparar TODOS os comandos de uma vez
    all_commands = []
    for onu_info in selected_onus:
        chassis = onu_info['chassis']
        slot = onu_info['slot']
        port = onu_info['port']
        onu_id = onu_info['onu_id']
        command = f"request firmware onu install {firmware_file} interface gpon {chassis}/{slot}/{port} onu {onu_id}"
        all_commands.append(command)
    # Criar um único bloco de comandos
    commands_block = "\n".join(all_commands)

    try:
        ssh = ConnectHandler(**device)
        # Enviar TODOS os comandos de uma vez!
        # Como não retorna nada útil, usamos timeout baixo
        ssh.send_command_timing(commands_block, read_timeout=50, cmd_verify=False)
        ssh.disconnect()
        return {
            "success": True,
            "output": f"✅ {len(all_commands)} comandos enviados com sucesso!\n\nComandos executados:\n" + "\n".join(all_commands)
        }
    except Exception as e:
        return {"success": False, "error": f"Erro na execução: {str(e)}"}
