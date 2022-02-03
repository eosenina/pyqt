# Задание 2
# Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
# Меняться должен только последний октет каждого адреса. По результатам проверки должно
# выводиться соответствующее сообщение.

from ipaddress import ip_address
from task1 import host_ping


def host_range_ping():
    while True:
        start = input('Введите первоначальный адрес: ')
        try:
            last_oct = int(start.split('.')[3])
            break
        except Exception as e:
            print(e)
    while True:
        try:
            count = int(input('Сколько адресов проверить?: '))
        except ValueError:
            print('Необходимо ввести число: ')
            continue
        if last_oct + count > 255:
            print(f"Максимальное число хостов для проверки: {255-last_oct}")
        else:
            break

    host_list = []
    [host_list.append(str(ip_address(start) + i)) for i in range(count)]
    return host_ping(host_list)


if __name__ == "__main__":
    host_range_ping()
