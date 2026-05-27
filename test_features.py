from run import Program
from storage import memory, register, variable


def reset_runtime():
    """
    Reset only the key runtime registers and simple memory variables.
    This helps make each test cleaner.
    """
    register.store(variable.load("IR"), variable.load("BR"))
    register.store(variable.load("PC"), variable.load("BR") + 1)

    for name in ["A", "B", "C", "D", "E", "F", "G", "H"]:
        memory.store(variable.load(name), 0)

    for name in ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]:
        register.store(variable.load(name), 0)

    register.store(variable.load("JR"), 0)
    register.store(variable.load("CR"), 0)


def run_program(program):
    reset_runtime()
    p = Program(program)
    p.run()


# ------------------------------------------------------------
# Test 1: MOD
# ------------------------------------------------------------

run_program([
    "MOV A 10",
    "MOD A 3",
    "EOP"
])

print("Test 1 - MOD")
print("Expected A = 1.0")
print("Actual A   =", memory.load(variable.load("A")))
print()


# ------------------------------------------------------------
# Test 2: Register addressing
# ------------------------------------------------------------

run_program([
    "MOV R1 5",
    "ADD R1 2",
    "MOV A R1",
    "EOP"
])

print("Test 2 - Register addressing")
print("Expected A = 7.0")
print("Actual A   =", memory.load(variable.load("A")))
print()


# ------------------------------------------------------------
# Test 3: Division by zero
# ------------------------------------------------------------

run_program([
    "MOV A 5",
    "DIV A 0",
    "EOP"
])

print("Test 3 - Division by zero")
print("Expected A = Infinity")
print("Actual A   =", memory.load(variable.load("A")))
print()


# ------------------------------------------------------------
# Test 4: Register indirect addressing
# ------------------------------------------------------------

run_program([
    "MOV R1 1",      # R1 points to memory address 1, which is A
    "MOV A 10",      # memory[1] = 10
    "ADD (R1) 5",    # memory[R1] = memory[R1] + 5
    "EOP"
])

print("Test 4 - Register indirect addressing")
print("Expected A = 15.0")
print("Actual A   =", memory.load(variable.load("A")))
print()


# ------------------------------------------------------------
# Test 5: Memory indirect addressing
# ------------------------------------------------------------

run_program([
    "MOV A 2",       # A stores address 2, which is B
    "MOV B 20",      # B = 20
    "ADD (A) 5",     # memory[memory[A]] = memory[2] = B = B + 5
    "EOP"
])

print("Test 5 - Memory indirect addressing")
print("Expected B = 25.0")
print("Actual B   =", memory.load(variable.load("B")))
print()


# ------------------------------------------------------------
# Test 6: Auto-increment addressing
# ------------------------------------------------------------

run_program([
    "MOV R1 1",      # R1 points to A
    "MOV A 10",
    "ADD (R1+) 5",   # use memory[R1], then R1 = R1 + 1
    "EOP"
])

print("Test 6 - Auto-increment addressing")
print("Expected A  = 15.0")
print("Actual A    =", memory.load(variable.load("A")))
print("Expected R1 = 2.0")
print("Actual R1   =", register.load(variable.load("R1")))
print()


# ------------------------------------------------------------
# Test 7: Auto-decrement addressing
# ------------------------------------------------------------

run_program([
    "MOV R1 2",      # R1 points after A, so decrement should point to A
    "MOV A 10",
    "ADD (R1-) 5",   # R1 = R1 - 1 first, then use memory[R1]
    "EOP"
])

print("Test 7 - Auto-decrement addressing")
print("Expected A  = 15.0")
print("Actual A    =", memory.load(variable.load("A")))
print("Expected R1 = 1.0")
print("Actual R1   =", register.load(variable.load("R1")))
print()


# ------------------------------------------------------------
# Test 8: CMP + JEQ
# ------------------------------------------------------------

run_program([
    "MOV A 5",
    "CMP A",
    "JEQ B1",
    "MOV A 99",
    "CB B1",
    "MOV A 10",
    "EOP"
])

print("Test 8 - CMP + JEQ")
print("Expected A = 10.0 if jump works")
print("Actual A   =", memory.load(variable.load("A")))
print()


# ------------------------------------------------------------
# Test 9: CMP + JNE should NOT jump when JR == 0
# ------------------------------------------------------------

run_program([
    "MOV JR 5",
    "MOV A 5",
    "CMP A",       # JR = 5 - 5 = 0
    "JNE B1",      # should NOT jump
    "MOV A 10",
    "EOP",
    "CB B1",
    "MOV A 99",
    "EOP"
])

print("Test 9 - CMP + JNE")
print("Expected A = 10.0 if JNE does NOT jump when JR == 0")
print("Actual A   =", memory.load(variable.load("A")))
print()


# ------------------------------------------------------------
# Test 10: CMP + JGT should jump when JR > 0
# ------------------------------------------------------------

