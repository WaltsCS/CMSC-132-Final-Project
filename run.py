# run.py

# Import the simulated memory storage
from storage import memory, register, variable

# Import all addressing mode handlers
from addressing import AddressingMode, Access

# Import binary conversion utilities and instruction lengths
from bin_convert import Length, HalfPrecision


# =========================================================
# Exception Class
# =========================================================
class Except:
    """
    Handles runtime exceptions like division by zero.
    """

    # Constructor
    def __init__(self, msg="", occur=True):

        # Store the exception message
        self.message = msg

        # True if exception happened
        self.occur = occur

        # Optional return value from exception
        self.ret = None

    # Print the exception message
    def dispMSG(self):
        print(self.message)

    # Check whether exception occurred
    def isOccur(self):
        return self.occur

    # Save a return value
    def setReturn(self, value):
        self.ret = value

    # Get the saved return value
    def getReturn(self):
        return self.ret


# =========================================================
# Main CPU / Program Class
# =========================================================
class Program:
    """
    Simulates a CPU executing machine instructions.
    """

    # Shared division-by-zero exception object
    DIV_ZERO_EXCEPTION = Except("Division By Zero")

    # -----------------------------------------------------
    # Constructor
    # -----------------------------------------------------
    def __init__(self, program=None):

        # If a program list is provided
        if program is not None:

            # Import compiler only when needed
            from compiler import Instruction

            # Convert assembly instructions into machine code
            # and store them in memory
            Instruction.encodeProgram(program)

    # -----------------------------------------------------
    # Run Program From File
    # -----------------------------------------------------
    @classmethod
    def runFile(cls, filename, extension=".grp"):
        """
        Reads a source file, compiles it, and runs it.
        """

        # Check if file extension is correct
        if not filename.endswith(extension):

            # Stop program if extension is invalid
            raise ValueError(
                f"Invalid file extension. Expected '{extension}'"
            )

        # Try reading the file
        try:

            # Open the source file
            with open(filename, "r") as file:

                # Convert every line into a clean instruction
                instructions = [

                    # Remove spaces/newlines
                    line.strip()

                    # Loop through all file lines
                    for line in file

                    # Ignore blank lines
                    if line.strip() != ""
                ]

        # File does not exist
        except FileNotFoundError:

            print(f"File '{filename}' not found.")
            return

        # Compile instructions into memory
        cls(instructions)

        # Start execution
        cls.run()

    # -----------------------------------------------------
    # Exception Handler
    # -----------------------------------------------------
    @staticmethod
    def exception(name, value=None):
        """
        Handles runtime exceptions.
        """

        # Division by zero exception
        if name == "DivByZero":

            # Use shared exception object
            exc = Program.DIV_ZERO_EXCEPTION

            # Display error message
            exc.dispMSG()

            # If 0 / 0
            if value == 0:

                # Return Infinity
                exc.setReturn("Infinity")

            # If x / 0
            else:

                # Return undefined
                exc.setReturn("undefined")

            return exc

        # No exception
        return Except("", False)

    # -----------------------------------------------------
    # Write Operations
    # -----------------------------------------------------
    @classmethod
    def write(cls, dest, src, movecode=0):
        """
        Writes values into registers or memory.
        """

        # -------------------------------------------------
        # CALL instruction
        # -------------------------------------------------
        if movecode == 1:

            # Load current PC value
            pc = register.load(variable.load("PC"))

            # Save return address into CR
            register.store(variable.load("CR"), pc)

        # -------------------------------------------------
        # RET instruction
        # -------------------------------------------------
        elif movecode == 2:

            # Load saved return address
            cr = register.load(variable.load("CR"))

            # Restore PC
            register.store(variable.load("PC"), cr)

        # -------------------------------------------------
        # SCAN instruction
        # -------------------------------------------------
        elif movecode == 3:

            # Get user input
            src = input()

        # -------------------------------------------------
        # Normal write
        # -------------------------------------------------

        # Split destination into storage type and address
        storage, addr = dest

        # Write into register
        if storage == "register":

            register.store(addr, src)

        # Write into memory
        else:

            memory.store(addr, src)

    # -----------------------------------------------------
    # Execute Operations
    # -----------------------------------------------------
    @classmethod
    def execute(cls, result, opcode):

        # First bit tells if instruction executes
        execute_bit = opcode[0]

        # Second bit tells if instruction writes result
        write_bit = opcode[1]

        # Remaining bits determine instruction type
        category = opcode[2:]

        # -------------------------------------------------
        # Arithmetic Instructions
        # -------------------------------------------------
        if write_bit == "1":

            # First operand value
            op1 = result[0]

            # Second operand value
            op2 = result[1]

            # MOD instruction
            if category == "000":

                return op1 % op2

            # ADD instruction
            elif category == "001":

                return op1 + op2

            # SUB instruction
            elif category == "010":

                return op1 - op2

            # MUL instruction
            elif category == "011":

                return op1 * op2

            # DIV instruction
            elif category == "100":

                # Prevent division by zero
                if op2 == 0:

                    # Trigger exception
                    exc = cls.exception("DivByZero", op1)

                    return exc.getReturn()

                return op1 / op2

        # -------------------------------------------------
        # Jump Instructions
        # -------------------------------------------------
        else:

            # Load comparison result register
            jr = register.load(variable.load("JR"))

            # Default: no jump
            jump = False

            # Jump if equal
            if category == "000":

                jump = (jr == 0)

            # Jump if not equal
            elif category == "001":

                jump = (jr != 0)

            # Jump if less than
            elif category == "010":

                jump = (jr < 0)

            # Jump if less/equal
            elif category == "011":

                jump = (jr <= 0)

            # Jump if greater than
            elif category == "100":

                jump = (jr > 0)

            # Jump if greater/equal
            elif category == "101":

                jump = (jr >= 0)

            # Unconditional jump
            elif category == "110":

                jump = True

            return jump

    # -----------------------------------------------------
    # Decode Operand
    # -----------------------------------------------------
    @classmethod
    def getOp(cls, inscode, immediate=False, relative=False):

        # Immediate values are directly converted
        if immediate:

            return HalfPrecision.hpbin2dec(inscode)

        # First 4 bits = addressing mode
        mode = inscode[:4]

        # Remaining bits = address
        addr = inscode[4:]

        # Convert binary address into decimal
        addr_dec = int(addr, 2)

        # -------------------------------------------------
        # Relative / Based Addressing
        # -------------------------------------------------
        if relative:

            # Based addressing
            if mode == "0000":
                return AddressingMode.based(addr_dec)

            elif mode == "0001":
                return AddressingMode.based(memory.load(addr_dec))

            elif mode == "0010":
                return AddressingMode.based(addr_dec)

            elif mode == "0011":
                return AddressingMode.based(-addr_dec)

            # Relative addressing
            elif mode == "0100":
                return AddressingMode.relative(addr_dec)

            elif mode == "0101":
                return AddressingMode.relative(memory.load(addr_dec))

            elif mode == "0110":
                return AddressingMode.relative(addr_dec)

            elif mode == "0111":
                return AddressingMode.relative(-addr_dec)

        # -------------------------------------------------
        # Standard Addressing Modes
        # -------------------------------------------------

        # Register mode
        if mode == "0000":

            return AddressingMode.register(addr_dec)

        # Register indirect mode
        elif mode == "0001":

            return AddressingMode.registerIndirect(addr_dec)

        # Direct memory access
        elif mode == "0010":

            return AddressingMode.direct(addr_dec)

        # Indirect memory access
        elif mode == "0011":

            return AddressingMode.indirect(addr_dec)

        # Indexed addressing
        elif mode == "0100":

            return AddressingMode.indexed(addr_dec)

        # Indexed negative displacement
        elif mode == "0101":

            return AddressingMode.indexed(-addr_dec)

        # Auto increment mode
        elif mode == "0110":

            return AddressingMode.autoinc(addr_dec)

        # Auto decrement mode
        elif mode == "0111":

            return AddressingMode.autodec(addr_dec)

    # -----------------------------------------------------
    # Main CPU Execution Loop
    # -----------------------------------------------------
    @classmethod
    def run(cls):

        # Keep executing forever until stop condition
        while True:

            # -------------------------------------------------
            # FETCH PHASE
            # -------------------------------------------------

            # Get address of Instruction Register
            ir_addr = variable.load("IR")

            # Load current instruction pointer
            ir = register.load(ir_addr)

            # Fetch instruction from memory
            ins = memory.load(ir)

            # -------------------------------------------------
            # STOP CONDITIONS
            # -------------------------------------------------

            # Invalid instruction type
            if type(ins) != type(str()):

                break

            # Wrong instruction length
            if len(ins) != Length.instrxn:

                break

            # All-zero instruction = end of program
            if int(ins, 2) == 0:

                break

            # -------------------------------------------------
            # DECODE PHASE
            # -------------------------------------------------

            # First 5 bits = opcode
            opcode = ins[:5]

            # Immediate bit
            ib = ins[5]

            # Operand 1 mode bits
            op1mode = ins[6:10]

            # Operand 1 address bits
            op1addr = ins[10:17]

            # Relative addressing bit
            rb = ins[17]

            # Operand 2 mode bits
            op2mode = ins[18:22]

            # Operand 2 address bits
            op2addr = ins[22:29]

            # Extra bits
            extra = ins[29:]

            # Combine operand 1 mode + address
            op1code = op1mode + op1addr

            # Decode operand 1
            op1 = cls.getOp(op1code)

            # -------------------------------------------------
            # Decode operand 2
            # -------------------------------------------------

            # Immediate value mode
            if ib == "1":

                op2 = cls.getOp(
                    extra.zfill(Length.precision),
                    immediate=True
                )

            else:

                # Combine mode + address
                op2code = op2mode + op2addr

                # Decode operand 2
                op2 = cls.getOp(
                    op2code,
                    relative=(rb == "1")
                )

            # Extract execute/write bits
            execute_bit = opcode[0]
            write_bit = opcode[1]

            # -------------------------------------------------
            # EXECUTE PHASE
            # -------------------------------------------------

            # Default result
            result = None

            # Instruction performs execution
            if execute_bit == "1":

                # Arithmetic instruction
                if write_bit == "1":

                    # Get operand 1 value
                    val1 = op1[1]

                    # Get operand 2 value
                    val2 = op2[1] if type(op2) == tuple else op2

                    # Execute operation
                    result = cls.execute(
                        [val1, val2],
                        opcode
                    )

                # Jump instruction
                else:

                    # Evaluate jump condition
                    jump = cls.execute(None, opcode)

                    # If jump succeeds
                    if jump:

                        # Get jump target
                        target = (
                            op1[1]
                            if type(op1) == tuple
                            else op1
                        )

                        # Load IR and PC addresses
                        ir_addr = variable.load("IR")
                        pc_addr = variable.load("PC")

                        # Jump to target instruction
                        register.store(ir_addr, target)

                        # Move PC to next instruction after target
                        register.store(pc_addr, target + 1)

                        # Skip normal increment
                        continue

            # -------------------------------------------------
            # WRITE PHASE
            # -------------------------------------------------
            if write_bit == "1":

                # Default move operation
                movecode = 0

                # CALL instruction
                if opcode == "01001":

                    movecode = 1

                # RET instruction
                elif opcode == "01010":

                    movecode = 2

                # Destination location
                dest = (op1[2], op1[0])

                # MOV-style instructions
                if execute_bit == "0":

                    src = (
                        op2[1]
                        if type(op2) == tuple
                        else op2
                    )

                # Arithmetic result
                else:

                    src = result

                # Write final value
                cls.write(dest, src, movecode)

            # -------------------------------------------------
            # PRINT PHASE
            # -------------------------------------------------
            if execute_bit == "0" and write_bit == "0":

                # If operand contains address/value tuple
                if type(op1) == tuple:

                    print(op1[1])

                # Direct value
                else:

                    print(op1)

            # -------------------------------------------------
            # UPDATE PC / IR
            # -------------------------------------------------

            # Get PC register address
            pc_addr = variable.load("PC")

            # Get IR register address
            ir_addr = variable.load("IR")

            # Load current PC value
            pc = register.load(pc_addr)

            # Move current PC into IR
            register.store(ir_addr, pc)

            # Increment PC
            register.store(pc_addr, pc + 1)

