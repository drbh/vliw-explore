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

    return registers.get("OUTPUT", None)

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
    # Define a simple computation DAG.
    # This DAG computes: output = (input0 + input1) * input2
    program = [
        ("LOAD",  "R1", "input0", None, 16),        # LOAD input0 into R1 (latency ~3+1)
        ("LOAD",  "R2", "input1", None, 16),        # LOAD input1 into R2
        ("ADD",   "R3", "R1",     "R2",  1),        # R3 = R1 + R2
        ("LOAD",  "R4", "input2", None, 16),        # LOAD input2 into R4
        ("MUL",   "R5", "R3",     "R4",  1),        # R5 = R3 * R4
        ("STORE", "R5", None,     None,  1)         # STORE R5 to OUTPUT
    ]
    
    # Define inputs for the DAG.
    # For example, (3 + 5) * 10 = 80.
    inputs = {
        "input0": 3,
        "input1": 5,
        "input2": 10,
    }

    
    print("Bundle size = 2")
    result = run_program(program, inputs, bundle_size=2)
    print("\nFinal Output:", result)

    print("-" * 40)

    print("Bundle size = 4")
    result = run_program(program, inputs, bundle_size=4)
    print("\nFinal Output:", result)

