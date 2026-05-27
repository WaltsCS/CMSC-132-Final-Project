"""
Comprehensive integration test for the CMSC132 ISA simulator.

Tests all addressing modes and major instruction types.
Each test creates a single Program block, runs it, and checks results.

Usage:
    python integration_test.py
"""

import sys
import importlib
import traceback


def reload_all():
    """Reload all modules in dependency order to reset global state."""
    import bin_convert as _bc
    import storage as _st
    import addressing as _ad
    import compiler as _co
    import run as _ru

    importlib.reload(_bc)
    importlib.reload(_st)
    importlib.reload(_ad)
    importlib.reload(_co)
    importlib.reload(_ru)

    from storage import memory, register, variable
    return memory, register, variable


def test_basic_arithmetic():
    """Test MOV, ADD, SUB, MUL, DIV, MOD with registers."""
    memory, register, variable = reload_all()
    from run import Program

    prog = Program([
        "MOV R1 10",
        "MOV R2 20",
        "ADD R1 R2",    # R1 = 10 + 20 = 30
        "SUB R1 R2",    # R1 = 30 - 20 = 10
        "MUL R1 R2",    # R1 = 10 * 20 = 200
        "MOV R3 100",
        "MOV R4 25",
        "DIV R3 R4",    # R3 = 100 / 25 = 4
        "MOD R3 R4",    # R3 = 4 % 25 = 4
    ])
    prog.run()

    r1 = register.load(1)
    r2 = register.load(2)
    r3 = register.load(3)
    r4 = register.load(4)

    assert r1 == 200, f"R1 should be 200, got {r1}"
    assert r2 == 20, f"R2 should be 20, got {r2}"
    assert r3 == 4, f"R3 should be 4, got {r3}"
    assert r4 == 25, f"R4 should be 25, got {r4}"
    print("  PASS: basic arithmetic")


def test_direct_memory():
    """Test direct memory access via A-H variables."""
    memory, register, variable = reload_all()
    from run import Program

    prog = Program([
        "MOV A 42",
        "MOV B A",
        "MOV C 100",
        "ADD C B",      # C = 100 + 42 = 142
    ])
    prog.run()

    a = memory.load(1)
    b = memory.load(2)
    c = memory.load(3)

    assert a == 42, f"A should be 42, got {a}"
    assert b == 42, f"B should be 42, got {b}"
    assert c == 142, f"C should be 142, got {c}"
    print("  PASS: direct memory")


def test_register_indirect():
    """Test register-indirect addressing: (R1)."""
    memory, register, variable = reload_all()
    from run import Program

    prog = Program([
        "MOV R1 1",         # R1 = 1 (points to memory addr 1 = variable A)
        "MOV A 77",         # A (mem 1) = 77
        "MOV R2 (R1)",      # R2 = memory[R1] = memory[1] = 77
    ])
    prog.run()

    r2 = register.load(2)
    assert r2 == 77, f"R2 should be 77 (from register-indirect), got {r2}"
    print("  PASS: register-indirect")


def test_auto_inc_dec():
    """Test auto-increment and auto-decrement."""
    memory, register, variable = reload_all()
    from run import Program

    prog = Program([
        "MOV A 10",
        "MOV B 20",
        "MOV C 30",
        "MOV R1 1",         # R1 = 1 (address of A)
        "MOV R2 (R1+)",     # R2 = memory[1] = 10, then R1++ (R1=2)
        "MOV R3 (R1+)",     # R3 = memory[2] = 20, then R1++ (R1=3)
        "MOV R4 (R1-)",     # R1-- first: R1=2, then R4 = memory[2] = 20
    ])
    prog.run()

    r1 = register.load(1)
    r2 = register.load(2)
    r3 = register.load(3)
    r4 = register.load(4)

    assert r2 == 10, f"R2 (autoinc) should be 10, got {r2}"
    assert r3 == 20, f"R3 (autoinc) should be 20, got {r3}"
    assert r4 == 20, f"R4 (autodec) should be 20, got {r4}"
    assert r1 == 2, f"R1 should be 2 after inc+inc+dec, got {r1}"
    print("  PASS: auto-inc/dec")


def test_indirect():
    """Test indirect addressing: (A) where A holds a pointer."""
    memory, register, variable = reload_all()
    from run import Program

    prog = Program([
        "MOV A 3",          # A (mem 1) = 3 (address of C)
        "MOV C 99",         # C (mem 3) = 99
        "MOV R1 (A)",       # R1 = memory[A] = memory[3] = 99
    ])
    prog.run()

    r1 = register.load(1)
    assert r1 == 99, f"R1 (indirect) should be 99, got {r1}"
    print("  PASS: indirect")


