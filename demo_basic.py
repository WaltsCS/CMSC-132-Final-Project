from run import Program
from storage import memory, register, variable


def reset_runtime():
    """
    Reset memory and registers so every demo starts cleanly.
    """
    # Clear memory
    for addr in range(128):
        memory.store(addr, 0)

    # Reset general memory variables A-H
    for name in ["A", "B", "C", "D", "E", "F", "G", "H"]:
        memory.store(variable.load(name), 0)

    # Reset general registers R1-R8
    for name in ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]:
        register.store(variable.load(name), 0)

    # Reset special registers
    register.store(variable.load("BR"), variable.load("BR"))
    register.store(variable.load("XR"), 77)
    register.store(variable.load("ACC"), 0)
    register.store(variable.load("IR"), variable.load("BR"))
    register.store(variable.load("PC"), variable.load("BR") + 1)
    register.store(variable.load("JR"), 0)
    register.store(variable.load("CR"), 0)

    # Reset block/function memory locations
    for name in ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]:
        memory.store(variable.load(name), 0)

    for name in ["F1", "F2", "F3", "F4"]:
        memory.store(variable.load(name), 0)


def run_demo(title, program, watch_memory=None, watch_registers=None):
    """
    Compile and run one demo program, then print selected memory/register values.
    """
    reset_runtime()

    print("=" * 60)
    print(title)
    print("=" * 60)

    print("\nProgram:")
    for line in program:
        print(" ", line)

    print("\nOutput:")
    p = Program(program)
    p.run()

    if watch_memory:
        print("\nMemory values:")
        for name in watch_memory:
            print(f"{name} =", memory.load(variable.load(name)))

    if watch_registers:
        print("\nRegister values:")
        for name in watch_registers:
            print(f"{name} =", register.load(variable.load(name)))

    print()


# ============================================================
# Demo 1: Simple arithmetic + PC/IR behavior
# ============================================================

demo1 = [
    "MOV A 5",
    "ADD A 2",
    "SUB A 1",
    "MUL A 3",
    "DIV A 2",
    "EOP"
]

run_demo(
    "Demo 1: Simple Arithmetic + PC/IR Behavior",
    demo1,
    watch_memory=["A"],
    watch_registers=["PC", "IR"]
)


# ============================================================
# Demo 2: CMP + JGT/JMP + CB block behavior
# ============================================================

demo2 = [
    "MOV JR 10",
    "MOV A 5",
    "CMP A",
    "JGT B1",
    "MOV A 99",
    "CB B1",
    "MOV A 10",
    "EOP"
]

run_demo(
    "Demo 2: CMP + JGT + CB Block Jump",
    demo2,
    watch_memory=["A", "B1"],
    watch_registers=["JR", "PC", "IR"]
)


# ============================================================
# Demo 3: CF + CALL + RET + ACC behavior
# ============================================================

demo3 = [
    "CALL F1",
    "EOP",
    "CF F1",
    "MOV A 10",
    "RET A",
    "FUNC"
]

run_demo(
    "Demo 3: CF + CALL + RET + ACC",
    demo3,
    watch_memory=["A", "F1"],
    watch_registers=["ACC", "CR", "PC", "IR"]
)


# ============================================================
# Demo 4: Except class / Division by zero handling
# ============================================================

demo4 = [
    "MOV A 5",
    "DIV A 0",
    "EOP"
]

run_demo(
    "Demo 4: Except Class Handling / Division by Zero",
    demo4,
    watch_memory=["A"],
    watch_registers=["PC", "IR"]
)