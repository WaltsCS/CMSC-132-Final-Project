# run.py

from storage import memory, register, variable
from addressing import AddressingMode, Access
from bin_convert import Length, HalfPrecision


class Except:
    """
    Handles runtime exceptions.
    """

    def __init__(self, msg="", occur=True):
        self.message = msg
        self.occur = occur
        self.ret = None

    def dispMSG(self):
        print(self.message)

    def isOccur(self):
        return self.occur

    def setReturn(self, value):
        self.ret = value

    def getReturn(self):
        return self.ret


class Program:
    """
    Runs the encoded instruction codes from memory.
    """

    def __init__(self, program=None):
        # Optional compiler support
        if program is not None:
            from compiler import Instruction
            Instruction.encodeProgram(program)

    @staticmethod
    def exception(name, value=None):
        """
        Handles runtime exceptions.
        """

        if name == "DivByZero":

            exc = Except("Division By Zero")

            # 0 / 0
            if value == 0:
                exc.setReturn("undefined")

            # x / 0
            else:
                exc.setReturn("Infinity")

            return exc

        return Except("", False)

    @classmethod
    def write(cls, dest, src, movecode=0):
        """
        Perform write operations.
        movecode:
            0 = normal MOV
            1 = CALL
            2 = RET
            3 = SCAN
        """

        # CALL
        if movecode == 1:
            pc = register.load(variable.load("PC"))
            register.store(variable.load("CR"), pc)

        # RET
        elif movecode == 2:
            cr = register.load(variable.load("CR"))
            register.store(variable.load("PC"), cr)

        # SCAN
        elif movecode == 3:
            src = input()

        # Default write
        storage, addr = dest

        if storage == "register":
            register.store(addr, src)

        else:
            memory.store(addr, src)

    @classmethod
    def execute(cls, result, opcode):
        """
        Execute arithmetic or jump operations.
        """

        execute_bit = opcode[0]
        write_bit = opcode[1]
        category = opcode[2:]

        # Arithmetic instructions
        if write_bit == "1":

            op1 = result[0]
            op2 = result[1]

            # MOD
            if category == "000":
                return op1 % op2

            # ADD
            elif category == "001":
                return op1 + op2

            # SUB
            elif category == "010":
                return op1 - op2

            # MUL
            elif category == "011":
                return op1 * op2

            # DIV
            elif category == "100":

                if op2 == 0:
                    exc = cls.exception("DivByZero", op1)
                    exc.dispMSG()
                    return exc.getReturn()

                return op1 / op2

        # Jump instructions
        else:

            jr = register.load(variable.load("JR"))

            jump = False

            # JEQ
            if category == "000":
                jump = (jr == 0)

            # JNE
            elif category == "001":
                jump = (jr != 0)

            # JLT
            elif category == "010":
                jump = (jr < 0)

            # JLE
            elif category == "011":
                jump = (jr <= 0)

            # JGT
            elif category == "100":
                jump = (jr > 0)

            # JGE
            elif category == "101":
                jump = (jr >= 0)

            # JMP
            elif category == "110":
                jump = True

            return jump

    @classmethod
    def getOp(cls, inscode, immediate=False, relative=False):
        """
        Decode operand and return:
            value/effective address/storage
        """

        # Immediate mode
        if immediate:
            return HalfPrecision.hpbin2dec(inscode)

        mode = inscode[:4]
        addr = inscode[4:]

        addr_dec = int(addr, 2)

        # -----------------------------
        # Relative / Based modes
        # -----------------------------
        if relative:

            # BASED
            if mode == "0000":
                return AddressingMode.based(addr_dec)

            elif mode == "0001":
                return AddressingMode.based(memory.load(addr_dec))

            elif mode == "0010":
                return AddressingMode.based(addr_dec)

            elif mode == "0011":
                return AddressingMode.based(-addr_dec)

            # RELATIVE
            elif mode == "0100":
                return AddressingMode.relative(addr_dec)

            elif mode == "0101":
                return AddressingMode.relative(memory.load(addr_dec))

            elif mode == "0110":
                return AddressingMode.relative(addr_dec)

            elif mode == "0111":
                return AddressingMode.relative(-addr_dec)

        # -----------------------------
        # Normal Addressing Modes
        # -----------------------------

        # Register
        if mode == "0000":
            return AddressingMode.register(addr_dec)

        # Register indirect
        elif mode == "0001":
            return AddressingMode.registerIndirect(addr_dec)

        # Direct
        elif mode == "0010":
            return AddressingMode.direct(addr_dec)

        # Indirect
        elif mode == "0011":
            return AddressingMode.indirect(addr_dec)

        # Indexed
        elif mode == "0100":
            return AddressingMode.indexed(addr_dec)

        # Indexed integer displacement
        elif mode == "0101":
            return AddressingMode.indexed(addr_dec)

        # Auto increment
        elif mode == "0110":
            return AddressingMode.autoinc(addr_dec)

        # Auto decrement
        elif mode == "0111":
            return AddressingMode.autodec(addr_dec)

    @classmethod
    def run(cls):
        """
        Execute instructions from memory.
        """

        while True:

            # Current IR
            ir_addr = variable.load("IR")
            ir = register.load(ir_addr)

            # Fetch instruction
            ins = memory.load(ir)

            # Stop conditions
            if type(ins) != type(str()):
                break

            if len(ins) != Length.instrxn:
                break

            if int(ins, 2) == 0:
                break

            # ------------------------------------------------
            # Decode instruction
            # ------------------------------------------------

            opcode = ins[:5]

            ib = ins[5]

            op1mode = ins[6:10]
            op1addr = ins[10:17]

            rb = ins[17]

            op2mode = ins[18:22]
            op2addr = ins[22:29]

            extra = ins[29:]

            op1code = op1mode + op1addr

            # operand 1
            op1 = cls.getOp(op1code)

            # operand 2
            op2 = None

            if ib == "1":

                op2 = cls.getOp(extra.zfill(Length.precision),
                                immediate=True)

            else:

                op2code = op2mode + op2addr

                op2 = cls.getOp(op2code, relative=(rb == "1"))

            execute_bit = opcode[0]
            write_bit = opcode[1]

            # ------------------------------------------------
            # EXECUTE
            # ------------------------------------------------

            result = None

            if execute_bit == "1":

                # arithmetic
                if write_bit == "1":

                    val1 = op1[1]
                    val2 = op2[1] if type(op2) == tuple else op2

                    result = cls.execute([val1, val2], opcode)

                # jump
                else:

                    jump = cls.execute(None, opcode)

                    if jump:

                        # For JMP/JEQ/JNE/etc., op1 is usually B1-B8 or F1-F4.
                        # op1[0] is the memory address of B1/F1.
                        # op1[1] is the actual target instruction address stored in B1/F1.
                        target = op1[1] if type(op1) == tuple else op1

                        ir_addr = variable.load("IR")
                        pc_addr = variable.load("PC")

                        # Jump directly to target on the next fetch.
                        register.store(ir_addr, target)
                        register.store(pc_addr, target + 1)

                        # Skip the normal PC/IR update at the bottom of the loop.
                        continue

            # ------------------------------------------------
            # WRITE
            # ------------------------------------------------

            if write_bit == "1":

                movecode = 0

                # CALL
                if opcode == "01001":
                    movecode = 1

                # RET
                elif opcode == "01010":
                    movecode = 2

                # destination
                dest = (op1[2], op1[0])

                # MOV operation
                if execute_bit == "0":

                    src = op2[1] if type(op2) == tuple else op2

                else:
                    src = result

                cls.write(dest, src, movecode)

            # ------------------------------------------------
            # PRINT
            # ------------------------------------------------

            if execute_bit == "0" and write_bit == "0":

                print(op1)

            # ------------------------------------------------
            # Increment PC / IR
            # ------------------------------------------------

            pc_addr = variable.load("PC")
            ir_addr = variable.load("IR")

            pc = register.load(pc_addr)

            # Move current PC to IR first
            register.store(ir_addr, pc)

            # Then increment PC
            register.store(pc_addr, pc + 1)