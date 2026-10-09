# P-0198/M-5r2 减箱模型（UNSIGNED）

```bash
python3 models/P-0198/M-5r2/width.py
python3 models/P-0198/M-5r2/harness.py --seed 20261009 --trials 3
python3 models/P-0198/M-5r2/test_ss.py
```

全部数字 UNSIGNED，不是 card-claim，不得贴到 T3 / 周报绝对值。
减箱周期探针（N=12，flit=beat，无 RBRG/HBM/3DIO），不是满信封 `tests/soc_sim`。
`k=1` 列标 `FAKE_WIDTH`。KILL 看最坏 k。

SEED=20261009 / 3 trials 的一次打印（UNSIGNED）：最坏 k=18 混合 `T_snp/off=6.889` KILL，`T_dat/off=1.017` r≈1 淘汰；`header-only≡drain-off≡stitch`。不得当 card-claim。
