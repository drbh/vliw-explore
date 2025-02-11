# VLIW Processor Simulator

This is a tiny repo that explores the concept of Very Long Instruction Word (VLIW) processors.  

specifically, we are interested in the concept of determining the complete dataflow graph of a program and then scheduling the instructions to minimize the number of cycles required to execute the program.

## Bundling Instructions

this repo contains a naive/toy implementation of converting a program (a list of instructions) into a `bundles` of instructions that can be executed in parallel. 

hypothetically bundles would be limited by the hardware constraints however in this example we are limiting the bundle size to a fixed number.

example input

```python
program = [
    ("LOAD", "R1", None, None, 16),     # LOAD R1, size 16 => latency = 3 + (16//10)=4 cycles.
    ("ADD",  "R2", "R1", "R3", 1),      # ADD R2 = R1 + R3, latency = 1 cycle.
    ("MOVE", "R4", "R2", None, 32),     # MOVE R4 from R2, size 32 => latency = 3 + (32//10)=6 cycles.
    ("MUL",  "R5", "R4", "R6", 1),      # MUL R5 = R4 * R6, latency = 2 cycles.
    ("STORE","R5", None, None, 16),     # STORE R5, size 16 => latency = 3 + 1 = 4 cycles.
]
```

running

```bash
uv run bundle.py
# Bundle size = 1
# Cycle 0:
#     ('LOAD', 'R1', None, None, 16) -> latency 4
# Cycle 4:
#     ('ADD', 'R2', 'R1', 'R3', 1) -> latency 1
# Cycle 5:
#     ('MOVE', 'R4', 'R2', None, 32) -> latency 6
# Cycle 11:
#     ('MUL', 'R5', 'R4', 'R6', 1) -> latency 2
# Cycle 13:
#     ('STORE', 'R5', None, None, 16) -> latency 4
# ----------------------------------------
# Bundle size = 2
# Cycle 0:
#     ('LOAD', 'R1', None, None, 16) -> latency 4
#     ('STORE', 'R5', None, None, 16) -> latency 4
# Cycle 4:
#     ('ADD', 'R2', 'R1', 'R3', 1) -> latency 1
# Cycle 5:
#     ('MOVE', 'R4', 'R2', None, 32) -> latency 6
# Cycle 11:
#     ('MUL', 'R5', 'R4', 'R6', 1) -> latency 2
```

## Executing Bundles

in addition to simple bundle generation, we can add a `"implementation"` of each instruction and essentially execute the program on a tiny virtual machine.

example input

```python
program = [
    ("LOAD",  "R1", "input0", None, 16),        # LOAD input0 into R1 (latency ~3+1)
    ("LOAD",  "R2", "input1", None, 16),        # LOAD input1 into R2
    ("ADD",   "R3", "R1",     "R2",  1),        # R3 = R1 + R2
    ("LOAD",  "R4", "input2", None, 16),        # LOAD input2 into R4
    ("MUL",   "R5", "R3",     "R4",  1),        # R5 = R3 * R4
    ("STORE", "R5", None,     None,  1)         # STORE R5 to OUTPUT
]
```

running

```bash
uv run execute.py
# Bundle size = 2
# Scheduled Bundles:
#  Cycle 0:
#     ('LOAD', 'R1', 'input0', None, 16) latency 4
#     ('LOAD', 'R2', 'input1', None, 16) latency 4
#  Cycle 4:
#     ('ADD', 'R3', 'R1', 'R2', 1) latency 1
#     ('LOAD', 'R4', 'input2', None, 16) latency 4
#  Cycle 8:
#     ('MUL', 'R5', 'R3', 'R4', 1) latency 2
#  Cycle 10:
#     ('STORE', 'R5', None, None, 1) latency 3

# Executing bundle at cycle 0:
#  Executing: ('LOAD', 'R1', 'input0', None, 16)
#  Executing: ('LOAD', 'R2', 'input1', None, 16)

# Executing bundle at cycle 4:
#  Executing: ('ADD', 'R3', 'R1', 'R2', 1)
#  Executing: ('LOAD', 'R4', 'input2', None, 16)

# Executing bundle at cycle 8:
#  Executing: ('MUL', 'R5', 'R3', 'R4', 1)

# Executing bundle at cycle 10:
#  Executing: ('STORE', 'R5', None, None, 1)

# Final Output: 80
# ----------------------------------------
# Bundle size = 4
# Scheduled Bundles:
#  Cycle 0:
#     ('LOAD', 'R1', 'input0', None, 16) latency 4
#     ('LOAD', 'R2', 'input1', None, 16) latency 4
#     ('LOAD', 'R4', 'input2', None, 16) latency 4
#  Cycle 4:
#     ('ADD', 'R3', 'R1', 'R2', 1) latency 1
#  Cycle 5:
#     ('MUL', 'R5', 'R3', 'R4', 1) latency 2
#  Cycle 7:
#     ('STORE', 'R5', None, None, 1) latency 3

# Executing bundle at cycle 0:
#  Executing: ('LOAD', 'R1', 'input0', None, 16)
#  Executing: ('LOAD', 'R2', 'input1', None, 16)
#  Executing: ('LOAD', 'R4', 'input2', None, 16)

# Executing bundle at cycle 4:
#  Executing: ('ADD', 'R3', 'R1', 'R2', 1)

# Executing bundle at cycle 5:
#  Executing: ('MUL', 'R5', 'R3', 'R4', 1)

# Executing bundle at cycle 7:
#  Executing: ('STORE', 'R5', None, None, 1)

# Final Output: 80
```

### References

- <https://arxiv.org/pdf/1901.10008>
