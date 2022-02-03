# Задание 1
# Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность
# сетевых узлов. Аргументом функции является список, в котором каждый сетевой узел должен быть
# представлен именем хоста или ip-адресом. В функции необходимо перебирать ip-адреса и проверять
# их доступность с выводом соответствующего сообщения («Узел доступен», «Узел недоступен»).
# При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
import socket
from ipaddress import ip_address
from subprocess import Popen, PIPE


def host_ping(ip_list, timeout=500, requests=1):
    results = {'Доступные узлы': "", 'Недоступные узлы': ""}
    for address in ip_list:
        try:
            ip = ip_address(address)
        except ValueError:
            ip = socket.gethostbyname(address)
        # works for MacOS
        proc = Popen(['ping', '-W', str(timeout), '-c', str(requests), str(ip)], stdout=PIPE)
        proc.wait()
        if proc.returncode == 0:
            results['Доступные узлы'] += f"{address}\n"
            result_str = f'{address} - Узел доступен'
        else:
            results['Недоступные узлы'] += f"{address}\n"
            result_str = f'{address} - Узел недоступен'
        print(result_str)
    return results


if __name__ == '__main__':
    ip_lst = ['ya.ru', '2.2.2.2', '87.250.250.242', '192.168.0.100']
    host_ping(ip_lst)
