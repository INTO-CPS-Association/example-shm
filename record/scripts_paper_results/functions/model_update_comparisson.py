import numpy as np
import sys
import os
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Times New Roman'

import pickle as pk
with open("initial_model_update_comparisson.pkl", "rb") as f:
    initial_model_update_results = pk.load(f)

freq_error_before,freq_error_after,MAC_1,MAC_2 = initial_model_update_results
print(freq_error_before)
# Bar plot for frequency error comparison
fig, ax1 = plt.subplots(figsize=(8, 6), tight_layout=True)
bar_width = 0.30
index = np.arange(freq_error_before.shape[0])

# Bars
ax1.bar(index, freq_error_before, bar_width, label='Before update', color='tab:red')
ax1.bar(index + bar_width, freq_error_after, bar_width, label='After update', color='tab:blue')

# Axes settings
ax1.tick_params(axis='both', labelsize=17, labelcolor='black')
ax1.set_ylabel('Eigenfrequency discrepancy [%]', fontsize=20)
ax1.set_xticks(index + bar_width / 2)
ax1.set_xticklabels([f'Mode {i+1}' for i in index], fontsize=20)
ax1.set_ylim(0, 25)

# Grids
ax1.grid(which='major', linestyle='-', linewidth=0.75, color='gray', alpha=0.5)
ax1.minorticks_on()
ax1.grid(which='minor', linestyle=':', linewidth=0.5, color='gray', alpha=0.3)

# Legend
ax1.legend(fontsize=20, loc='upper right', ncol=2)

# Layout
fig.tight_layout()
plt.show()

# Bar plot for MAC comparison
fig, ax2 = plt.subplots(figsize=(8, 6), tight_layout=True)

ax2.bar(index, MAC_1, bar_width, label='Before update', color='tab:red')
ax2.bar(index + bar_width, MAC_2, bar_width, label='After update', color='tab:blue')
ax2.tick_params(axis='both', labelsize=17, labelcolor='black')
# ax2.set_xlabel('Mode', fontsize=20)
ax2.set_ylabel('MAC', fontsize=20)
# ax2.set_title('MAC Values Comparison')
ax2.set_xticks(index + bar_width / 2)
ax2.set_xticklabels([f'Mode {i+1}' for i in index], fontsize=20)
ax2.set_ylim(0, 1.2)
ax2.legend(fontsize=20, loc='upper center', bbox_to_anchor=(0.5, 1.0), ncol=2)
# Grids
ax2.grid(which='major', linestyle='-', linewidth=0.75, color='gray', alpha=0.5)
ax2.minorticks_on()
ax2.grid(which='minor', linestyle=':', linewidth=0.5, color='gray', alpha=0.3)

fig.tight_layout()
plt.show()