run_program([
    "MOV JR 10",
    "MOV A 5",
    "CMP A",       # JR = 10 - 5 = 5
    "JGT B1",      # should jump
    "MOV A 99",
    "CB B1",
    "MOV A 10",
    "EOP"
])

print("Test 10 - CMP + JGT")
print("Expected A = 10.0 if JGT jumps when JR > 0")
print("Actual A   =", memory.load(variable.load("A")))
print()


# ------------------------------------------------------------
# Test 11: CMP + JLT should jump when JR < 0
# ------------------------------------------------------------

run_program([
    "MOV JR 2",
    "MOV A 5",
    "CMP A",       # JR = 2 - 5 = -3
    "JLT B1",      # should jump
    "MOV A 99",
    "CB B1",
    "MOV A 10",
    "EOP"
])

print("Test 11 - CMP + JLT")
print("Expected A = 10.0 if JLT jumps when JR < 0")
print("Actual A   =", memory.load(variable.load("A")))
print()


# ------------------------------------------------------------
# Test 12: JMP unconditional
# ------------------------------------------------------------

run_program([
    "JMP B1",
    "MOV A 99",
    "CB B1",
    "MOV A 10",
    "EOP"
])

print("Test 12 - JMP")
print("Expected A = 10.0 if JMP skips MOV A 99")
print("Actual A   =", memory.load(variable.load("A")))
print()


# ------------------------------------------------------------
# Test 13: Comments in encodeProgram
# ------------------------------------------------------------

run_program([
    "x this is a single-line comment",
    "MOV A 5",
    "z",
    "MOV A 99",
    "ADD A 99",
    "z",
    "ADD A 2",
    "EOP"
])

print("Test 13 - Comments")
print("Expected A = 7.0 if comments are skipped")
print("Actual A   =", memory.load(variable.load("A")))
print()


# ------------------------------------------------------------
# Test 14: CMP + JLE
# ------------------------------------------------------------

run_program([
    "MOV JR 5",
    "MOV A 5",
    "CMP A",       # JR = 5 - 5 = 0
    "JLE B1",      # should jump because JR <= 0
    "MOV A 99",
    "CB B1",
    "MOV A 10",
    "EOP"
])

print("Test 14 - CMP + JLE")
print("Expected A = 10.0 if JLE jumps when JR == 0")
print("Actual A   =", memory.load(variable.load("A")))
print()


# ------------------------------------------------------------
# Test 15: CMP + JGE
# ------------------------------------------------------------

run_program([
    "MOV JR 10",
    "MOV A 5",
    "CMP A",       # JR = 10 - 5 = 5
    "JGE B1",      # should jump because JR >= 0
    "MOV A 99",
    "CB B1",
    "MOV A 10",
    "EOP"
])

print("Test 15 - CMP + JGE")
print("Expected A = 10.0 if JGE jumps when JR > 0")
print("Actual A   =", memory.load(variable.load("A")))
print()


# ------------------------------------------------------------
# Test 16: CF + CALL + RET
# ------------------------------------------------------------

run_program([
    "CALL F1",
    "EOP",
    "CF F1",
    "MOV A 10",
    "RET A",
    "FUNC"
])

print("Test 16 - CF + CALL + RET")
print("Expected A   = 10.0 after function body")
print("Actual A     =", memory.load(variable.load("A")))
print("Expected ACC = 10.0 after RET A")
print("Actual ACC   =", register.load(variable.load("ACC")))
print()


# ------------------------------------------------------------
# Test 17: ADDPC / Relative addressing
# ------------------------------------------------------------

run_program([
    "ADDPC A 1",   # A should receive value from address PC + 1
    "MOV B 20",
    "EOP"
])

print("Test 17 - ADDPC / Relative addressing")
print("Expected: depends on current ADDPC behavior")
print("Actual A =", memory.load(variable.load("A")))
print("Actual B =", memory.load(variable.load("B")))
print()


# ------------------------------------------------------------
# Test 18: Indexed addressing
# ------------------------------------------------------------

reset_runtime()

# Manually prepare array-like memory.
# XR = 77, so indexed displacement 0 should point to memory[77].
register.store(variable.load("XR"), 77)
memory.store(77, 10)

program = [
    "ADD A 0",   # simple program just to trigger normal setup
    "EOP"
]

# Directly test the addressing mode method.
from addressing import AddressingMode

result = AddressingMode.indexed(0)

print("Test 18 - Indexed addressing direct method")
print("Expected effective address = 77.0")
print("Actual effective address   =", result[0])
print("Expected value             = 10.0")
print("Actual value               =", result[1])
print()


# ------------------------------------------------------------
# Test 19: Based addressing direct method
# ------------------------------------------------------------

reset_runtime()

from addressing import AddressingMode

