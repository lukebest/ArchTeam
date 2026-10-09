# P-0198/M-5r2 减箱模型（UNSIGNED）

```bash
python3 models/P-0198/M-5r2/width.py
python3 models/P-0198/M-5r2/harness.py --seed 20261009 --trials 3
python3 models/P-0198/M-5r2/test_ss.py
```

全部数字 UNSIGNED，不是 card-claim，不得贴到 T3 / 周报绝对值。
减箱周期探针（N=12，flit=beat，无 RBRG/HBM/3DIO），不是满信封 `tests/soc_sim`。
`k=1` 列标 `FAKE_WIDTH`。KILL 看最坏 k。
