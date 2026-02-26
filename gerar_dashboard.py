import pandas as pd
import json

# ==========================
# Configurações
# ==========================
ANO = 2026

# URL do Google Sheets
url = "https://docs.google.com/spreadsheets/d/1JTq0hJwFfMZY5mDsFy0DuEOcOgXSK_b2WylTybB8bWk/export?format=csv"

# Ler planilha principal
df = pd.read_csv(url)

# Limpeza de valores
df['Valor'] = (
    df['Valor']
    .replace({'R\$': '', '\.': ''}, regex=True)
    .replace({',': '.'}, regex=True)
    .astype(float)
)

# Conversão de datas
df['Data da compra'] = pd.to_datetime(df['Data da compra'], dayfirst=True)
df['Data de pagamento'] = pd.to_datetime(df['Data de pagamento'], dayfirst=True)

# Filtrar pelo ano
df = df[df['Data de pagamento'].dt.year == ANO]

# Criar coluna Mês
df['Mês'] = df['Data de pagamento'].dt.strftime('%m/%Y')

# Preencher colunas de parcelas se existirem
for col in ['Parcela', 'T. Parcelas']:
    if col in df.columns:
        df[col] = df[col].fillna('')

# Lista de meses para o dropdown
meses = sorted(df['Mês'].unique(), key=lambda x: pd.to_datetime(x, format='%m/%Y'))
mes_padrao = meses[-1] if meses else ""
meses = ['Todos'] + meses

# ==========================
# Transformar df em JSON seguro para JS
# ==========================
df_json = json.dumps(df.to_dict(orient="records"), ensure_ascii=False)

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
<style>
body {{ background-color: #f8f9fa; }}
.card-summary {{ margin-bottom: 20px; }}
#grafico, #grafico-mensal {{ margin-top: 30px; }}
</style>
</head>

<body>

<div class="container py-4">
<h2 class="text-center mb-4">Dashboard Financeiro {ANO}</h2>

<div class="row mb-4">
    <div class="col-md-4">
        <select id="mesSelect" class="form-select" onchange="atualizar()">
            {''.join([f'<option value="{m}" {"selected" if m==mes_padrao else ""}>{m}</option>' for m in meses])}
        </select>
    </div>
</div>

<div class="row" id="resumo-cards">
    <!-- Cartões de resumo serão inseridos aqui -->
</div>

<div id="grafico" class="mb-5"></div>
<div id="grafico-mensal"></div>

</div>

<script>
// JSON seguro vindo do Python
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

    // Total de gastos
    let total = dados.reduce((a,b)=>a+Number(b.Valor),0);
    let numTransacoes = dados.length;
    let media = numTransacoes>0 ? total/numTransacoes : 0;

    document.getElementById("resumo-cards").innerHTML = `
        <div class="col-md-4">
            <div class="card text-white bg-primary card-summary">
                <div class="card-body text-center">
                    <h5 class="card-title">Total de Gastos</h5>
                    <p class="card-text fs-4">${{moeda(total)}}</p>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card text-white bg-success card-summary">
                <div class="card-body text-center">
                    <h5 class="card-title">Transações</h5>
                    <p class="card-text fs-4">${{numTransacoes}}</p>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card text-white bg-warning card-summary">
                <div class="card-body text-center">
                    <h5 class="card-title">Média por Transação</h5>
                    <p class="card-text fs-4">${{moeda(media)}}</p>
                </div>
            </div>
        </div>
    `;

    // Categoria gastos (pizza)
    let cat={{}};
    dados.forEach(d=>{
        let c = d.Categoria || 'Sem Categoria';
        cat[c] = (cat[c]||0) + Number(d.Valor);
    }});

    Plotly.newPlot("grafico",
    [{
        labels: Object.keys(cat),
        values: Object.values(cat),
        type:'pie',
        textinfo: 'label+percent',
        hoverinfo: 'label+value'
    }],
    {{margin:{{t:30}}, title: "Gastos por Categoria"}}
    );

    // Gastos por mês (barra) - apenas se "Todos" estiver selecionado
    let mesesGastos = [];
    let valoresMensais = [];
    if(mes==="Todos"){{
        let mapMes = {{}};
        df.forEach(d=>mapMes[d.Mês] = (mapMes[d.Mês]||0)+Number(d.Valor));
        mesesGastos = Object.keys(mapMes).sort((a,b)=>new Date('01/'+a)-new Date('01/'+b));
        valoresMensais = mesesGastos.map(m=>mapMes[m]);
    }}

    Plotly.newPlot("grafico-mensal",
    [{
        x: mesesGastos,
        y: valoresMensais,
        type:'bar',
        marker:{{color:'#0d6efd'}}
    }],
    {{margin:{{t:30}}, title: "Gastos Mensais", yaxis:{{title:'R$'}}}}
    );
}}

atualizar();
</script>
</body>
</html>
"""

with open("index.html","w",encoding="utf-8") as f:
    f.write(html)

print("Dashboard atualizado com sucesso!")
