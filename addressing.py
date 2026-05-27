# Helper layer for memory/register I/O and all ISA addressing modes.

from storage import memory as mem, register as reg, variable as var
from bin_convert import HalfPrecision, Length


class Access:
    """Convenient bridge to read/write storage by chaining lookups."""

    @staticmethod
    def data(addr, chain):
        """Walk a list of storage layers to resolve a value.

        chain  : sequence of 'var', 'reg', 'mem'
                 Each step uses the previous result as the next key.
        """
        current = addr
        for layer in chain:
            if layer == 'var':
                current = var.load(current)
            elif layer == 'reg':
                current = reg.load(current)
            else:  # 'mem'
                current = mem.load(current)
        return current

    @staticmethod
    def store(kind, address, value):
        """Route a write to the correct storage ('register' or 'memory')."""
        pool = {'register': reg, 'memory': mem}.get(kind)
        if pool is not None:
            pool.store(address, value)


# ---------------------------------------------------------------------------
# Addressing Mode Implementations
# ---------------------------------------------------------------------------

class AddressingMode:
    """One static method per ISA addressing mode."""

    # ==================================================================
    # Second-operand-only modes (rb=1, ib=0)
    # ==================================================================

    @staticmethod
    def immediate(raw):
        """Decode a half-precision binary string to a decimal float.

        raw : str — binary string (will be zero-padded to Length.precision).
        """
        return HalfPrecision.hpbin2dec(raw.zfill(Length.precision))

    @staticmethod
    def based(offset):
        """Based: effective address = BR + offset.

        offset : int (caller decides sign).
        Returns (address, content, 'memory').
        """
        base = Access.data('BR', ['var', 'reg'])
        address = int(base) + offset
        return (address, mem.load(address), 'memory')

    @staticmethod
    def relative(offset):
        """Relative: effective address = PC + offset.

        offset : int (caller decides sign).
        Returns (address, content, 'memory').
        """
        base = Access.data('PC', ['var', 'reg'])
        address = int(base) + offset
        return (address, mem.load(address), 'memory')

    # ==================================================================
    # Dual-operand modes (appear on either operand)
    # ==================================================================

    @staticmethod
    def register(idx):
        """Register: value held in register at *idx*.

        idx : int — register slot number.
        Returns (address, content, 'register').
        """
        return (idx, reg.load(idx), 'register')

    @staticmethod
    def registerIndirect(idx):
        """Register-indirect: register content is a memory address.

        idx : int — register whose value points into memory.
        Returns (address, content, 'memory').
        """
        address = reg.load(idx)
        return (address, mem.load(address), 'memory')

    @staticmethod
    def direct(location):
        """Direct: *location* is used verbatim as a memory address.

        Returns (address, content, 'memory').
        """
        return (location, mem.load(location), 'memory')

    @staticmethod
    def indirect(location):
        """Indirect: memory[*location*] holds the real address.

        Returns (address, content, 'memory').
        """
        target = mem.load(location)
        return (target, mem.load(target), 'memory')

    @staticmethod
    def indexed(offset):
        """Indexed: effective address = XR + offset.

        offset : int — displacement (caller passes sign).
        Returns (address, content, 'memory').
        """
        base = Access.data('XR', ['var', 'reg'])
        address = int(base) + offset
        return (address, mem.load(address), 'memory')

    @staticmethod
    def autoinc(idx):
        """Auto-increment (post): read memory at reg[idx], then reg[idx] += 1.

        Returns (address, content, 'memory').
        """
        address = reg.load(idx)
        content = mem.load(address)
        reg.store(idx, address + 1)
        return (address, content, 'memory')

    @staticmethod
    def autodec(idx):
        """Auto-decrement (pre): reg[idx] -= 1, then read memory at new address.

        Returns (address, content, 'memory').
        """
        updated = reg.load(idx) - 1
        reg.store(idx, updated)
        return (updated, mem.load(updated), 'memory')
