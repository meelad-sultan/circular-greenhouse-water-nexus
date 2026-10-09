# Method

## Loop and tank (hourly, per contaminant i; masses in ug, concentrations in ug/L, volumes in m3)
```
ET(t)      crop transpiration (radiation term + VPD term, scaled by canopy development)
Qb         bleed = min(bleed_ratio * ET, treatment capacity)
Qmu        make-up demand = ET + Qb
from_tank  = min(Qmu, tank volume);  freshwater = Qmu - from_tank
M_L(t+1)   = M_L + from_tank * 1000 * C_T - (Qb * 1000 + ET * 1000 * uptake_i) * C_L          (loop; volume fixed)
treatment inflow = source intake Qs (pre-filtered) + bleed Qb * C_L
M_T(t+1)   = M_T + treated mass - from_tank * 1000 * C_T - overflow mass                       (tank, well mixed)
```
Concentration in the loop rises because transpired water leaves without contaminants, so the steady-state
concentration factor is about 1 + 1/bleed_ratio relative to the make-up water.

## Safety metric
Hazard index `HI = sum_i C_L,i / limit_i`; exposure hours are hours with `HI > 1`.

## Adsorption bed (Thomas-type, affinity-weighted competition)
`f_i = 1 / (1 + exp(K (1 - S_i)))`, `S_i = L / a_i`, `L = sum_j a_j fed_j / cap`.
For one species `S = fed / cap`, which equals the Thomas model for constant flow and feed
(`K = kTh q0 m / Q`). Capacity units are micromoles for metals (feed mass divided by molar mass) and micrograms for
PFAS classes. Effluent mass = feed mass x f; adsorbed mass = feed mass x (1 - f), so mass is conserved by construction.
The multi-species rule is a stylised heuristic, not a mechanistic isotherm.

## Sediment pre-filter
Acts on the source stream: removes a fraction of suspended solids and the particle-bound fraction of each metal in
proportion; backwash after a solids capacity is reached (energy only).

## Sensing and policies
- Online metal sensors on bed effluent: signed readings with noise sd = sd_frac x limit; one-sided CUSUM per metal
  (`S = max(0, S + y/(limit sd_frac) - k)`, alarm when S > h); alarm replaces the bed.
- PFAS: no online sensor assumed; lab samples at a fixed interval with delay and multiplicative noise; replace when
  the result exceeds a fraction of the limit.
- Fixed schedule: replace all beds every N days. None: never replace.
- Intake guard: block the source intake for a hold time when the source hazard-index reading exceeds a ratio of
  its running baseline.

## Mass balance
Source mass in = pre-filter removal + adsorbed on beds + overflow + crop uptake + final storage (tank + loop).
Reported as `mass_balance_rel_err`; tests require < 1e-9 (observed about 1e-15).

## CUSUM theory used for checking
Siegmund approximations: `ARL0 = (exp(2kb) - 2kb - 1) / (2k^2)`, `b = h + 1.166`; shifted mean:
`ARL1 = (exp(-2 D b) + 2 D b - 1) / (2 D^2)`, `D = delta - k`.
