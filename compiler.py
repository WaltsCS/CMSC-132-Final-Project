# compiler.py

from bin_convert import HalfPrecision, Length
from storage import memory, register, variable


# ------------------------------------------------------------
# Operation codes
# Format: Execute bit + Write bit + 3-bit category
# ------------------------------------------------------------

OPCODES = {
    # Execute + Write
    "MOD": "11000",
    "ADD": "11001",
    "CB":  "11001",
    "CF":  "11001",
    "SUB": "11010",
    "CMP": "11010",
    "MUL": "11011",
    "DIV": "11100",

    # Execute only / jumps
    "JEQ": "10000",
    "JNE": "10001",
    "JLT": "10010",
    "JLE": "10011",
    "JGT": "10100",
    "JGE": "10101",
    "JMP": "10110",

    # Write only / move-like
    "MOV":   "01000",
    "ADDPC": "01000",
    "CALL":  "01001",
    "RET":   "01010",
    "SCAN":  "01011",

    # Niladic / special
    "PRNT": "00000",
    "EOP":  "00001",
    "FUNC": "00001",
}


# ------------------------------------------------------------
# Addressing mode codes
# These are 4 bits because the given Length.opMode is 4
# and the uploaded run.py slices 4-bit operand modes.
# ------------------------------------------------------------

ADDR_MODE = {
    "REGISTER": "0000",
    "REGISTER_INDIRECT": "0001",
    "DIRECT": "0010",
    "INDIRECT": "0011",
    "INDEXED": "0100",
    "INDEXED_INT": "0101",
    "AUTOINC": "0110",
    "AUTODEC": "0111",
}


# For compatibility with the current run.py:
# Current run.py only reads the last 3 bits as "extra" for immediate values,
# so true HalfPrecision immediate operands will not decode correctly yet.
# To avoid breaking runtime, numeric operands are stored in a small memory
# constant pool and encoded as direct memory operands.
CONST_POOL_START = 117
_next_const_addr = CONST_POOL_START


