"""Reproduce the equal-cell sensitivity and the two panels of Figure 3 after technical.py."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

out = Path(__file__).resolve().parent
pairs = pd.read_csv(out / 'pairs.csv')
cycles = pd.read_csv(out / 'fastsim.csv').iloc[-1]
charging = pd.read_parquet(out.parent / 'inputs/p14_charging_conversion.parquet')
efficiency = charging.loc[charging.scenario_id == 'central_efficiency', 'charging_efficiency_fraction'].item()
id3 = pd.read_csv(out / 'id3_boundary.csv').query('loss_multiplier == 1').iloc[0]
energy = {'FASTSim': cycles.fresh_battery_side_kwh_per_km, 'ID.3': id3.stored_Wh_km / 1000,
          'ATB': 0.270072194 / 1.609344 * efficiency}
available = 77.413145 * 0.90 * pairs.q
extra = cycles.fresh_storage_loss_kwh_per_km * (pairs.r10_rel - 1).clip(lower=0)
rows = []
for name, base in energy.items():
    for distance in [201.1744, 400]:
        for label, rate in [('Capacity', base), ('Joint', base + extra)]:
            fails = available / rate < distance
            per_cell = fails.groupby(pairs.cell_key).mean()
            rows.append(dict(reference=name, km=distance, model=label, failed_checks=fails.sum(),
                             checks=len(pairs), cells=len(per_cell), check_share=fails.mean(),
                             cell_share=per_cell.mean()))
pd.DataFrame(rows).to_csv(out / 'cell_weighting.csv', index=False)

cases = pd.read_csv(out / 'circular.csv')
roots = pd.read_csv(out / 'storage_thresholds.csv')
case = roots.query("grid == 'MidCase' and roots == 1").iloc[0]
fig, (left, right) = plt.subplots(1, 2, figsize=(7.5, 3.4), layout='constrained')
for year, offset, color, marker in [(2025, -.09, '#146b76', 'o'), (2035, .09, '#a14f21', 's')]:
    limits = cases.loc[cases.year == year].groupby('delay').immediate_minus_delay.agg(['min','max'])
    x = limits.index + offset
    left.vlines(x, limits['min'], limits['max'], color=color, lw=2.5)
    left.scatter(x, limits['min'], marker=marker, color=color, label=str(year))
    left.scatter(x, limits['max'], marker=marker, color=color)
left.set(title='A   Range across scenarios', xticks=[1,3,5], xlabel='Deferral (years)',
         ylabel='Immediate minus deferred (kg CO₂e)')
left.legend(frameon=False, fontsize=9)
right.plot([99, case.first_root * 100, 100], [case.delta_at_099, 0, case.delta_at_100],
           '-o', color='#146b76', markersize=5)
right.annotate('99.37%', (case.first_root * 100, 0), xytext=(5,9),textcoords='offset points')
right.annotate('+0.73', (99,case.delta_at_099), xytext=(4,5),textcoords='offset points')
right.annotate('−1.26', (100,case.delta_at_100), xytext=(-34,6),textcoords='offset points')
right.set(title='B   2035 MidCase, one year', xlabel='Potential storage displacement (%)',
          xticks=[99,99.5,100], ylim=(-1.5,1.1), ylabel='Immediate minus deferred (kg CO₂e)')
for axis in (left, right):
    axis.axhline(0, color='#555555', lw=.8, zorder=0)
    axis.spines[['right','top']].set_visible(False)
fig.savefig(out / 'figure3.png', dpi=240)
