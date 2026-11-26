# Run 05 training (val only)

Source: `experiments/2026-11-24_run05_train/<variant>/` (`selection.json`, `grid_*/result.json`, `seed*/metrics.csv`, `train_log.txt`, `load_info.txt`). Script `scripts/run05_training_report.py`. Selection metric = total replay planner cost on val (main config), 5-epoch trailing mean, min 10 epochs, patience 25, ≤ 150 epochs; configs ranked by the mean over grid seeds 0, 1, 2; the chosen config retrained with seeds 100–104 (docs/PREREG_run05.md §3).

| variant | configs | chosen config | chosen mean val cost (s, seeds 0–2) | final seeds 100–104: best smoothed val cost (s) | mean ± std | best epochs | params |
|---|---|---|---|---|---|---|---|
| mlp_bce | 8 | `{"hidden": 64, "lr": 0.0003, "layers": 2, "lam": null}` | 2050.9 | 2128, 2228, 2193, 2080, 2342 | 2194.2 ± 100.6 | 5, 4, 7, 4, 5 | 22,337 |
| mlp_survival | 8 | `{"hidden": 64, "lr": 0.0003, "layers": 2, "lam": null}` | 1831.1 | 1716, 2079, 2135, 2014, 2050 | 1998.8 ± 164.3 | 9, 4, 14, 33, 32 | 22,792 |
| gnn_bce | 8 | `{"hidden": 64, "lr": 0.001, "layers": 2, "lam": null}` | 1877.3 | 2020, 1964, 2011, 1976, 1728 | 1939.8 ± 120.7 | 11, 10, 7, 6, 20 | 23,105 |
| gnn_survival | 8 | `{"hidden": 64, "lr": 0.0003, "layers": 3, "lam": null}` | 1712.1 | 1887, 1616, 1778, 1834, 1992 | 1821.4 ± 139.5 | 8, 11, 6, 9, 4 | 32,392 |
| gnn_survival_tail | 16 | `{"hidden": 128, "lr": 0.0003, "layers": 2, "lam": 1.0}` | 1614.6 | 1794, 1700, 1580, 1629, 1637 | 1668.2 ± 82.4 | 5, 6, 8, 7, 45 | 88,072 |
| pn_gnn_survival | 8 | `{"hidden": 64, "lr": 0.0003, "layers": 2, "lam": null}` | 1625.1 | 1693, 1795, 1763, 1648, 1709 | 1721.5 ± 58.2 | 14, 11, 10, 14, 9 | 61,192 |
| asap_retrained | 6 | `{"lr": 0.001, "batch": 16}` | 3115.1 | 3270, 3206, 3234, 3200, 3327 | 3247.5 ± 52.4 | 28, 40, 57, 24, 16 | 1,703,681 |

Every seed is listed; none is dropped.

