#### E1: one simulated year, scenario S3 (single seed)

| policy | hours HI>1 | max HI | replacements | cost (EUR) | reuse fraction |
|---|---|---|---|---|---|
| none | 4911 | 12.82 | 0 | 204 | 1.000 |
| sensor + guard | 0 | 0.09 | 7 | 1126 | 1.000 |

#### E2: bleed trade-off (mean over replicates; scenario S3, sensor + guard)

| bleed ratio | conc. factor 1+1/b | hours HI>1 | max HI | reuse fraction | freshwater m3 | replacements | cost EUR |
|---|---|---|---|---|---|---|---|
| 0.05 | 21.0 | 0.0 | 0.12 | 1.0 | 0.0 | 6.3 | 992.0 |
| 0.1 | 11.0 | 0.0 | 0.1 | 1.0 | 0.0 | 6.2 | 987.0 |
| 0.15 | 7.7 | 0.0 | 0.08 | 1.0 | 0.0 | 6.2 | 994.0 |
| 0.25 | 5.0 | 0.0 | 0.07 | 1.0 | 0.0 | 6.2 | 1010.0 |
| 0.4 | 3.5 | 0.0 | 0.06 | 1.0 | 0.0 | 6.2 | 1033.0 |
| 0.6 | 2.7 | 0.0 | 0.05 | 1.0 | 0.0 | 6.2 | 1063.0 |
| 0.8 | 2.2 | 0.0 | 0.05 | 1.0 | 0.0 | 6.2 | 1094.0 |

#### E3: replacement and guard policies (median [IQR] over replicates, identical weather/events per replicate)

| scenario | policy | hours HI>1 | max HI | replacements | premature | cost EUR |
|---|---|---|---|---|---|---|
| S2 | none | 0 [0, 0] | 0.00 [0.00, 0.00] | 0 [0, 0] | 0 [0, 0] | 194 [190, 198] |
| S2 | fixed 90 d | 0 [0, 0] | 0.00 [0.00, 0.00] | 12 [12, 12] | 12 [12, 12] | 1740 [1736, 1744] |
| S2 | fixed 270 d | 0 [0, 0] | 0.00 [0.00, 0.00] | 3 [3, 3] | 3 [3, 3] | 581 [576, 584] |
| S2 | sensor | 0 [0, 0] | 0.00 [0.00, 0.00] | 1 [1, 2] | 1 [0, 2] | 327 [312, 444] |
| S2 | none + guard | 0 [0, 0] | 0.00 [0.00, 0.00] | 0 [0, 0] | 0 [0, 0] | 194 [190, 198] |
| S2 | sensor + guard | 0 [0, 0] | 0.00 [0.00, 0.00] | 1 [1, 2] | 1 [1, 2] | 327 [312, 444] |
| S3 | none | 4912 [4868, 4949] | 11.80 [11.26, 12.25] | 0 [0, 0] | 0 [0, 0] | 196 [191, 199] |
| S3 | fixed 90 d | 781 [173, 1493] | 1.22 [0.84, 1.50] | 12 [12, 12] | 7 [7, 8] | 1742 [1737, 1745] |
| S3 | fixed 270 d | 4912 [4868, 4949] | 9.12 [8.42, 9.66] | 3 [3, 3] | 1 [1, 1] | 582 [578, 586] |
| S3 | sensor | 0 [0, 0] | 0.07 [0.06, 0.08] | 6 [6, 7] | 1 [0, 1] | 988 [981, 1075] |
| S3 | none + guard | 4912 [4868, 4949] | 11.80 [11.26, 12.25] | 0 [0, 0] | 0 [0, 0] | 196 [191, 199] |
| S3 | sensor + guard | 0 [0, 0] | 0.07 [0.06, 0.08] | 6 [6, 7] | 1 [0, 1] | 988 [981, 1075] |
| S4 | none | 5279 [5231, 5311] | 13.17 [12.91, 13.33] | 0 [0, 0] | 0 [0, 0] | 194 [190, 198] |
| S4 | fixed 90 d | 3454 [2876, 3722] | 2.83 [2.37, 3.15] | 12 [12, 12] | 10 [10, 10] | 1740 [1736, 1744] |
| S4 | fixed 270 d | 5279 [5231, 5311] | 11.88 [11.51, 12.13] | 3 [3, 3] | 2 [2, 2] | 581 [576, 584] |
| S4 | sensor | 528 [401, 599] | 1.41 [1.35, 1.72] | 4 [3, 5] | 1 [1, 2] | 695 [606, 790] |
| S4 | none + guard | 5279 [5231, 5311] | 13.17 [12.91, 13.33] | 0 [0, 0] | 0 [0, 0] | 194 [190, 198] |
| S4 | sensor + guard | 528 [401, 599] | 1.41 [1.35, 1.72] | 4 [3, 5] | 1 [1, 2] | 695 [606, 790] |

