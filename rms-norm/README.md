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
# Total cycles: 71
# Final Outputs: {0: 0.07348467357382137, 1: 0.1959591295301903, 2: 0.36742336786910673}
# ...
# Total cycles: 49
# Final Outputs: {0: 0.07348467357382137, 1: 0.1959591295301903, 2: 0.36742336786910673}
```

***fast inverse square root*** is a method used in the Quake III Arena game engine to compute the inverse square root of a 32-bit floating-point number.

in this example we use the quake method to reduce the number of cycles required to compute the square root of a number.

```bash
uv run rms-norm/rms-vliw-quake-sqrt.py
# Bundle size = 2
# Total cycles: 61
# Final Outputs: {0: 0.07341910757069907, 1: 0.19578428685519753, 2: 0.3670955378534953}
# ----------------------------------------
# Bundle size = 50
# Total cycles: 35
# Final Outputs: {0: 0.07341910757069907, 1: 0.19578428685519753, 2: 0.3670955378534953}
```

*This is actually a strangely accurate approximation method, but does require more operations to be added to the computation DAG. These ops are `FTOI`, `ITOF`, `SHR` and are Float to Integer, Integer to Float and Shift Right respectively.

> [!NOTE]
>
> - the output of the vliw example is verbose and shows the intermediate steps, but the final outputs are very close to the expected values
> - the vlim is executed twice, one with bundles size 2, which requires 46 cycles and again with bundle size 50 which requires 39 cycles
> - realted to the previous note, the sqrt operation requires sequential execution and results in many bundles with a single instruction (memory bound)
