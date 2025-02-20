# rms-norm - vliw'ed

see the `torch` expected output that we'll use as reference

```bash
uv run rms-norm/rms-torch.py
# tensor([3., 4., 5.])
# tensor([0.0735, 0.1960, 0.3674])
```

next we can rewrite this (with a fixed size of 3 elements) to use the native Python

```bash
uv run rms-norm/rms-basic.py
# [3.0, 4.0, 5.0]
# [0.07348467575632431, 0.19595913535019815, 0.3674233787816215]
```

and finally we can convert the more simple math into a even more simple computation DAG by unrolling each step into a single instruction

```bash
uv run rms-norm/rms-vliw.py
# ...
# Final Outputs: {0: 0.07348467357382137, 1: 0.1959591295301903, 2: 0.36742336786910673}
```

> [!NOTE]
>
> - the output of the vliw example is verbose and shows the intermediate steps, but the final outputs are very close to the expected values
> - the vlim is executed twice, one with bundles size 2, which requires 46 cycles and again with bundle size 50 which requires 39 cycles
> - realted to the previous note, the sqrt operation requires sequential execution and results in many bundles with a single instruction (memory bound)
