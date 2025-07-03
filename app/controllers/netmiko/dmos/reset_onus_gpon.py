import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()


def execute_reset_onus_gpon(hostname, username, password, chassis, slot, port_id):
    device = {
        'device_type': 'cisco_ios',
        'host': hostname,
        'username': username,
        'password': password,
        'port': os.getenv('PORT'),
        'timeout': os.getenv('TIMEOUT'),
        'session_timeout': os.getenv('SESSION_TIMEOUT'),
    }

    # Comando completo pq n sei colocar menor e o chatgpt nao me mostrou uma forma simples
    reset_commands = f"""config
interface gpon {chassis}/{slot}/{port_id}
onu-reset onu 0
yes
onu-reset onu 1
yes
onu-reset onu 2
yes
onu-reset onu 3
yes
onu-reset onu 4
yes
onu-reset onu 5
yes
onu-reset onu 6
yes
onu-reset onu 7
yes
onu-reset onu 8
yes
onu-reset onu 9
yes
onu-reset onu 10
yes
onu-reset onu 11
yes
onu-reset onu 12
yes
onu-reset onu 13
yes
onu-reset onu 14
yes
onu-reset onu 15
yes
onu-reset onu 16
yes
onu-reset onu 17
yes
onu-reset onu 18
yes
onu-reset onu 19
yes
onu-reset onu 20
yes
onu-reset onu 21
yes
onu-reset onu 22
yes
onu-reset onu 23
yes
onu-reset onu 24
yes
onu-reset onu 25
yes
onu-reset onu 26
yes
onu-reset onu 27
yes
onu-reset onu 28
yes
onu-reset onu 29
yes
onu-reset onu 30
yes
onu-reset onu 31
yes
onu-reset onu 32
yes
onu-reset onu 33
yes
onu-reset onu 34
yes
onu-reset onu 35
yes
onu-reset onu 36
yes
onu-reset onu 37
yes
onu-reset onu 38
yes
onu-reset onu 39
yes
onu-reset onu 40
yes
onu-reset onu 41
yes
onu-reset onu 42
yes
onu-reset onu 43
yes
onu-reset onu 44
yes
onu-reset onu 45
yes
onu-reset onu 46
yes
onu-reset onu 47
yes
onu-reset onu 48
yes
onu-reset onu 49
yes
onu-reset onu 50
yes
onu-reset onu 51
yes
onu-reset onu 52
yes
onu-reset onu 53
yes
onu-reset onu 54
yes
onu-reset onu 55
yes
onu-reset onu 56
yes
onu-reset onu 57
yes
onu-reset onu 58
yes
onu-reset onu 59
yes
onu-reset onu 60
yes
onu-reset onu 61
yes
onu-reset onu 62
yes
onu-reset onu 63
yes
onu-reset onu 64
yes
onu-reset onu 65
yes
onu-reset onu 66
yes
onu-reset onu 67
yes
onu-reset onu 68
yes
onu-reset onu 69
yes
onu-reset onu 70
yes
onu-reset onu 71
yes
onu-reset onu 72
yes
onu-reset onu 73
yes
onu-reset onu 74
yes
onu-reset onu 75
yes
onu-reset onu 76
yes
onu-reset onu 77
yes
onu-reset onu 78
yes
onu-reset onu 79
yes
onu-reset onu 80
yes
onu-reset onu 81
yes
onu-reset onu 82
yes
onu-reset onu 83
yes
onu-reset onu 84
yes
onu-reset onu 85
yes
onu-reset onu 86
yes
onu-reset onu 87
yes
onu-reset onu 88
yes
onu-reset onu 89
yes
onu-reset onu 90
yes
onu-reset onu 91
yes
onu-reset onu 92
yes
onu-reset onu 93
yes
onu-reset onu 94
yes
onu-reset onu 95
yes
onu-reset onu 96
yes
onu-reset onu 97
yes
onu-reset onu 98
yes
onu-reset onu 99
yes
onu-reset onu 100
yes
onu-reset onu 101
yes
onu-reset onu 102
yes
onu-reset onu 103
yes
onu-reset onu 104
yes
onu-reset onu 105
yes
onu-reset onu 106
yes
onu-reset onu 107
yes
onu-reset onu 108
yes
onu-reset onu 109
yes
onu-reset onu 110
yes
onu-reset onu 111
yes
onu-reset onu 112
yes
onu-reset onu 113
yes
onu-reset onu 114
yes
onu-reset onu 115
yes
onu-reset onu 116
yes
onu-reset onu 117
yes
onu-reset onu 118
yes
onu-reset onu 119
yes
onu-reset onu 120
yes
onu-reset onu 121
yes
onu-reset onu 122
yes
onu-reset onu 123
yes
onu-reset onu 124
yes
onu-reset onu 125
yes
onu-reset onu 126
yes
onu-reset onu 127
yes
top
exit
"""

    try:
        ssh = ConnectHandler(**device)
        output = ssh.send_command_timing(reset_commands, read_timeout=5)
        final_output = [
            ssh.find_prompt(),
            output
        ]

    except Exception as e:
        print(f'Error to execute commands: {e}')
        final_output = [f'Erro na execução: {str(e)}']

    finally:
        ssh.disconnect()

    if final_output:
        formatted_output = ''.join(final_output)

    return formatted_output