Paired comparison:
- S2: sensor + guard vs fixed 90 d: exposure lower or equal in 100% of replicates, cost lower in 100%, median cost difference -1415 EUR
- S3: sensor + guard vs fixed 90 d: exposure lower or equal in 100% of replicates, cost lower in 100%, median cost difference -760 EUR
- S4: sensor + guard vs fixed 90 d: exposure lower or equal in 100% of replicates, cost lower in 100%, median cost difference -1046 EUR

#### E4: CUSUM operating characteristics (k = 0.5; hours, standardised iid normal data)

| h | sim in-control ARL0 | sim shift 1sd | sim shift 2sd | sim shift 3sd | sim shift 4sd | ARL0 Siegmund approx. | in-control runs censored |
|---|---|---|---|---|---|---|---|
| 3 | 117.4 | 6.4 | 2.7 | 1.8 | 1.3 | 119.0 | 0.0 |
| 4 | 325.2 | 8.3 | 3.3 | 2.2 | 1.7 | 338.0 | 0.0 |
| 5 | 892.8 | 10.3 | 4.0 | 2.6 | 2.0 | 938.0 | 0.0 |
| 6 | 2379.0 | 12.3 | 4.7 | 3.0 | 2.2 | 2573.0 | 0.01 |
| 7 | censored | 14.2 | 5.3 | 3.4 | 2.5 | 7020.0 | 0.19 |
| 8 | censored | 16.2 | 6.0 | 3.8 | 2.8 | 19112.0 | 0.51 |
| 9 | censored | 18.2 | 6.7 | 4.2 | 3.1 | 51985.0 | 0.79 |
| 10 | censored | 20.2 | 7.3 | 4.6 | 3.4 | 141347.0 | 0.92 |

#### E5: Sobol sensitivity (S1 = first-order, ST = total effect; +/- 95% bootstrap CI)

| output | parameter | S1 | ST |
|---|---|---|---|
| max_hi | source_scale | 0.19 +/- 0.21 | 0.98 +/- 0.88 |
| max_hi | sensor_sd_frac | 0.08 +/- 0.28 | 0.35 +/- 0.42 |
| max_hi | cation_mass_kg | 0.00 +/- 0.29 | 0.15 +/- 0.10 |
| max_hi | cation_q_tot | 0.05 +/- 0.24 | 0.14 +/- 0.06 |
| cost_eur | source_scale | 0.44 +/- 0.29 | 0.72 +/- 0.58 |
| cost_eur | cation_q_tot | 0.18 +/- 0.24 | 0.21 +/- 0.08 |
| cost_eur | arsenic_q_tot | 0.09 +/- 0.21 | 0.13 +/- 0.09 |
| cost_eur | cation_mass_kg | 0.07 +/- 0.13 | 0.09 +/- 0.15 |

#### E6: PFAS robustness (EXPLORATORY; scenario S4, wide parameter ranges)

- Parameter draws: 24 (Latin hypercube over PFAS capacity, affinity ratio, lab interval, lab delay)
- Sensor-based (lab-sampling) policy has exposure <= fixed 90 d in 50% of draws and <= no replacement in 100%
- Median hours with HI > 1: none 1817, fixed 90 d 0, sensor 642
- Median cost (EUR): none 159, fixed 90 d 932, sensor 415
