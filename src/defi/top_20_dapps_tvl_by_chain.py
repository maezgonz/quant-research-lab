from . import defi_tools as dft
import matplotlib.pyplot as plt

df = dft.getProtocols()
fig, ax = plt.subplots(figsize=(12,6))

n = 50 # quantity to show
top = df.sort_values('tvl', ascending=False).head(n)

chains = top.groupby('chain').size().index.values.tolist()
for chain in chains:
    filtro = top.loc[top.chain==chain]
    ax.bar(filtro.index, filtro.tvl, label=chain)

ax.set_title(f'Top {n} dApp TVL, groupBy dApp main Chain', fontsize=14)
ax.grid(alpha=0.5)
plt.legend()
plt.xticks(rotation=90)
plt.show()
