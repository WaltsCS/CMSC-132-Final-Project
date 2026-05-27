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