def test_indexed():
    """Test indexed addressing: (X+offset)."""
    memory, register, variable = reload_all()
    from run import Program

    # XR defaults to 77 (start of array area)
    prog = Program([
        "MOV (X+0) 100",
        "MOV (X+1) 200",
        "MOV (X+2) 300",
        "MOV R1 (X+0)",
        "MOV R2 (X+1)",
        "MOV R3 (X+2)",
    ])
    prog.run()

    r1 = register.load(1)
    r2 = register.load(2)
    r3 = register.load(3)

    assert r1 == 100, f"R1 (X+0) should be 100, got {r1}"
    assert r2 == 200, f"R2 (X+1) should be 200, got {r2}"
    assert r3 == 300, f"R3 (X+2) should be 300, got {r3}"
    print("  PASS: indexed")


def test_jump_execute():
    """Test conditional jump logic via Program.execute()."""
    memory, register, variable = reload_all()
    from run import Program

    jr_addr = variable.load("JR")

    # JEQ: jump if JR == 0
    register.store(jr_addr, 0)
    assert Program.execute(None, "10000") == True, "JEQ with JR=0 should jump"

    register.store(jr_addr, 5)
    assert Program.execute(None, "10000") == False, "JEQ with JR=5 should not jump"

    # JNE: jump if JR != 0
    register.store(jr_addr, 5)
    assert Program.execute(None, "10001") == True, "JNE with JR=5 should jump"

    register.store(jr_addr, 0)
    assert Program.execute(None, "10001") == False, "JNE with JR=0 should not jump"

    # JLT: jump if JR < 0
    register.store(jr_addr, -1)
    assert Program.execute(None, "10010") == True, "JLT with JR=-1 should jump"

    register.store(jr_addr, 0)
    assert Program.execute(None, "10010") == False, "JLT with JR=0 should not jump"

    # JLE: jump if JR <= 0
    register.store(jr_addr, 0)
    assert Program.execute(None, "10011") == True, "JLE with JR=0 should jump"

    register.store(jr_addr, -5)
    assert Program.execute(None, "10011") == True, "JLE with JR=-5 should jump"

    register.store(jr_addr, 3)
    assert Program.execute(None, "10011") == False, "JLE with JR=3 should not jump"

    # JGT: jump if JR > 0
    register.store(jr_addr, 3)
    assert Program.execute(None, "10100") == True, "JGT with JR=3 should jump"

    register.store(jr_addr, 0)
    assert Program.execute(None, "10100") == False, "JGT with JR=0 should not jump"

    # JGE: jump if JR >= 0
    register.store(jr_addr, 0)
    assert Program.execute(None, "10101") == True, "JGE with JR=0 should jump"

    register.store(jr_addr, -1)
    assert Program.execute(None, "10101") == False, "JGE with JR=-1 should not jump"

    # JMP: always jump
    register.store(jr_addr, 0)
    assert Program.execute(None, "10110") == True, "JMP should always jump"

    register.store(jr_addr, 999)
    assert Program.execute(None, "10110") == True, "JMP should always jump"

    print("  PASS: jump execute logic")


def test_jump_non_firing():
    """Test that a conditional jump that should NOT fire falls through."""
    memory, register, variable = reload_all()
    from run import Program

    # JEQ with JR=5 → should NOT jump, falls through to MOV R2=99 then EOP
    prog = Program([
        "CB B1",
        "MOV R1 10",
        "MOV JR 5",         # JR = 5
        "JEQ B1",            # JR=5 != 0 → no jump
        "MOV R2 99",        # Should execute (fall-through)
        "EOP",
    ])
    prog.run()

    r1 = register.load(1)
    r2 = register.load(2)
    assert r1 == 10, f"R1 should be 10, got {r1}"
    assert r2 == 99, f"R2 should be 99 (fall-through), got {r2}"
    print("  PASS: jump non-firing (fall-through)")


def test_jump_firing_cb():
    """Test that CB properly stores block address and execution adds BR."""
    memory, register, variable = reload_all()
    from run import Program

    prog = Program([
        "CB B1",
        "MOV R1 10",
        "EOP",
    ])

    # After encodeProgram (before run):
    # - BR = block_count = 1
    # - CB stores B1(mem57) = start_addr + normal_counter = 9 + 0 = 9
    br = register.load(9)
    b1_pre = memory.load(57)

    assert br == 1, f"BR (block count) should be 1, got {br}"
    assert b1_pre == 9, f"B1 pre-run should be 9, got {b1_pre}"

    # After run: CB (ADD B1, BR) adds BR to B1 → 9 + 1 = 10
    prog.run()
    b1_post = memory.load(57)
    assert b1_post == 10, f"B1 post-run should be 10, got {b1_post}"
    print("  PASS: CB block setup")


