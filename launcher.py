import os
import subprocess
from sys import platform

processes = []

while True:
    action = input('Выберите действие: q - выход, s - запустить сервер и клиенты, x - закрыть все окна: ')
    if action == 'q':
        break
    elif action == 's':

        if platform == 'win32':
            # Работает только для Windows:
            processes.append(subprocess.Popen('python server.py',
                                              creationflags=subprocess.CREATE_NEW_CONSOLE))
            processes.append(subprocess.Popen('python client.py -n test1',
                                              creationflags=subprocess.CREATE_NEW_CONSOLE))
            processes.append(subprocess.Popen('python client.py -n test2',
                                              creationflags=subprocess.CREATE_NEW_CONSOLE))
            processes.append(subprocess.Popen('python client.py -n test3',
                                              creationflags=subprocess.CREATE_NEW_CONSOLE))

        elif platform == 'darwin':
            # MacOS:
            ser_script_path = os.path.join(os.getcwd(), 'server.py')
            cli_script_path = os.path.join(os.getcwd(), 'client.py')
            processes.append(subprocess.Popen(["osascript", "open_term.scpt", "python3 '" + ser_script_path + "'"]))
            processes.append(subprocess.Popen(["osascript", "open_term.scpt",
                                               "python3 '" + cli_script_path + "' -n test1"]))
            processes.append(subprocess.Popen(["osascript", "open_term.scpt",
                                               "python3 '" + cli_script_path + "' -n test2"]))
            processes.append(subprocess.Popen(["osascript", "open_term.scpt",
                                               "python3 '" + cli_script_path + "' -n test3"]))
    elif action == 'x':
        while processes:
            proc = processes.pop()
            proc.kill()
