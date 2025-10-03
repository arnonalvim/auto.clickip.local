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
    # Construir comando com suporte a wildcards
    chassis_param = chassis if chassis != '*' else '*'
    slot_param = slot if slot != '*' else '*'
    port_param = port_id if port_id != '*' else '*'
    command = f"show interface gpon {chassis_param}/{slot_param}/{port_param} onu | display json | nomore"
    device = {
        'device_type': 'cisco_ios',
        'host': hostname,
        'username': username,
        'password': password,
        'port': int(os.getenv('PORT', '22')),
        'timeout': int(os.getenv('TIMEOUT', '30')),
        'session_timeout': int(os.getenv('SESSION_TIMEOUT', '60')),
    }

    try:
        ssh = ConnectHandler(**device)
        output = ssh.send_command(command, read_timeout=1600)
        ssh.disconnect()
        try:
            json_data = json.loads(output)
            return {"success": True, "data": json_data}
        except json.JSONDecodeError as e:
            print(f"ERRO: Falha ao parsear JSON de {hostname}: {str(e)}")
            return {"success": False, "error": f"Erro ao parsear JSON: {str(e)}", "raw_output": output}
    except Exception as e:
        print(f"ERRO: Falha na conexão SSH com {hostname}: {str(e)}")
        return {"success": False, "error": f"Erro na conexão SSH: {str(e)}"}


def execute_firmware_update(hostname, username, password, selected_onus, firmware_file):
    """
    Executa TODOS os comandos de uma vez para uma OLT específica
    """
    device = {
        'device_type': 'cisco_ios',
        'host': hostname,
        'username': username,
        'password': password,
        'port': int(os.getenv('PORT', '22')),
        'timeout': int(os.getenv('TIMEOUT', '30')),
        'session_timeout': int(os.getenv('SESSION_TIMEOUT', '60')),
    }

    # Preparar TODOS os comandos de uma vez para esta OLT
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
        # Enviar TODOS os comandos de uma vez
        ssh.send_command_timing(commands_block, read_timeout=60, cmd_verify=False)
        ssh.disconnect()
        # Log de sucesso
        print(f"✅ [{hostname}] {len(all_commands)} comandos enviados com sucesso!")
        return {
            "success": True,
            "output": f"✅ [{hostname}] {len(all_commands)} comandos enviados com sucesso!\n\nComandos executados:\n" + "\n".join(all_commands),
            "commands_sent": len(all_commands),
            "hostname": hostname
        }
    except Exception as e:
        error_msg = f"❌ [{hostname}] Erro na execução: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "hostname": hostname,
            "commands_attempted": len(all_commands)
        }


def execute_firmware_update_multiple_olts(olts_data, username, password, firmware_file):
    """
    Nova função para executar atualizações em múltiplas OLTs de forma otimizada

    Args:
        olts_data: Dicionário com {hostname: [lista_de_onus]}
        username: Nome de usuário
        password: Senha
        firmware_file: Nome do arquivo de firmware
    Returns:
        Dicionário com resultados de cada OLT
    """
    results = {}
    total_onus = sum(len(onus) for onus in olts_data.values())
    print(f"🚀 Iniciando atualização em {len(olts_data)} OLTs para {total_onus} ONUs total...")
    for hostname, onus_list in olts_data.items():
        print(f"\n📡 Processando OLT: {hostname} ({len(onus_list)} ONUs)")
        result = execute_firmware_update(
            hostname=hostname,
            username=username,
            password=password,
            selected_onus=onus_list,
            firmware_file=firmware_file
        )
        results[hostname] = result
        # Log do resultado
        if result["success"]:
            print(f"✅ {hostname}: {result['commands_sent']} comandos enviados")
        else:
            print(f"❌ {hostname}: {result['error']}")
    # Estatísticas finais
    successful_olts = sum(1 for r in results.values() if r["success"])
    total_commands_sent = sum(r.get("commands_sent", 0) for r in results.values() if r["success"])
    print("📊 Resumo Final:")
    print(f"   • OLTs processadas: {len(olts_data)}")
    print(f"   • OLTs com sucesso: {successful_olts}")
    print(f"   • Total de comandos enviados: {total_commands_sent}")
    return {
        "results": results,
        "summary": {
            "total_olts": len(olts_data),
            "successful_olts": successful_olts,
            "total_commands_sent": total_commands_sent,
            "success_rate": (successful_olts / len(olts_data)) * 100 if olts_data else 0
        }
    }


def validate_firmware_file(hostname, username, password, firmware_file):
    """
    Nova função para validar se o arquivo de firmware existe na OLT
    Args:
        hostname: IP da OLT
        username: Nome de usuário
        password: Senha
        firmware_file: Nome do arquivo de firmware
    Returns:
        Dict com success (bool) e message (str)
    """
    device = {
        'device_type': 'cisco_ios',
        'host': hostname,
        'username': username,
        'password': password,
        'port': int(os.getenv('PORT', '22')),
        'timeout': int(os.getenv('TIMEOUT', '30')),
        'session_timeout': int(os.getenv('SESSION_TIMEOUT', '60')),
    }

    try:
        ssh = ConnectHandler(**device)
        # Comando para listar firmwares disponíveis
        output = ssh.send_command("show firmware onu | tab", read_timeout=30)
        ssh.disconnect()
        # Verificar se o arquivo está na lista
        if firmware_file in output:
            return {
                "success": True,
                "message": f"✅ Arquivo '{firmware_file}' encontrado na OLT {hostname}"
            }
        else:
            return {
                "success": False,
                "message": f"❌ Arquivo '{firmware_file}' NÃO encontrado na OLT {hostname}",
                "available_files": output
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Erro ao verificar firmware na OLT {hostname}: {str(e)}"
        }
