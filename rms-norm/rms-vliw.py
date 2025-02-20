#!/usr/bin/env python3
from collections import defaultdict

# -----------------------------
# PART 1. SCHEDULING (Compilation)
# -----------------------------

def get_registers(instr):
    """
    Each instruction is a tuple: (op, dest, src1, src2, size)
    
    For most ops, returns (destination, [source registers]). 
    For STORE instructions the operand to be stored is given in the "dest" field;
    we therefore return (None, [dest]) so that STORE is treated as reading from a register.
    """
    op, dest, src1, src2, size = instr
    if op == "STORE":
        return None, [dest]
    else:
        srcs = [r for r in (src1, src2) if r is not None]
        return dest, srcs

def compute_latency(instr):
    """
    Compute a simple latency based on the operation and the data size.
    For example, a LOAD has a base latency of 3 cycles plus 1 extra cycle per 10 units.
    """
    op, dest, src1, src2, size = instr
    base_latencies = {
        "ADD": 1,
        "SUB": 1,
        "MUL": 2,
        "DIV": 2,
        "MOVE": 3,
        "LOAD": 3,
        "STORE": 3,
    }
    base = base_latencies.get(op, 1)
    extra = size // 10  # extra cycle per 10 units of data
    return base + extra

def schedule_instructions(instructions, bundle_size=2):
    """
    A VLIW scheduler that groups instructions into bundles.
      - It reorders the instructions (when possible) so that any instruction whose operands
        are ready and that does not conflict with others in the same bundle is scheduled now.
      - Intra–bundle conflicts are prevented (e.g. an instruction may not read a register
        that is produced by another instruction in the same bundle).
      - Dependencies are checked using a reg_avail table.
    
    Dependency tracking is fixed: registers that are not "externally provided" are not
    assumed to be available until they are produced in an earlier bundle. (For our DAG,
    external registers are those that appear as LOAD keys, e.g. "input0", "input1", etc.)
    
    Returns a list of bundles, where each bundle is a tuple: (start_cycle, list_of_instructions).
    """
    # === Pre‐process registers: mark which names are "externally" available.
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

# -----------------------------
# PART 2. EXECUTION (Simulation)
# -----------------------------

def execute_instruction(instr, registers, inputs):
    """
    Execute one instruction on the simulated machine.
    The register file (a dict) is updated.
    
    For:
      - LOAD: 'src1' is the key in the inputs dict.
      - STORE: copies the register value to a special "OUTPUT" register.
      - Other ops: arithmetic or MOVE.
    """
    op, dest, src1, src2, size = instr
    if op == "LOAD":
        # For LOAD, src1 is the input key.
        registers[dest] = inputs[src1]
    elif op == "STORE":
        # For STORE, write the value from register (stored in 'dest') to "OUTPUT".
        registers["OUTPUT"] = registers[dest]
    elif op == "ADD":
        registers[dest] = registers[src1] + registers[src2]
    elif op == "SUB":
        registers[dest] = registers[src1] - registers[src2]
    elif op == "MUL":
        registers[dest] = registers[src1] * registers[src2]
    elif op == "MOVE":
        registers[dest] = registers[src1]
    elif op == "DIV":
        registers[dest] = registers[src1] / registers[src2]
    else:
        raise ValueError(f"Unknown operation: {op}")

def run_program(instructions, inputs, bundle_size=2):
    """
    Runs the given computation DAG:
      1. Schedules the instructions into bundles.
      2. Executes each bundle sequentially, updating the registers.
    
    Returns the final output (from the special "OUTPUT" register).
    """
    registers = {}  # our register file
    bundles = schedule_instructions(instructions, bundle_size)

    print("Scheduled Bundles:")
    for cycle, bundle in bundles:
        print(f" Cycle {cycle}:")
        for instr in bundle:
            print("   ", instr, "latency", compute_latency(instr))

    current_cycle = 0
    for cycle, bundle in bundles:
        # Simulate waiting until the bundle's start cycle.
        if current_cycle < cycle:
            current_cycle = cycle
        print(f"\nExecuting bundle at cycle {current_cycle}:")
        for instr in bundle:
            print(" Executing:", instr)
            execute_instruction(instr, registers, inputs)
        # Advance time by the bundle's maximum latency.
        bundle_latency = max(compute_latency(i) for i in bundle)
        current_cycle += bundle_latency

    return registers

def run_bundle(bundles, inputs):
    """
    Alternative runner that assumes the bundles have been computed.
    """
    registers = {}  # our register file
    current_cycle = 0
    for cycle, bundle in bundles:
        if current_cycle < cycle:
            current_cycle = cycle
        print(f"\nExecuting bundle at cycle {current_cycle}:")
        for instr in bundle:
            print(" Executing:", instr)
            execute_instruction(instr, registers, inputs)
        bundle_latency = max(compute_latency(i) for i in bundle)
        current_cycle += bundle_latency

    return registers.get("OUTPUT", None)

# -----------------------------
# PART 3. MAIN: DEFINE THE DAG AND RUN
# -----------------------------

