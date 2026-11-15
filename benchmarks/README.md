# Nexus benchmarks

Measured numbers for accuracy and performance changes. Every accuracy or performance PR quotes a
before and after run of the relevant script. Nothing here calls a paid model: the providers are the
showcase's deterministic squad and `MockProvider`.

Both scripts execute generated code (pytest, uvicorn) in subprocesses on this machine. Run them from
an environment where this checkout is installed (`pip install -e ".[dev]"`), so the generated apps
import this version of `nexus`.

| Script | Question it answers |
| :--- | :--- |
| `bench_generation.py` | For a fixed set of 8 ideas: does each generated app compile, start (`/health` 200 under uvicorn) and pass its own tests end to end? Time per stage, prompt and output size per stage, test run time, healing cycles. |
| `bench_output_defects.py` | Does the pipeline absorb realistic model output defects (markdown fences, prose, double escaping, BOM, CRLF, wrong import roots, missing imports)? One defect injected into otherwise passing output, self healing off. |

```bash
python benchmarks/bench_generation.py                 # deterministic and mock, 8 ideas
python benchmarks/bench_output_defects.py --ideas 3   # 12 defect types plus a clean control
```

The idea list in `bench_generation.py` is fixed; append new ideas at the end so earlier numbers stay
comparable.

## Results log

| Date | Commit | Benchmark | Result |
| :--- | :--- | :--- | :--- |
| 2026-11-15 | ea8afc2 (0.3.3) | defects | 4/12 defect types absorbed, 12/36 cases pass |
| 2026-11-15 | ea8afc2 (0.3.3) | generation, deterministic | 8/8 end to end; median 4.6 s per run, of which 4.5 s are 2 pytest runs |
| 2026-11-15 | ea8afc2 (0.3.3) | generation, mock | 0/8 end to end (placeholder output) |
| 2026-11-15 | 0.3.4 (code normalizer) | defects | 12/12 defect types absorbed, 36/36 cases pass |
| 2026-11-15 | 0.3.4 (code normalizer) | generation, deterministic | 8/8 end to end; median 4.6 s (unchanged) |