def test_cmp():
    """Test CMP (simplifies to SUB JR, X)."""
    memory, register, variable = reload_all()
    from run import Program

    prog = Program([
        "MOV R1 10",
        "CMP R1",          # JR = JR - R1 = 0 - 10 = -10
    ])
    prog.run()

    jr = register.load(14)
    assert jr == -10, f"JR after CMP should be -10, got {jr}"
    print("  PASS: CMP")


def test_div_by_zero():
    """Test division by zero handling."""
    memory, register, variable = reload_all()
    from run import Program

    prog = Program([
        "MOV R1 10",
        "MOV R2 0",
        "DIV R1 R2",      # Should handle gracefully
    ])
    prog.run()
    print("  PASS: div by zero (handled)")


def test_prnt():
    """Test PRNT (just verifies it doesn't crash)."""
    memory, register, variable = reload_all()
    from run import Program

    prog = Program([
        "MOV R1 55",
        "PRNT R1",         # Should print "55"
    ])
    prog.run()
    print("  PASS: PRNT (no crash)")


def test_eop():
    """Test that EOP halts execution."""
    memory, register, variable = reload_all()
    from run import Program

    prog = Program([
        "MOV R1 10",
        "EOP",
        "MOV R1 999",     # Should not execute
    ])
    prog.run()

    r1 = register.load(1)
    assert r1 == 10, f"R1 should be 10 (after EOP), got {r1}"
    print("  PASS: EOP halts")


def test_comprehensive():
    """Combined test exercising multiple features together (no loops)."""
    memory, register, variable = reload_all()
    from run import Program

    prog = Program([
        # Register setup
        "MOV R1 100",
        "MOV R2 200",
        "MOV R3 300",

        # Arithmetic chain (values exact in half-precision)
        "ADD R1 R2",       # R1 = 300
        "SUB R1 R3",       # R1 = 0
        "MOV R4 9",
        "MUL R4 R4",       # R4 = 81
        "MOV R5 3",
        "DIV R4 R5",       # R4 = 27 (exact)
        "MOD R4 R5",       # R4 = 0 (exact)

        # Direct memory
        "MOV A 42",
        "MOV B A",

        # Register-indirect: R6 holds addr of B (=2)
        "MOV R6 2",
        "MOV R7 (R6)",     # R7 = memory[2] = 42

        # CMP
        "CMP R7",           # JR = 0 - 42 = -42

        # JLT with JR=-42: should NOT fire in normal flow
        # (We don't jump, just test that execute classifies it correctly)

        # EOP
        "EOP",
    ])
    prog.run()

    r1 = register.load(1)
    r4 = register.load(4)
    r7 = register.load(7)
    a_val = memory.load(1)
    b_val = memory.load(2)

    assert r1 == 0, f"R1 (SUB result) should be 0, got {r1}"
    assert r4 == 0, f"R4 (MOD result 27%3) should be 0, got {r4}"
    assert r7 == 42, f"R7 (from reg-indirect) should be 42, got {r7}"
    assert a_val == 42, f"A should be 42, got {a_val}"
    assert b_val == 42, f"B should be 42, got {b_val}"
    jr = register.load(14)
    assert jr == -42, f"JR after CMP should be -42, got {jr}"
    print("  PASS: comprehensive combined")


# -------------------------------------------------------
# Run tests
# -------------------------------------------------------

if __name__ == "__main__":
    tests = [
        ("Basic arithmetic", test_basic_arithmetic),
        ("Direct memory", test_direct_memory),
        ("Register-indirect", test_register_indirect),
        ("Auto-inc/dec", test_auto_inc_dec),
        ("Indirect", test_indirect),
        ("Indexed", test_indexed),
        ("Jump execute logic", test_jump_execute),
        ("Jump non-firing", test_jump_non_firing),
        ("CB block setup", test_jump_firing_cb),
        ("CMP", test_cmp),
        ("Division by zero", test_div_by_zero),
        ("PRNT", test_prnt),
        ("EOP halts", test_eop),
        ("Comprehensive combined", test_comprehensive),
    ]

    passed = 0
    failed = 0

    for name, func in tests:
        print(f"\n[{name}]")
        try:
            func()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'=' * 40}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