class Instruction:
    """
    Converts assembly-like instructions into 32-bit instruction codes.
    """

    # ------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------

    @staticmethod
    def _is_number(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _addr_to_bin(addr):
        return Length.addZeros(int(addr), Length.opAddr)

    @staticmethod
    def _normal_operand(mode, addr):
        """
        Returns 11-bit operand code:
        4-bit addressing mode + 7-bit address
        """
        return mode + Instruction._addr_to_bin(addr)

    @staticmethod
    def _store_constant(value):
        """
        Store numeric constants in memory and return their address.
        This is used instead of true immediate mode for now because
        the current run.py does not fully decode 16-bit immediate operands.
        """
        global _next_const_addr

        addr = _next_const_addr

        if addr >= 128:
            raise MemoryError("Constant pool is full. No more memory slots available.")

        memory.store(addr, float(value))
        _next_const_addr += 1

        return addr

    @staticmethod
    def _lookup_variable_addr(name):
        """
        Gets the address of a named variable/register/memory symbol.
        Examples: A, B, R1, PC, ACC, B1, F1
        """
        try:
            return variable.load(name)
        except Exception:
            raise ValueError(f"Unknown operand or variable name: {name}")

    # ------------------------------------------------------------
    # Message decoding
    # ------------------------------------------------------------

    @staticmethod
    def decodeMSG(msg):
        """
        Converts encoded message text:
        - dash+underscore -> newline
        - dash -> space
        - underscore -> tab
        - word 'minus' -> dash
        - word 'under' -> underscore
        """

        msg = msg.replace("minus", "-")
        msg = msg.replace("under", "_")
        msg = msg.replace("-_", "\n")
        msg = msg.replace("-", " ")
        msg = msg.replace("_", "\t")

        return msg

    # ------------------------------------------------------------
    # Operand encoding
    # ------------------------------------------------------------

    @staticmethod
    def encodeOp(operand):
        """
        Encodes one operand into an 11-bit operand code:
        4-bit mode + 7-bit address.

        Supported forms:
            R1      -> register
            A       -> direct memory
            (R1)    -> register indirect
            (A)     -> memory indirect
            (R1+)   -> auto-increment
            (R1-)   -> auto-decrement
            5       -> stored in memory constant pool, encoded direct
        """

        operand = str(operand).strip()

        if operand == "":
            return "0" * Length.operand

        # Numeric literal.
        # Compatibility mode: store constant in memory, encode as direct.
        if Instruction._is_number(operand):
            const_addr = Instruction._store_constant(operand)
            return Instruction._normal_operand(ADDR_MODE["DIRECT"], const_addr)

        # Message operand, optional for SCAN/PRNT.
        if operand.startswith("M:"):
            msg = operand[2:]
            msg = Instruction.decodeMSG(msg)

            msg_index = variable.data["MI"]
            variable.data["MSG"][msg_index] = msg
            variable.data["MI"] = msg_index + 1

            return Instruction._normal_operand(ADDR_MODE["DIRECT"], msg_index)

        # Parenthesized addressing
        if operand.startswith("(") and operand.endswith(")"):
            inner = operand[1:-1].strip()

            # Auto-increment: (R1+)
            if inner.endswith("+"):
                reg_name = inner[:-1].strip()
                addr = Instruction._lookup_variable_addr(reg_name)
                return Instruction._normal_operand(ADDR_MODE["AUTOINC"], addr)

            # Auto-decrement: (R1-)
            if inner.endswith("-"):
                reg_name = inner[:-1].strip()
                addr = Instruction._lookup_variable_addr(reg_name)
                return Instruction._normal_operand(ADDR_MODE["AUTODEC"], addr)

            # Register indirect: (R1), (PC), (ACC), etc.
            if inner.startswith("R") or inner in ["PC", "ACC", "IR", "BR", "XR", "JR", "CR"]:
                addr = Instruction._lookup_variable_addr(inner)
                return Instruction._normal_operand(ADDR_MODE["REGISTER_INDIRECT"], addr)

            # Memory indirect: (A), (B), etc.
            addr = Instruction._lookup_variable_addr(inner)
            return Instruction._normal_operand(ADDR_MODE["INDIRECT"], addr)

        # Register addressing
        if operand.startswith("R") or operand in ["PC", "ACC", "IR", "BR", "XR", "JR", "CR"]:
            addr = Instruction._lookup_variable_addr(operand)
            return Instruction._normal_operand(ADDR_MODE["REGISTER"], addr)

        # Direct memory addressing
        addr = Instruction._lookup_variable_addr(operand)
        return Instruction._normal_operand(ADDR_MODE["DIRECT"], addr)

    # ------------------------------------------------------------
    # Relative / based operand encoding for second operand
    # ------------------------------------------------------------

    @staticmethod
    def encodeRelativeOp(operand, relative_type="relative"):
        """
        Encodes based/relative operands for ADDPC or future relative use.

        In run.py:
            rb == 1 means second operand is based/relative.

        Mode meanings in run.py:
            0000 based, displacement from register
            0001 based, displacement from memory
            0010 based, positive integer displacement
            0011 based, negative integer displacement
            0100 relative, displacement from register
            0101 relative, displacement from memory
            0110 relative, positive integer displacement
            0111 relative, negative integer displacement
        """

        operand = str(operand).strip()

        is_based = relative_type == "based"

        if Instruction._is_number(operand):
            value = int(float(operand))

            if is_based:
                mode = "0010" if value >= 0 else "0011"
            else:
                mode = "0110" if value >= 0 else "0111"

            return mode + Instruction._addr_to_bin(abs(value))

        addr = Instruction._lookup_variable_addr(operand)

        # Register displacement
        if operand.startswith("R") or operand in ["PC", "ACC", "IR", "BR", "XR", "JR", "CR"]:
            mode = "0000" if is_based else "0100"
            return mode + Instruction._addr_to_bin(addr)

        # Memory displacement
        mode = "0001" if is_based else "0101"
        return mode + Instruction._addr_to_bin(addr)

    # ------------------------------------------------------------
    # Instruction encoding
    # ------------------------------------------------------------

    @staticmethod
    def encode(inst):
        """
        Encodes one assembly-like instruction into a 32-bit instruction code.

        Current format compatible with uploaded run.py:
            opcode      5 bits
            ib          1 bit
            op1         11 bits
            rb          1 bit
            op2         11 bits
            extra       3 bits
            total       32 bits
        """

        if isinstance(inst, str):
            parts = inst.strip().split()
        else:
            parts = inst

        if len(parts) == 0:
            return None

        op = parts[0].upper()

        # FUNC and EOP are encoded as all zeroes to stop Program.run().
        if op in ["FUNC", "EOP"]:
            return "0" * Length.instrxn

        opcode = OPCODES.get(op)

        if opcode is None:
            raise ValueError(f"Unknown operation: {op}")

        ib = "0"
        rb = "0"
        extra = "000"

        op1 = "0" * Length.operand
        op2 = "0" * Length.operand

        # --------------------------------------------------------
        # Special instruction simplifications
        # --------------------------------------------------------

        # CMP X  -> SUB JR X
        if op == "CMP":
            if len(parts) < 2:
                raise ValueError("CMP requires one operand.")

            op1 = Instruction.encodeOp("JR")
            op2 = Instruction.encodeOp(parts[1])

        # CB B1 -> ADD B1 BR
        elif op == "CB":
            if len(parts) < 2:
                raise ValueError("CB requires one block operand.")

            op1 = Instruction.encodeOp(parts[1])
            op2 = Instruction.encodeOp("BR")

        # CF F1 -> ADD F1 BR
        elif op == "CF":
            if len(parts) < 2:
                raise ValueError("CF requires one function block operand.")

            op1 = Instruction.encodeOp(parts[1])
            op2 = Instruction.encodeOp("BR")

        # CALL F1 -> write PC to CR, then move F1 to PC
        # Compatible with current run.py movecode == 1.
        elif op == "CALL":
            if len(parts) < 2:
                raise ValueError("CALL requires one function operand.")

            op1 = Instruction.encodeOp("PC")
            op2 = Instruction.encodeOp(parts[1])

        # RET X -> move CR to PC, then move X to ACC
        # Compatible with current run.py movecode == 2.
        elif op == "RET":
            if len(parts) < 2:
                raise ValueError("RET requires one return operand.")

            op1 = Instruction.encodeOp("ACC")
            op2 = Instruction.encodeOp(parts[1])

        # ADDPC dest displacement
        elif op == "ADDPC":
            if len(parts) < 3:
                raise ValueError("ADDPC requires two operands.")

            op1 = Instruction.encodeOp(parts[1])
            rb = "1"
            op2 = Instruction.encodeRelativeOp(parts[2], relative_type="relative")

        # PRNT X
        elif op == "PRNT":
            if len(parts) >= 2:
                op1 = Instruction.encodeOp(parts[1])

        # SCAN dest message
        elif op == "SCAN":
            if len(parts) < 2:
                raise ValueError("SCAN requires at least one destination operand.")

            op1 = Instruction.encodeOp(parts[1])

            if len(parts) >= 3:
                op2 = Instruction.encodeOp(" ".join(parts[2:]))

        # Jump instructions: JEQ B1, JMP F1, etc.
        elif op in ["JEQ", "JNE", "JLT", "JLE", "JGT", "JGE", "JMP"]:
            if len(parts) < 2:
                raise ValueError(f"{op} requires one operand.")

            op1 = Instruction.encodeOp(parts[1])

        # Normal dyadic instructions: MOV, ADD, SUB, MUL, DIV, MOD
        else:
            if len(parts) < 3:
                raise ValueError(f"{op} requires two operands.")

            op1 = Instruction.encodeOp(parts[1])
            op2 = Instruction.encodeOp(parts[2])

        inscode = opcode + ib + op1 + rb + op2 + extra

        if len(inscode) != Length.instrxn:
            raise ValueError(
                f"Instruction length error for '{' '.join(parts)}': "
                f"got {len(inscode)} bits instead of {Length.instrxn}."
            )

        return inscode

    # ------------------------------------------------------------
    # Program encoding
    # ------------------------------------------------------------

    @staticmethod
    def encodeProgram(program):
        """
        Encodes a list of program instructions and stores them in memory.

        Handles:
            - blank lines
            - x single-line comments
            - z multiline comments
            - moving CB/CF instructions to the start
            - storing encoded instructions from BR address
        """

        global _next_const_addr
        _next_const_addr = CONST_POOL_START

        # Clear previous constants from the constant pool.
        for addr in range(CONST_POOL_START, 128):
            memory.store(addr, 0)

        cleaned = []
        in_multiline_comment = False

        # First pass: remove comments and blank lines
        for raw_line in program:
            line = raw_line.strip()

            if line == "":
                continue

            # Toggle multiline comment using z
            if line.startswith("z"):
                in_multiline_comment = not in_multiline_comment
                continue

            if in_multiline_comment:
                continue

            # Single-line comment using x
            if line.startswith("x"):
                continue

            cleaned.append(line)

        # Count CB/CF instructions first
        block_lines = []
        normal_lines = []

        for line in cleaned:
            op = line.split()[0].upper()

            if op in ["CB", "CF"]:
                block_lines.append(line)
            else:
                normal_lines.append(line)

        block_count = len(block_lines)

        start_addr = variable.load("BR")

        # Store number of blocks in BR, as required by the instructions.
        register.store(variable.load("BR"), block_count)

        # Store block/function start addresses.
        # The actual normal instructions begin after all CB/CF instructions.
        normal_start_addr = start_addr + block_count
        normal_counter = 0

        for line in cleaned:
            parts = line.split()
            op = parts[0].upper()

            if op in ["CB", "CF"] and len(parts) >= 2:
                block_name = parts[1]
                block_addr = variable.load(block_name)

                # Store the address of the next normal instruction.
                memory.store(block_addr, normal_start_addr + normal_counter)

            elif op not in ["CB", "CF"]:
                normal_counter += 1

        # Final instruction order:
        # all CB/CF first, then the rest
        final_lines = block_lines + normal_lines

        addr = start_addr

        for line in final_lines:
            inscode = Instruction.encode(line)

            if inscode is not None:
                memory.store(addr, inscode)
                addr += 1

        # Ensure there is an end marker after the program.
        memory.store(addr, "0" * Length.instrxn)