if __name__ == "__main__":
    # Define the computation DAG for the RMS normalization example.
    program = [
        # Load inputs and constants.
        ("LOAD",  "R1", "x0",      None, 16),     # R1 = x0
        ("LOAD",  "R2", "x1",      None, 16),     # R2 = x1
        ("LOAD",  "R3", "x2",      None, 16),     # R3 = x2
        ("LOAD",  "R4", "gamma0",  None, 16),     # R4 = gamma0
        ("LOAD",  "R5", "gamma1",  None, 16),     # R5 = gamma1
        ("LOAD",  "R6", "gamma2",  None, 16),     # R6 = gamma2
        ("LOAD",  "R7", "epsilon", None, 16),     # R7 = epsilon
        ("LOAD",  "R8", "const0",  None, 16),     # R8 = 3.0 (for division)
        ("LOAD",  "R9", "const1",  None, 16),     # R9 = 0.5 (for multiplication)

        # Compute squares.
        ("MUL",   "R10", "R1", "R1", 1),         # R10 = x0 * x0
        ("MUL",   "R11", "R2", "R2", 1),         # R11 = x1 * x1
        ("MUL",   "R12", "R3", "R3", 1),         # R12 = x2 * x2

        # Sum of squares.
        ("ADD",   "R13", "R10", "R11", 1),        # R13 = R10 + R11
        ("ADD",   "R14", "R13", "R12", 1),        # R14 = R13 + R12

        # Compute mean of squares.
        ("DIV",   "R15", "R14", "R8", 1),         # R15 = R14 / 3.0

        # Add epsilon: n = mean_sq + epsilon.
        ("ADD",   "R16", "R15", "R7", 1),         # R16 = R15 + epsilon

        # Begin Newton's method iterations for sqrt(n).
        ("MOVE",  "R17", "R16", None, 0),         # R17 = n   (s0)
        ("DIV",   "R18", "R16", "R17", 1),         # R18 = n / s0
        ("ADD",   "R19", "R17", "R18", 1),         # R19 = s0 + (n / s0)
        ("MUL",   "R20", "R9", "R19", 1),          # R20 = 0.5 * R19  (s1)

        ("DIV",   "R21", "R16", "R20", 1),         # R21 = n / s1
        ("ADD",   "R22", "R20", "R21", 1),         # R22 = s1 + (n / s1)
        ("MUL",   "R23", "R9", "R22", 1),          # R23 = 0.5 * R22  (s2)

        ("DIV",   "R24", "R16", "R23", 1),         # R24 = n / s2
        ("ADD",   "R25", "R23", "R24", 1),         # R25 = s2 + (n / s2)
        ("MUL",   "R26", "R9", "R25", 1),          # R26 = 0.5 * R25  (s3)

        ("DIV",   "R27", "R16", "R26", 1),         # R27 = n / s3
        ("ADD",   "R28", "R26", "R27", 1),         # R28 = s3 + (n / s3)
        ("MUL",   "R29", "R9", "R28", 1),          # R29 = 0.5 * R28  (s4)

        ("DIV",   "R30", "R16", "R29", 1),         # R30 = n / s4
        ("ADD",   "R31", "R29", "R30", 1),         # R31 = s4 + (n / s4)
        ("MUL",   "R32", "R9", "R31", 1),          # R32 = 0.5 * R31  (s5)

        ("MOVE",  "R33", "R32", None, 0),          # R33 = s5, which is the approximated sqrt(n) = rms

        # Normalize each element.
        ("DIV",   "R34", "R1", "R33", 1),         # R34 = x0 / rms
        ("MUL",   "R35", "R34", "R4", 1),         # R35 = (x0 / rms) * gamma0  (norm0)

        ("DIV",   "R36", "R2", "R33", 1),         # R36 = x1 / rms
        ("MUL",   "R37", "R36", "R5", 1),         # R37 = (x1 / rms) * gamma1  (norm1)

        ("DIV",   "R38", "R3", "R33", 1),         # R38 = x2 / rms
        ("MUL",   "R39", "R38", "R6", 1),         # R39 = (x2 / rms) * gamma2  (norm2)

        # Store the normalized outputs.
        ("STORE", "R35", "norm0", None, 1),       # Store norm0
        ("STORE", "R37", "norm1", None, 1),       # Store norm1
        ("STORE", "R39", "norm2", None, 1)        # Store norm2
    ]

    # Define the inputs.
    inputs = {
        "x0": 3.0,
        "x1": 4.0,
        "x2": 5.0,
        "gamma0": 0.1,
        "gamma1": 0.2,
        "gamma2": 0.3,
        "epsilon": 1e-6,
        "const0": 3.0,
        "const1": 0.5
    }

    
    print("Bundle size = 2")
    registers = run_program(program, inputs, bundle_size=2)
    outputs = {
        0: registers.get("R35", None),
        1: registers.get("R37", None),
        2: registers.get("R39", None)
    }
    print("\nFinal Outputs:", outputs)

    print("-" * 40)

    print("Bundle size = 50")
    result = run_program(program, inputs, bundle_size=50)
    outputs = {
        0: result.get("R35", None),
        1: result.get("R37", None),
        2: result.get("R39", None)
    }
    print("\nFinal Outputs:", outputs)