# BR = 70, displacement = 5, so effective address should be 75.
register.store(variable.load("BR"), 70)
memory.store(75, 30)

result = AddressingMode.based(5)

print("Test 19 - Based addressing direct method")
print("Expected value             = 30.0")
print("Actual value               =", result)
print()


# ------------------------------------------------------------
# Test 20: Relative addressing direct method
# ------------------------------------------------------------

reset_runtime()

from addressing import AddressingMode

# PC = 80, displacement = 3, so effective address should be 83.
register.store(variable.load("PC"), 80)
memory.store(83, 40)

result = AddressingMode.relative(3)

print("Test 20 - Relative addressing direct method")
print("Expected value             = 40.0")
print("Actual value               =", result)
print()


# ------------------------------------------------------------
# Test 21: Indexed addressing through compiler syntax
# ------------------------------------------------------------

reset_runtime()

register.store(variable.load("XR"), 77)
memory.store(77, 10)

try:
    run_program([
        "ADD A (X+0)",
        "EOP"
    ])

    print("Test 21 - Indexed addressing through compiler syntax")
    print("Expected A = 10.0 if compiler supports (X+0)")
    print("Actual A   =", memory.load(variable.load("A")))
    print()

except Exception as e:
    print("Test 21 - Indexed addressing through compiler syntax")
    print("Compiler/runtime error:")
    print(type(e).__name__, ":", e)
    print()


# ------------------------------------------------------------
# Test 22: Based addressing through compiler syntax
# ------------------------------------------------------------

reset_runtime()

from run import Program

try:
    p = Program([
        "ADD A (Y+5)",
        "EOP"
    ])

    # Set BR after compilation, because encodeProgram() stores block_count in BR.
    register.store(variable.load("BR"), 70)
    memory.store(75, 30)

    p.run()

    print("Test 22 - Based addressing through compiler syntax")
    print("Expected A = 30.0 if compiler supports (Y+5)")
    print("Actual A   =", memory.load(variable.load("A")))
    print()

except Exception as e:
    print("Test 22 - Based addressing through compiler syntax")
    print("Compiler/runtime error:")
    print(type(e).__name__, ":", e)
    print()


# ------------------------------------------------------------
# Test 23: Relative addressing through compiler syntax
# ------------------------------------------------------------

reset_runtime()

from run import Program

try:
    p = Program([
        "ADD A (Z+3)",
        "EOP"
    ])

    # Program starts at BR address, usually 9.
    # First instruction is at IR = 9.
    # PC is usually 10 while first instruction runs.
    # So Z+3 should point to 10 + 3 = 13.
    memory.store(13, 40)

    p.run()

    print("Test 23 - Relative addressing through compiler syntax")
    print("Expected A = 40.0 if compiler supports (Z+3)")
    print("Actual A   =", memory.load(variable.load("A")))
    print()

except Exception as e:
    print("Test 23 - Relative addressing through compiler syntax")
    print("Compiler/runtime error:")
    print(type(e).__name__, ":", e)
    print()


# ------------------------------------------------------------
# Test 24: Negative indexed displacement through compiler syntax
# ------------------------------------------------------------

reset_runtime()

register.store(variable.load("XR"), 78)
memory.store(77, 15)

try:
    run_program([
        "ADD A (X-1)",
        "EOP"
    ])

    print("Test 24 - Negative indexed displacement")
    print("Expected A = 15.0 if (X-1) points to memory[77]")
    print("Actual A   =", memory.load(variable.load("A")))
    print()

except Exception as e:
    print("Test 24 - Negative indexed displacement")
    print("Compiler/runtime error:")
    print(type(e).__name__, ":", e)
    print()


# ------------------------------------------------------------
# Test 25: Negative based displacement through compiler syntax
# ------------------------------------------------------------

reset_runtime()

from run import Program

try:
    p = Program([
        "ADD A (Y-5)",
        "EOP"
    ])

    # Set BR after compilation because encodeProgram() overwrites BR.
    register.store(variable.load("BR"), 80)
    memory.store(75, 25)

    p.run()

    print("Test 25 - Negative based displacement")
    print("Expected A = 25.0 if (Y-5) points to memory[75]")
    print("Actual A   =", memory.load(variable.load("A")))
    print()

except Exception as e:
    print("Test 25 - Negative based displacement")
    print("Compiler/runtime error:")
    print(type(e).__name__, ":", e)
    print()


# ------------------------------------------------------------
# Test 26: PRNT instruction
# ------------------------------------------------------------

try:
    run_program([
        "MOV A 42",
        "PRNT A",
        "EOP"
    ])

    print("Test 26 - PRNT")
    print("Expected: console should print the value of A, likely 42.0")
    print("Actual A =", memory.load(variable.load("A")))
    print()

except Exception as e:
    print("Test 26 - PRNT")
    print("Compiler/runtime error:")
    print(type(e).__name__, ":", e)
    print()