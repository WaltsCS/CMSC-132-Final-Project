# This file contains a Access class for easy acces of memory and register and AddressingMode class.

# addressing.py

from storage import memory, register, variable


class Access:
    @staticmethod
    def data(addr, flow):
        current = addr

        for typ in flow:
            if typ == "var":
                current = variable.load(current)
            elif typ == "reg":
                current = register.load(current)
            elif typ == "mem":
                current = memory.load(current)

        return current

    @staticmethod
    def store(typ, addr, value):
        if typ == "reg" or typ == "register":
            register.store(addr, value)
        elif typ == "mem" or typ == "memory":
            memory.store(addr, value)


class AddressingMode:
    @staticmethod
    def register(reg_addr):
        value = register.load(reg_addr)
        return reg_addr, value, "register"

    @staticmethod
    def registerIndirect(reg_addr):
        effective_addr = register.load(reg_addr)
        value = memory.load(effective_addr)
        return effective_addr, value, "memory"

    @staticmethod
    def direct(var_addr):
        value = memory.load(var_addr)
        return var_addr, value, "memory"

    @staticmethod
    def indirect(var_addr):
        effective_addr = memory.load(var_addr)
        value = memory.load(effective_addr)
        return effective_addr, value, "memory"

    @staticmethod
    def indexed(displace):
        effective_addr = register.load(variable.load("XR")) + displace
        value = memory.load(effective_addr)
        return effective_addr, value, "memory"

    @staticmethod
    def autoinc(reg_addr):
        effective_addr = register.load(reg_addr)
        value = memory.load(effective_addr)
        register.store(reg_addr, effective_addr + 1)
        return effective_addr, value, "memory"

    @staticmethod
    def autodec(reg_addr):
        effective_addr = register.load(reg_addr) - 1
        register.store(reg_addr, effective_addr)
        value = memory.load(effective_addr)
        return effective_addr, value, "memory"

    @staticmethod
    def based(displace):
        effective_addr = register.load(variable.load("BR")) + displace
        value = memory.load(effective_addr)
        return effective_addr, value, "memory"

    @staticmethod
    def relative(displace):
        effective_addr = register.load(variable.load("PC")) + displace
        value = memory.load(effective_addr)
        return effective_addr, value, "memory"

    @staticmethod
    def immediate(value):
        return value