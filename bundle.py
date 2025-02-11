from collections import defaultdict

def get_registers(instr):
    """
    For an instruction represented as:
      (op, dest, src1, src2, size)
    Return its destination and list of source registers.
    """
    op, dest, src1, src2, size = instr
    srcs = [r for r in (src1, src2) if r is not None]
    return dest, srcs

def compute_latency(instr):
    """
    Returns a simple latency value based on the operation and data size.
    For example, arithmetic ops have low latency while data movement ops (LOAD, MOVE, STORE)
    add extra cost depending on the size of the data.
    """
    op, dest, src1, src2, size = instr
    base_latencies = {
        "ADD": 1,
        "SUB": 1,
        "MUL": 2,
        "MOVE": 3,
        "LOAD": 3,
        "STORE": 3,
    }
    base = base_latencies.get(op, 1)
    # For simplicity, add 1 extra cycle per 10 data units.
    extra = size // 10
    return base + extra


def schedule_instructions(instructions, bundle_size=2):
    """
    A VLIW scheduler that groups instructions into bundles.
      - It reorders the instructions (when possible) so that any instruction whose operands
        are ready and that does not conflict with others in the same bundle is scheduled now.
      - Intra–bundle conflicts are prevented (e.g. an instruction may not read a register
        that is produced by another instruction in the same bundle).
      - Dependencies are checked using a reg_avail table.
    
    Dependency tracking is fixed: registers that are not “externally provided” are not
    assumed to be available until they are produced in an earlier bundle. (For our DAG,
    external registers are those that appear as LOAD keys, e.g. "input0", "input1", etc.)
    
    Returns a list of bundles, where each bundle is a tuple: (start_cycle, list_of_instructions).
    """
    # === Pre‐process registers: mark which names are “externally” available.
    # For instructions other than STORE the first operand is the destination.
    produced = set()
    for instr in instructions:
        op, dest, src1, src2, size = instr
        if op != "STORE":
            produced.add(dest)
    # A register appearing in a source that is not produced by any instruction is external.
    external = set()
    for instr in instructions:
        _, srcs = get_registers(instr)
        for r in srcs:
            if r not in produced:
                external.add(r)
    # For external registers, they are available at cycle 0.
    # For any other register (i.e. one that will be computed), we assume it’s not available until scheduled.
    reg_avail = {r: 0 for r in external}

    # === Main scheduling loop
    unscheduled = instructions[:]  # copy the list of instructions
    bundles = []
    current_cycle = 0

    while unscheduled:
        current_bundle = []
        # Try to add as many ready instructions as possible (up to bundle_size).
        for instr in unscheduled[:]:
            if len(current_bundle) >= bundle_size:
                break
            dest, srcs = get_registers(instr)
            # Check that all source registers are available:
            if any(reg_avail.get(r, float('inf')) > current_cycle for r in srcs):
                continue
            # Check intra–bundle conflicts: an instruction is disallowed if:
            #   - its destination (if any) appears as a source of an instruction already in the bundle,
            #   - an instruction already in the bundle writes to the same register,
            #   - or its destination appears as a source in an already–scheduled instruction.
            conflict = False
            for b in current_bundle:
                b_dest, b_srcs = get_registers(b)
                if (b_dest is not None and b_dest in srcs) or \
                   (dest is not None and dest == b_dest) or \
                   (dest is not None and dest in b_srcs):
                    conflict = True
                    break
            if conflict:
                continue
            # If we get here, this instruction is ready and doesn’t conflict.
            current_bundle.append(instr)
            unscheduled.remove(instr)
        if current_bundle:
            # Update register availability: each instruction that produces a register
            # makes that register available only after its own latency.
            bundle_latency = max(compute_latency(instr) for instr in current_bundle)
            for instr in current_bundle:
                dest, _ = get_registers(instr)
                if dest is not None:
                    reg_avail[dest] = current_cycle + compute_latency(instr)
            bundles.append((current_cycle, current_bundle))
            current_cycle += bundle_latency
        else:
            # If no instruction could be scheduled, wait one cycle.
            current_cycle += 1

    return bundles

# === Example Program ===
# Each instruction is a tuple: (op, dest, src1, src2, size)
program = [
    ("LOAD", "R1", None, None, 16),     # LOAD R1, size 16 => latency = 3 + (16//10)=4 cycles.
    ("ADD",  "R2", "R1", "R3", 1),      # ADD R2 = R1 + R3, latency = 1 cycle.
    ("MOVE", "R4", "R2", None, 32),     # MOVE R4 from R2, size 32 => latency = 3 + (32//10)=6 cycles.
    ("MUL",  "R5", "R4", "R6", 1),      # MUL R5 = R4 * R6, latency = 2 cycles.
    ("STORE","R5", None, None, 16),     # STORE R5, size 16 => latency = 3 + 1 = 4 cycles.
]

print("Bundle size = 1")
bundles = schedule_instructions(program, bundle_size=1)

# Output the scheduled bundles along with their start cycle and computed latencies.
for start, bundle in bundles:
    print(f"Cycle {start}:")
    for instr in bundle:
        print("   ", instr, "-> latency", compute_latency(instr))


print("-" * 40)

print("Bundle size = 2")
bundles = schedule_instructions(program, bundle_size=2)

# Output the scheduled bundles along with their start cycle and computed latencies.
for start, bundle in bundles:
    print(f"Cycle {start}:")
    for instr in bundle:
        print("   ", instr, "-> latency", compute_latency(instr))