**Reading the curves.** Train loss keeps falling while val loss and val replay cost bottom out early and then drift up: the models overfit after roughly 5–15 epochs. Val replay cost also jumps by several hundred seconds from epoch to epoch, because a few states where an unsolved (~30 s) query is tried first dominate the total. The 5-epoch trailing mean and the early best epochs are the registered response to this. Because val cost selected each checkpoint, val numbers for trained models are optimistic (see REPORT.md). The registered minimum of 10 epochs is implemented as 'do not stop before epoch 10'; the best checkpoint may come from an earlier epoch (18 of the 35 final checkpoints do; DECISIONS #9).


### Grid: mlp_bce

| hidden | lr | layers | lam | mean val cost (s) | per grid seed | best epochs |
|---|---|---|---|---|---|---|
| 64 | 0.0003 | 2 | None | 2050.9 | 1912, 1963, 2278 | [4, 6, 14] |
| 64 | 0.0003 | 3 | None | 2106.0 | 1924, 2152, 2243 | [4, 5, 5] |
| 128 | 0.0003 | 2 | None | 2179.2 | 2151, 2114, 2272 | [4, 9, 4] |
| 64 | 0.001 | 2 | None | 2222.9 | 2156, 2143, 2370 | [4, 5, 8] |
| 128 | 0.0003 | 3 | None | 2235.2 | 2164, 2243, 2298 | [4, 4, 8] |
| 64 | 0.001 | 3 | None | 2260.0 | 2309, 2154, 2318 | [4, 4, 8] |
| 128 | 0.001 | 2 | None | 2403.3 | 2304, 2336, 2570 | [4, 6, 4] |
| 128 | 0.001 | 3 | None | 2408.9 | 2448, 2336, 2442 | [4, 4, 4] |

![curves](figures/train_curves_mlp_bce.png) (vector: `figures/train_curves_mlp_bce.pdf`)

### Grid: mlp_survival

| hidden | lr | layers | lam | mean val cost (s) | per grid seed | best epochs |
|---|---|---|---|---|---|---|
| 64 | 0.0003 | 2 | None | 1831.1 | 1754, 1765, 1975 | [10, 5, 5] |
| 128 | 0.0003 | 2 | None | 1888.8 | 1844, 1965, 1857 | [7, 4, 11] |
| 64 | 0.0003 | 3 | None | 1906.2 | 1808, 1998, 1912 | [10, 5, 8] |
| 128 | 0.0003 | 3 | None | 1940.2 | 1895, 1981, 1945 | [10, 4, 10] |
| 64 | 0.001 | 2 | None | 1940.6 | 1917, 1963, 1942 | [5, 4, 8] |
| 128 | 0.001 | 2 | None | 2034.6 | 2035, 1915, 2154 | [4, 5, 8] |
| 64 | 0.001 | 3 | None | 2051.3 | 2002, 2022, 2130 | [4, 4, 4] |
| 128 | 0.001 | 3 | None | 2090.3 | 2008, 2046, 2217 | [4, 5, 6] |

![curves](figures/train_curves_mlp_survival.png) (vector: `figures/train_curves_mlp_survival.pdf`)

### Grid: gnn_bce

| hidden | lr | layers | lam | mean val cost (s) | per grid seed | best epochs |
|---|---|---|---|---|---|---|
| 64 | 0.001 | 2 | None | 1877.3 | 1980, 1768, 1884 | [8, 14, 11] |
| 128 | 0.001 | 3 | None | 1894.2 | 1910, 1881, 1891 | [4, 4, 5] |
| 128 | 0.0003 | 3 | None | 1922.2 | 1956, 1925, 1886 | [7, 9, 29] |
| 64 | 0.0003 | 2 | None | 1922.6 | 2163, 1596, 2009 | [9, 14, 15] |
| 128 | 0.001 | 2 | None | 1948.9 | 1996, 2092, 1759 | [4, 5, 7] |
| 64 | 0.001 | 3 | None | 1973.4 | 2086, 1960, 1875 | [5, 9, 23] |
| 128 | 0.0003 | 2 | None | 1985.6 | 2092, 1955, 1910 | [5, 5, 8] |
| 64 | 0.0003 | 3 | None | 2112.2 | 2151, 2016, 2170 | [7, 12, 4] |

![curves](figures/train_curves_gnn_bce.png) (vector: `figures/train_curves_gnn_bce.pdf`)

### Grid: gnn_survival

| hidden | lr | layers | lam | mean val cost (s) | per grid seed | best epochs |
|---|---|---|---|---|---|---|
| 64 | 0.0003 | 3 | None | 1712.1 | 1879, 1506, 1751 | [5, 32, 7] |
| 128 | 0.0003 | 3 | None | 1739.0 | 1769, 1718, 1730 | [4, 12, 8] |
| 64 | 0.001 | 2 | None | 1754.9 | 1749, 1560, 1956 | [18, 40, 22] |
| 128 | 0.0003 | 2 | None | 1775.5 | 1737, 1791, 1798 | [5, 5, 4] |
| 128 | 0.001 | 3 | None | 1786.5 | 1904, 1634, 1821 | [4, 5, 13] |
| 64 | 0.001 | 3 | None | 1787.1 | 1812, 1634, 1916 | [5, 5, 23] |
| 128 | 0.001 | 2 | None | 1827.3 | 1858, 1778, 1846 | [50, 4, 4] |
| 64 | 0.0003 | 2 | None | 1898.9 | 1786, 1922, 1988 | [9, 24, 29] |

![curves](figures/train_curves_gnn_survival.png) (vector: `figures/train_curves_gnn_survival.pdf`)

### Grid: gnn_survival_tail

| hidden | lr | layers | lam | mean val cost (s) | per grid seed | best epochs |
|---|---|---|---|---|---|---|
| 128 | 0.0003 | 2 | 1.0 | 1614.6 | 1674, 1603, 1567 | [5, 16, 11] |
| 64 | 0.0003 | 3 | 1.0 | 1637.3 | 1688, 1479, 1745 | [13, 16, 5] |
| 128 | 0.001 | 2 | 1.0 | 1648.4 | 1477, 1757, 1711 | [6, 12, 7] |
| 128 | 0.0003 | 3 | 1.0 | 1649.2 | 1621, 1803, 1525 | [6, 15, 10] |
| 64 | 0.001 | 3 | 0.1 | 1650.9 | 1687, 1567, 1698 | [4, 7, 17] |
| 64 | 0.001 | 2 | 1.0 | 1662.4 | 1640, 1439, 1908 | [5, 20, 11] |
| 128 | 0.0003 | 2 | 0.1 | 1691.4 | 1703, 1677, 1694 | [6, 12, 4] |
| 128 | 0.0003 | 3 | 0.1 | 1693.3 | 1678, 1688, 1714 | [4, 15, 8] |
| 64 | 0.001 | 3 | 1.0 | 1700.1 | 1672, 1591, 1837 | [5, 16, 13] |
| 128 | 0.001 | 3 | 0.1 | 1720.5 | 1881, 1565, 1715 | [4, 5, 4] |
| 64 | 0.0003 | 3 | 0.1 | 1721.7 | 1842, 1501, 1822 | [5, 13, 4] |
| 64 | 0.0003 | 2 | 1.0 | 1726.2 | 1687, 1497, 1995 | [9, 21, 8] |
| 64 | 0.001 | 2 | 0.1 | 1774.5 | 1684, 1741, 1898 | [5, 12, 10] |
| 128 | 0.001 | 2 | 0.1 | 1777.1 | 1816, 1811, 1705 | [4, 4, 4] |
| 128 | 0.001 | 3 | 1.0 | 1784.7 | 1937, 1647, 1770 | [26, 12, 4] |
| 64 | 0.0003 | 2 | 0.1 | 1876.6 | 1646, 1977, 2007 | [9, 20, 4] |

![curves](figures/train_curves_gnn_survival_tail.png) (vector: `figures/train_curves_gnn_survival_tail.pdf`)

### Grid: pn_gnn_survival

| hidden | lr | layers | lam | mean val cost (s) | per grid seed | best epochs |
|---|---|---|---|---|---|---|
| 64 | 0.0003 | 2 | None | 1625.1 | 1605, 1625, 1646 | [62, 42, 20] |
| 128 | 0.0003 | 2 | None | 1625.8 | 1666, 1573, 1639 | [31, 7, 13] |
| 64 | 0.0003 | 3 | None | 1652.9 | 1687, 1832, 1439 | [9, 4, 30] |
| 64 | 0.001 | 2 | None | 1682.5 | 1895, 1705, 1447 | [4, 7, 16] |
| 128 | 0.001 | 2 | None | 1702.0 | 1707, 1659, 1741 | [4, 6, 15] |
| 128 | 0.0003 | 3 | None | 1763.8 | 1931, 1651, 1709 | [4, 40, 5] |
| 64 | 0.001 | 3 | None | 1771.3 | 1776, 1759, 1778 | [20, 5, 24] |
| 128 | 0.001 | 3 | None | 1794.1 | 1876, 1906, 1601 | [18, 4, 11] |

![curves](figures/train_curves_pn_gnn_survival.png) (vector: `figures/train_curves_pn_gnn_survival.pdf`)

### Grid: asap_retrained

| lr | batch | mean val cost (s) | per grid seed | best epochs |
|---|---|---|---|---|
| 0.001 | 16 | 3115.1 | 3014, 3117, 3215 | [45, 22, 31] |
| 0.001 | 32 | 3236.6 | 3241, 3257, 3212 | [38, 17, 49] |
| 0.0003 | 16 | 3256.6 | 3100, 3214, 3456 | [43, 29, 24] |
| 0.0001 | 16 | 3444.4 | 3454, 3610, 3270 | [42, 34, 33] |
| 0.0003 | 32 | 3497.2 | 3506, 3656, 3330 | [25, 27, 30] |
| 0.0001 | 32 | 3546.7 | 3388, 3709, 3543 | [58, 44, 29] |

![curves](figures/train_curves_asap_retrained.png) (vector: `figures/train_curves_asap_retrained.pdf`)
