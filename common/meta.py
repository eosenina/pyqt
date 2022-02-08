import dis


# Metaclass for server
class ServerMaker(type):
    def __init__(self, clsname, bases, clsdict):
        methods = []
        attrs = []
        for item in clsdict:
            try:
                instructions = dis.get_instructions(clsdict[item])
            except TypeError:
                pass
            else:
                for i in instructions:
                    if i.opname == 'LOAD_GLOBAL' and i.argval not in methods:
                        methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR' and i.argval not in attrs:
                        attrs.append(i.argval)
        if 'connect' in methods:
            raise TypeError('Использование метода connect недопустимо в серверном классе')
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета.')

        super().__init__(clsname, bases, clsdict)
