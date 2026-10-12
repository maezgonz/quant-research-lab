import urllib3
from src.utils import network
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
def getDataV3(variableID):
    url = f"https://api.bcra.gob.ar/estadisticas/v3.0/Monetarias/{variableID}"
    r = network.get_insecure(url, timeout=15)
    return pd.DataFrame(r.json().get('results')).set_index('fecha')

tamar_tea = getDataV3(variableID=45)['valor']/100
tamar_tea.index = pd.to_datetime(tamar_tea.index)
tamar_tea = tamar_tea.sort_index()
tamar_tea = tamar_tea.loc[tamar_tea.index>'2025-01-15']
tamar_tem = ((1+tamar_tea)**(1/12)-1).to_frame().rename(columns={'valor': 'tamar_tem_spot'})
tamar_tem['tamar_tem_avg'] = tamar_tem.expanding().mean()
tamar_tem['TTM26'] = 0.0225
tamar_tem['TTJ26'] = 0.0219
tamar_tem['TTS26'] = 0.0217
tamar_tem['TTD26'] = 0.0214


plt.style.use('dark_background')
plt.rcParams.update({'font.size': 6})

fig, ax = plt.subplots(dpi=200, facecolor='black')


colores = {
    'tamar_tem_spot': 'white',
    'tamar_tem_avg': 'white',
    'TTM26': 'pink',
    'TTJ26': 'yellow',
    'TTS26': 'orange',
    'TTD26': 'gray'
}

for col in tamar_tem.columns:
    y = tamar_tem[col].dropna()
    if not y.empty:
        estilo = ':' if col == 'tamar_tem_spot' else '-'
        ax.plot(y.index, y.values, lw=0.5, color=colores[col], linestyle=estilo, label=col)
        ax.text(y.index[-1], y.iloc[-1], col, fontsize=5, va='center', ha='left', color=colores[col])

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(frameon=False, ncol=3)
ax.grid(alpha=0.1)

ax.set_title("Tasa TAMAR (TEM desde 10 dias habiles pre duales) vs TEM Fija duales")
plt.show()