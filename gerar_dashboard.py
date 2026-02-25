
import pandas as pd

# ==========================
# 1. LER GOOGLE SHEETS
# ==========================
url = "https://docs.google.com/spreadsheets/d/1JTq0hJwFfMZY5mDsFy0DuEOcOgXSK_b2WylTybB8bWk/export?format=csv"
url2 = "https://docs.google.com/spreadsheets/d/1JTq0hJwFfMZY5mDsFy0DuEOcOgXSK_b2WylTybB8bWk/export?format=csv&gid=918439659"

df = pd.read_csv(url)
df2 = pd.read_csv(url2, header=1)

# ==========================
# TABELAS ESPECÍFICAS
# ==========================
tabela1 = df2.iloc[:, 0:3]
tabela2 = df2.iloc[:, 5:8]
tabela3 = df2.iloc[:, 10:13]
tabela4 = df2.iloc[:, 15:18]

def limpar_tabela(tabela):
    tabela = tabela.copy()
    tabela.columns = ['Data', 'Tipo', 'Valor']
    tabela['Valor'] = (
        tabela['Valor']
        .astype(str)
        .replace({'R\$': '', '\.': ''}, regex=True)
        .replace({',': '.'}, regex=True)
        .astype(float)
    )
    tabela['Data'] = pd.to_datetime(tabela['Data'], dayfirst=True)
    tabela['Mês'] = tabela['Data'].dt.strftime('%m/%Y')
    return tabela

tabela1 = limpar_tabela(tabela1)
tabela2 = limpar_tabela(tabela2)
tabela3 = limpar_tabela(tabela3)
tabela4 = limpar_tabela(tabela4)

# FILTRAR ANO
ANO = 2026
tabela1 = tabela1[tabela1['Data'].dt.year == ANO]
tabela2 = tabela2[tabela2['Data'].dt.year == ANO]
tabela3 = tabela3[tabela3['Data'].dt.year == ANO]
tabela4 = tabela4[tabela4['Data'].dt.year == ANO]

# ==========================
# LIMPEZA DF PRINCIPAL
# ==========================
if 'Ano' in df.columns:
    df = df.drop(columns=['Ano'])

df['Valor'] = (
    df['Valor']
    .replace({'R\$': '', '\.': ''}, regex=True)
    .replace({',': '.'}, regex=True)
    .astype(float)
)

df['Data da compra'] = pd.to_datetime(df['Data da compra'], dayfirst=True)
df['Data de pagamento'] = pd.to_datetime(df['Data de pagamento'], dayfirst=True)

df = df[df['Data de pagamento'].dt.year == ANO]
df['Mês'] = df['Data de pagamento'].dt.strftime('%m/%Y')

df['Data da compra'] = df['Data da compra'].dt.strftime('%d/%m/%Y')
df['Data de pagamento'] = df['Data de pagamento'].dt.strftime('%d/%m/%Y')

for col in ['Parcela', 'T. Parcelas']:
    if col in df.columns:
        df[col] = df[col].fillna('')

meses = sorted(df['Mês'].unique(), key=lambda x: pd.to_datetime(x, format='%m/%Y'))
mes_padrao = meses[-1] if meses else ""
meses = ['Todos'] + meses
df_json = df.to_json(orient="records")

# ==========================
# HTML
# ==========================
html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard Financeiro {ANO}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>

<body class="bg-light">

<div class="container py-4">
<h2 class="text-center mb-4">Dashboard Financeiro {ANO}</h2>

<select id="mesSelect" class="form-select mb-4" onchange="atualizar()">
{''.join([f'<option value="{m}" {"selected" if m==mes_padrao else ""}>{m}</option>' for m in meses])}
</select>

<div id="alerta"></div>
<div id="grafico"></div>

</div>

<script>
let df = {df_json};

function moeda(v){{
    return Number(v).toLocaleString('pt-BR', {{
        style: 'currency',
        currency: 'BRL'
    }});
}}

function atualizar(){{
    let mes = document.getElementById("mesSelect").value;
    let dados = mes==="Todos" ? df : df.filter(d=>d.Mês===mes);

    // total gastos
    let total = dados.reduce((a,b)=>a+Number(b.Valor),0);
    document.getElementById("alerta").innerHTML = `
        <div class="alert alert-primary text-center">
            Total de Gastos: <strong>${{moeda(total)}}</strong>
        </div>
    `;

    // categoria gastos
    let cat={{}};
    dados.forEach(d=>cat[d.Categoria]=(cat[d.Categoria]||0)+Number(d.Valor));

    // plot gráfico
    Plotly.newPlot("grafico",
    [{
        labels: Object.keys(cat),
        values: Object.values(cat),
        type:'pie'
    }],
    {{margin:{{t:30}}}});
}}

atualizar();
</script>
</body>
</html>
"""

with open("index.html","w",encoding="utf-8") as f:
    f.write(html)

print("index.html atualizado com sucesso!")
