"""
# Correlación entre ETFS

        Información: https://www.cnbc.com/sector-etfs/

1. **XLE - Energy Select Sector SPDR Fund**: Sigue las empresas del sector energético en EE.UU., incluyendo las de petróleo, gas y energías renovables.
2. **XLF - Financial Select Sector SPDR Fund**: Representa a las empresas del sector financiero, como bancos, compañías de inversión y seguros.
3. **XLU - Utilities Select Sector SPDR Fund**: Incluye empresas de servicios públicos, como electricidad y agua.
4. **XLI - Industrial Select Sector SPDR Fund**: Se compone de empresas industriales, incluyendo construcción, fabricación y transporte.
5. **GDX - VanEck Gold Miners ETF**: Incluye compañías mineras de oro a nivel global, proporcionando exposición al sector de la minería de oro.
6. **XLK - Technology Select Sector SPDR Fund**: Agrupa a empresas del sector tecnológico, incluyendo hardware, software y servicios de información.
7. **XLV - Health Care Select Sector SPDR Fund**: Este ETF incluye empresas del sector de la salud, como farmacéuticas y equipos médicos.
8. **XLY - Consumer Discretionary Select Sector SPDR Fund**: Cubre empresas de bienes de consumo discrecional, como minoristas, automóviles y servicios de ocio.
9. **XLP - Consumer Staples Select Sector SPDR Fund**: Invierte en empresas de productos de consumo básico, como alimentos, bebidas y productos domésticos.
10. **XLB - Materials Select Sector SPDR Fund**: Contiene empresas del sector de materiales, que incluye químicos, construcción y empaques.
11. **XOP - Spdr S&P Oil & Gas Exploration & Production ETF**: Se enfoca en compañías de exploración y producción de petróleo y gas.
12. **IYR - iShares U.S. Real Estate ETF**: Proporciona exposición a propiedades y bienes raíces de EE.UU., incluyendo REITs.
13. **XHB - Spdr S&P Homebuilders ETF**: Incluye empresas relacionadas con la construcción de viviendas, desde constructores hasta proveedores de materiales.
14. **ITB - iShares U.S. Home Construction ETF**: Similar al XHB, este ETF se enfoca en constructores de viviendas y proveedores.
15. **VNQ - Vanguard Real Estate Index Fund ETF Shares**: Ofrece exposición al sector inmobiliario y a REITs, similar al IYR.
16. **GDXJ - VanEck Junior Gold Miners ETF**: Agrupa a pequeñas y medianas empresas de minería de oro y metales preciosos.
17. **IYE - iShares U.S. Energy ETF**: Sigue a empresas del sector energético en EE.UU., parecido al XLE pero con posiblemente una composición ligeramente diferente.
18. **OIH - VanEck Oil Services ETF**: Se centra en empresas que proporcionan servicios y equipos para la industria petrolera.
19. **XME - SPDR S&P Metals & Mining ETF**: Incluye compañías involucradas en la extracción y procesamiento de metales y minerales.
20. **XRT - Spdr S&P Retail Etf**: Se enfoca en el sector minorista, incluyendo tiendas de diferentes tipos y tamaños.
21. **SMH - VanEck Semiconductor ETF**: Proporciona exposición a la industria de semiconductores, incluyendo fabricantes y diseñadores de chips.
22. **IBB - iShares Biotechnology ETF**: Incluye empresas biotecnológicas y farmacéuticas enfocadas en el desarrollo de medicamentos y terapias.
23. **KBE - SPDR S&P Bank ETF**: Se compone de bancos de diferentes tamaños, desde multinacionales hasta bancos regionales.
24. **KRE - SPDR S&P Regional Banking ETF**: Similar al KBE pero enfocado en bancos regionales y pequeños de EE.UU.
25. **XTL - SPDR S&P Telecom ETF**: XTL - SPDR S&P Telecom ETF: Este ETF se centra en el sector de las telecomunicaciones, incluyendo empresas que proporcionan servicios de telecomunicaciones, como telefonía móvil, fija, internet y televisión por cable.

**Importancia de la Correlación en Inversiones:**
La correlación es una medida estadística que indica cómo se mueven juntas dos variables. El coeficiente de correlación, \( r \), se calcula con la siguiente fórmula:

"""

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

etfs = [
    'XLE', 'XLF', 'XLU', 'XLI', 'GDX', 'XLK', 'XLV', 'XLY', 'XLP', 'XLB',
    'XOP', 'IYR', 'XHB', 'ITB', 'VNQ', 'GDXJ', 'IYE', 'OIH', 'XME', 'XRT',
    'SMH', 'IBB', 'KBE', 'KRE', 'XTL'
]

start_date = '2010-01-01'
end_date = '2026-03-31'


data = yf.download(etfs, start=start_date, end=end_date)['Close']


returns = data.pct_change().dropna()  #NAN #Null


correlation_returns = returns.corr()

#Prepararnos para graficar

plt.figure(figsize=(14, 12))


sns.heatmap(correlation_returns, annot=True, fmt=".2f", cmap='coolwarm')


plt.title('Correlación de los retornos diarios de los ETFs seleccionados desde 2010')


plt.xticks(rotation=45)
plt.yticks(rotation=45)


plt.tight_layout()
plt.show()
