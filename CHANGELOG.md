## 1.3.1 (2024-02-06)

### Refactor

- drop BasePrimitiveResult.experiments and BasePrimitiveResult.num_experiments (#63)

## 1.3.0 (2024-02-05)

### Feat

- **folding_amplifier**: add multi-qubit amplifier facade (#61)

### Fix

- **zne_estrategy**: update default amplifier to multi-qubit (#62)
- **extrapolation**: support zero variance inputs (#60)

## 1.2.2 (2023-12-22)

### Fix

- **folding_amplifier**: avoid insertion of unnecessary barriers

### Refactor

- **noise_amplifier**: stop using Circuit and DAG amplifier classes

## 1.2.1 (2023-12-02)

### Fix

- **folding_amplifier**: add missing barriers setting to facades

## 1.2.0 (2023-12-02)

### Feat

- **folding_amplifier**: add setting to control barrier insertion (#52)

## 1.1.0 (2023-05-25)

### Feat

- **extrapolator**: add exponential extrapolators (#44)
- **extrapolator**: add OLS extrapolator interface (#43)
- **extrapolation**: new polynomial extrapolator with std errors (#41)
- **utils**: add normalize_array typing util (#42)
- **utils**: add strategy class decorator (#34)
- **utils**: add classconstant descriptor (#32)
- **unset**: add string representation (#31)
- **unset**: add repr

### Refactor

- discontinue using isint from typing utils module (#40)
- **utils**: remove dict_library module (#39)
- **cls**: update class through type call in zne function

### Perf

- **folding_amplifier**: remove unnecessary barriers in folded circuits (#37)

## 1.0.0 (2022-11-08)

### Fix

- **zne_strategy**: remove caching since mutable (#29)
- **global_folding_amplifier**: add barriers between all gates (#28)

## 1.0.0rc0 (2022-11-04)

### Feat

- **validation**: add quality descriptor (#21)
- **utils**: add unset singleton (#22)

### Refactor

- **zne_strategy**: discontinue frozen dataclass (#20)

## 1.0.0b2 (2022-10-27)

### Feat

- **extrapolation**: add quadratic, cubic, and quartic extrapolators (#18)
- **noise_amplification**: add two-qubit noise amplifier (#19)

## 1.0.0b1 (2022-10-20)

### Feat

- **zne_strategy**: add is_noop check (#15)
- **meta**: allow bypassing ZNE on run (#13)
- **zne_strategy**: add noop constructor (#12)

## 1.0.0b0 (2022-10-17)
