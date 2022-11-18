# Bibliotecas essênciais
import pandas as pd
import numpy as np

# Ferramentas de API's
import requests
import yfinance as yf

# Ferramenta para redimensionar valores (rescaling)
from mlxtend.preprocessing import minmax_scaling

# Ferramentas de plotagem
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import iplot
from plotly.subplots import make_subplots

#ferramenta para criação do Dashboard
from dash import Dash, html, dcc, Input, Output, State


response = requests.get("https://raw.githubusercontent.com/wcota/covid19br/master/cases-brazil-states.csv")

## Criando o dataframe:
response = response.content.decode("utf-8")
result = [x.split(',') for x in response.split('\n')]
df = pd.DataFrame(result[1:], columns= result[0])

## Substituindo os valores vazios por 0:
df = df.replace("", 0, regex=True)

#  Removendo colunas com valores constantes:
df.drop(["country", "city"], axis=1, inplace=True)
df = df[:-1]

# Transformando a coluna de data para o formato apropriado:
df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")

# Como a maioria das colunas está em um formato numérico, vamos converter elas para float:
for column in df.columns:
    try:
        df[column] = df[column].astype(float)
    except:
        continue

# Separando os dados a nível nacional:
df_total = df[df["state"]=="TOTAL"]

# Criando um sub-dataframe para análise de variações de novos casos:
days = pd.DataFrame({
    "newDeaths": [row for row in df_total["newDeaths"]],
    "newCases" : [row for row in df_total["newCases"]],
    "date"     : [row for row in df_total["date"]],
    "suspects" : [row for row in df_total["suspects"]],
    "vaccinated" : [row for row in df_total["vaccinated"]]
    
})

## agregando os dados por mês e semana
months = days.set_index("date").resample('M').sum()
weeks = days.set_index("date").resample('W').sum()
''' Fazendo essa agregação não podemos trabalhar com colunas de valores agregados. 
Por exemplo, a coluna 'deaths' soma diversas vezes a coluna 'newDeaths', 
e quando ela é agregada ela soma esses valores mais de uma vez!
>>> Isso gera um número absurdo de casos, além de dados errados!
'''
# Reescalando os dados, facilitar a plotagem:
scaled_months = minmax_scaling(months, columns = ["newCases","newDeaths", "suspects","vaccinated"])

#cores nos plots
colors = px.colors.qualitative.swatches()

#primeiro plot - 'Infecções Divulgadas ao Mês'
fig_infec_mes = px.line(months, x=months.index, y="newCases",
               markers= True,
               title='Infecções Divulgadas ao Mês',
               labels = {
                "newCases": "Quantidade",
                "date": "Data"
                },color_discrete_sequence=["royalblue"])
fig_infec_mes.update_layout(font_color='blue',
                title_font_color='red',
                title_font_size = 20,
                title_x = 0.5)

#segundo plot - 'Óbitos Divulgados ao Mês'
fig_mortes_mes = px.line(months, x=months.index, y="newDeaths",
               markers= True,
               title='Óbitos Divulgados ao Mês',
               labels = {
                "deathsMS": "Quantidade",
                "date": "Data"
                },color_discrete_sequence=["red"])
fig_mortes_mes.update_layout(font_color='red',
                title_font_color='orange',
                title_font_size = 20,
                title_x = 0.5)

# terceiro plot - 'Casos Suspeitos Divulgados por Mês'
fig_susp_mes = px.line(months, x=months.index, y="suspects",
                markers= True,
                title='Casos Suspeitos Divulgados por Mês',
                labels  = {
                "newCases": "Quantidade",
                "date": "Data"
                },color_discrete_sequence=["orange"])
fig_susp_mes.update_layout(font_color='orange',
                title_font_color='red',
                title_font_size = 20,
                title_x = 0.5)

# terceiro plot - 'Quantidade de Vacinados por Mês'
fig_vacinados_mes = px.line(months, x=months.index, y="vaccinated",
                markers= True,
                title='Quantidade de Vacinados por Mês',
                labels  = {
                "newCases": "Quantidade",
                "date": "Data"
                },color_discrete_sequence=["green"])
fig_vacinados_mes.update_layout(font_color='green',
                title_font_color='black',
                title_font_size = 20,
                title_x = 0.5)

# quarto plot - novos casos, suspeitas, vacinados e óbitos
fig_infec_susp_vacin_mortes = go.Figure()
fig_infec_susp_vacin_mortes = fig_infec_susp_vacin_mortes.add_trace(go.Scatter(x = months.index, 
                               y = scaled_months["newCases"],
                               mode = 'lines+markers',
                               name = "Infecções",
                               line = dict(color='royalblue',width=2,dash='dot')))
fig_infec_susp_vacin_mortes = fig_infec_susp_vacin_mortes.add_trace(go.Scatter(x = months.index, 
                               y = scaled_months["suspects"],
                               mode = 'lines+markers',
                               name = "Suspeitos",
                               line = dict(color='orange',width=2,dash='dot')))
fig_infec_susp_vacin_mortes = fig_infec_susp_vacin_mortes.add_trace(go.Scatter(x = months.index, 
                               y = scaled_months["vaccinated"],
                               mode = 'lines+markers',
                               name = "Vacinados"))
fig_infec_susp_vacin_mortes = fig_infec_susp_vacin_mortes.add_trace(go.Scatter(x = months.index, 
                               y = scaled_months["newDeaths"],
                               mode = 'lines+markers',
                               name = "Óbitos",
                               line = dict(color='red')
                               ))
fig_infec_susp_vacin_mortes.update_layout(
                                title='Comparando Novos casos, suspeitos, vacinados e Óbitos Mês',
                                title_font_size = 20,
                                title_font_color = 'black',
                                title_x = 0.5)

# Plotando relaçao das infecções e óbitos por covid:
fig_infec_mortes_covid = go.Figure()
fig_infec_mortes_covid = fig_infec_mortes_covid.add_trace(go.Scatter(x = scaled_months.index,
                               y = scaled_months["newCases"], 
                               mode = 'lines+markers',
                               name = "Infecções",
                               line = dict(color='royalblue',width=2,dash='dot')))

#quinto plot - 'Relação das Infecções e Óbitos por Covid'
fig_infec_mortes_covid = fig_infec_mortes_covid.add_trace(go.Bar(x = scaled_months.index,
                           y = scaled_months["newDeaths"], 
                           name = "Óbitos"))

fig_infec_mortes_covid.add_vline(x='2021-01-17',
                line_width=2,
                line_dash="dot")

fig_infec_mortes_covid.add_annotation(x="2021-01-17", y = 1,
            text="Início das Vacinações no Brasil",
            bordercolor="#c7c7c7",
            borderwidth=2,
            borderpad=4,
            bgcolor= "#FFFFFF")

fig_infec_mortes_covid.update_layout(
            title='Relação das Infecções e Óbitos por Covid',
            title_font_size = 20,
            title_font_color = 'black',
            title_x = 0.5)

# Analisando a variação de novos casos divulgados:
days_var = days.set_index("date").pct_change()
weeks_var = weeks.pct_change()
months_var = months.pct_change()

# Criando uma base de dados limpa:
months_cleaned = pd.DataFrame({})

# Identificando os outiliers da base:
outliers = months_var["newCases"].between(months_var["newCases"].quantile(.05),months_var["newCases"].quantile(.9))

# Removendo os outliers da tabela months e adicionando na tabela months_cleaned
months_cleaned["newCases"] = pd.DataFrame(months_var["newCases"].multiply(outliers))

# Fazendo a mesma coisa para a coluna de "newDeaths":
outliers = months_var["newDeaths"].between(months_var["newDeaths"].quantile(.05),months_var["newDeaths"].quantile(.9))
months_cleaned["newDeaths"] = pd.DataFrame(months_var["newDeaths"].multiply(outliers))

# Removendo valores nulos:
for column in months_cleaned.columns:
    months_cleaned[column].replace({0:np.nan}, inplace = True)

#  Removendo os outliers da tabela weekss e adicionando na tabela weeks_cleaned
weeks_cleaned = pd.DataFrame({})

outliers = weeks_var["newCases"].between(weeks_var["newCases"].quantile(.05),weeks_var["newCases"].quantile(.9))
weeks_cleaned["newCases"] = pd.DataFrame(weeks_var["newCases"].multiply(outliers))

outliers = weeks_var["newDeaths"].between(weeks_var["newDeaths"].quantile(.05),weeks_var["newDeaths"].quantile(.9))
weeks_cleaned["newDeaths"] = pd.DataFrame(weeks_var["newDeaths"].multiply(outliers))

for column in weeks_cleaned.columns:
    weeks_cleaned[column].replace({0:np.nan}, inplace = True)

# Criando um dicionário para os Dfs
dfs = {"days" : days_var[2:], "weeks": weeks_var[2:], "months":months_var[2:]}

# sexto plot - 'Variação de Novas Infecções Divulgadas'
fig_var_novas_inf_divul = go.Figure()
fig_var_novas_inf_divul = fig_var_novas_inf_divul.add_trace(go.Scatter(x = dfs["days"].index,
                               y = dfs["days"]["newCases"], 
                               name = "Variação Diária",
                               line = dict(color='orange')))

fig_var_novas_inf_divul = fig_var_novas_inf_divul.add_trace(go.Scatter(x = dfs["weeks"].index,
                               y = dfs["weeks"]["newCases"], 
                               name = "Variação Semanal",
                               line = dict(color='blue')))

fig_var_novas_inf_divul = fig_var_novas_inf_divul.add_trace(go.Scatter(x = dfs["months"].index,
                               y = dfs["months"]["newCases"], 
                               name = "Variação Mensal",
                               line = dict(color='red')))

fig_var_novas_inf_divul.update_layout(
                title='Variação de Novas Infecções Divulgadas',
                title_font_color= 'black',
                title_font_size = 20,
                title_x = 0.5)

# Criando um dicionário para os Dfs
dict_cases = {"days" : days_var[2:], "weeks": weeks_var[2:], "months":months_var[2:]}

# sétimo plot - 'Variação de Novos Óbitos Divulgados'
fig_var_novos_obit_div = go.Figure()
fig_var_novos_obit_div = fig_var_novos_obit_div.add_trace(go.Scatter(x = dict_cases["days"].index,
                               y = dict_cases["days"]["newDeaths"], 
                               name = "Variação Diária",
                               line = dict(color='orange')))

fig_var_novos_obit_div = fig_var_novos_obit_div.add_trace(go.Scatter(x = dict_cases["weeks"].index,
                               y = dict_cases["weeks"]["newDeaths"], 
                               name = "Variação Semanal",
                               line = dict(color='blue')))

fig_var_novos_obit_div = fig_var_novos_obit_div.add_trace(go.Scatter(x = dict_cases["months"].index,
                               y = dict_cases["months"]["newDeaths"], 
                               name = "Variação Mensal",
                               line = dict(color='red')))

fig_var_novos_obit_div.update_layout(
                title='Variação de Novos Óbitos Divulgados',
                title_font_size=20,
                title_font_color='black',
                title_x =0.5)

# Removendo os valores extremos das variações mensais e semanais:
out_dict = {
"Novas Infecções Mensais": months_var["newCases"],
"Novos Óbitos Mensais": months_var["newDeaths"],
"Novas Infecções Semanais": weeks_var["newCases"],
"Novos Óbitos Semanais": weeks_var["newDeaths"]
}

for item in out_dict:
    outliers = out_dict[item].between(out_dict[item].quantile(.05), out_dict[item].quantile(.9))
    outilers = pd.DataFrame(outliers)
    out_dict[item] = out_dict[item].multiply(outliers)

# oitavo plot -  Boxplot dos valores que restaram na base:
fig_boxplot = make_subplots(rows=1, cols=1)

for item in out_dict:
    fig_boxplot.add_trace(go.Box(y=out_dict[item], name = f"{item}"))

fig_boxplot.update_layout(height=600,
                            width=1400,
                            title_text="Box Plot das Variações",
                            title_font_size=20,
                            title_font_color='black',
                            title_x=0.5)

# baixando base de dados ipca
ipca = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.4449/dados?formato=csv")

##### TRATAMENTO DE DADOS
ipca = ipca.content.decode("utf-8")
ipca = [x.split(';') for x in ipca.split('\r\n')]

# Removendo as aspas ("") prensentes em cada item do dataframe:
for row in range(0, len(ipca)):
    for item in range(0, len(ipca[row])):
        ipca[row][item] = ipca[row][item].replace('\"', "")
ipca_df = pd.DataFrame(ipca[1:], columns= ipca[0])

# Removendo a última linha, que possui valores nulos:
ipca_df = ipca_df[:-1] 

# Colocando a data no formato datetime:
ipca_df["data"] = pd.to_datetime(ipca_df["data"], format="%d/%m/%Y")

# Subtraindo um dia da data, de modo a igualar com a data das tabelas do covid:
ipca_df["data"] = ipca_df["data"]-pd.Timedelta(days=1)

# Trocando os pontos por vírgulas:
ipca_df["valor"] = [row.replace(",", ".") for row in ipca_df["valor"]]

# Colocando o valor no formato float:
ipca_df["valor"] = ipca_df["valor"].astype(float)

# Separando um dataframe para analizar o IPCA entre 2020 e os dias atuais:
ipca = ipca_df.loc[ipca_df["data"]>="2020-02-09"]


# Dicionário para o Df:
dict_ipca = {"ipca" : ipca[2:], "covid": months_var[2:]}

# plot the data
fig_ipca_x_covid = go.Figure()
fig_ipca_x_covid = fig_ipca_x_covid.add_trace(go.Scatter(x = dict_ipca["ipca"]["data"],
                               y = dict_ipca["ipca"]["valor"],
                               name = "IPCA no Brasil",
                               line = dict(color='blue')))

fig_ipca_x_covid = fig_ipca_x_covid.add_trace(go.Scatter(x = dict_ipca["covid"].index,
                               y = dict_ipca["covid"]["newCases"], 
                               name = "Número de Infecções",
                               line = dict(color='orange')))

fig_ipca_x_covid = fig_ipca_x_covid.add_trace(go.Scatter(x = dict_ipca["covid"].index,
                               y = dict_ipca["covid"]["newDeaths"], 
                               name = "Número de Óbitos",
                               line = dict(color='red')))

fig_ipca_x_covid.update_layout(
                            title='Variações Mensais: IPCA x Casos de Covid',
                            title_font_size=20,
                            title_font_color='black',
                            title_x=0.5)


# Juntando os dados do covid com os dados do IPCA:
months_ipca = pd.merge_ordered(months_cleaned, ipca["valor"], left_on = months_cleaned.index, right_on = ipca["data"])
months_ipca.rename(columns = {"valor":"ipca"}, inplace=True)

# Reescalando os dados, facilitar a plotagem:
scaled_months_ipca = minmax_scaling(months_ipca.set_index("key_0"), 
                                    columns = ["newCases","newDeaths", "ipca"])

months_heatmap = scaled_months_ipca.dropna().corr().round(decimals=2)
heatmap_dict = {'z': months_heatmap.values.tolist(),
                'x': ["Novas Infecções", "Novos Óbitos", "IPCA"],
                'y': ["Novas Infecções", "Novos Óbitos", "IPCA"]}

# nono plot - Correlações Mensais do IPCA com a Covid
fig_corr_mes_ipca_covid = go.Figure(data=go.Heatmap(heatmap_dict,
                               text = months_heatmap.values.tolist(),
                               type = 'heatmap',
                               colorscale = 'rainbow',
                               texttemplate="%{text}",
                               textfont={"size":18}))
fig_corr_mes_ipca_covid.update_layout(showlegend = False,
                  width = 600, height = 600,
                  autosize = False,
                  title = "Correlações Mensais do IPCA com a Covid",
                  font_size = 16)
fig_corr_mes_ipca_covid.update_yaxes(tickangle = 270, linewidth = 5, tickfont_size =14)
fig_corr_mes_ipca_covid.update_xaxes(linewidth = 5, tickfont_size =14)

# décimo plot - Variações Mensais: IPCA x Casos de Covid
fig_line_covid_ipca = go.Figure()
fig_line_covid_ipca = fig_line_covid_ipca.add_trace(go.Scatter(x = scaled_months_ipca.dropna().index,
                               y =  scaled_months_ipca.dropna()["ipca"], 
                               name = "IPCA no Brasil"))

fig_line_covid_ipca = fig_line_covid_ipca.add_trace(go.Scatter(x = scaled_months_ipca.dropna().index,
                               y = scaled_months_ipca.dropna()["newCases"], 
                               name = "Número de Infecções"))

fig_line_covid_ipca = fig_line_covid_ipca.add_trace(go.Scatter(x = scaled_months_ipca.dropna().index,
                               y = scaled_months_ipca.dropna()["newDeaths"], 
                               name = "Número de Óbitos"))

fig_line_covid_ipca.update_layout(
    title='Variações Mensais: IPCA x Casos de Covid'
)

# Comparação dos Casos de Covid com a Bolsa de Valores e o Dolar
ibov_month = yf.download('^bvsp', start='2020-01-01', end="2022-11-30", interval='1mo')
usd_month = yf.download('USDBRL=X', start='2020-01-01', end="2022-11-30", interval='1mo')

ibov_week = yf.download('^bvsp', start='2020-01-01', end="2022-11-30", interval='1wk')
usd_week = yf.download('USDBRL=X', start='2020-01-01', end="2022-11-30", interval='1wk')

# Obtendo as variações mensais e semanais:
ibov_mvar = ibov_month.pct_change()
usd_mvar = usd_month.pct_change()

ibov_wvar = ibov_week.pct_change()
usd_wvar = usd_week.pct_change()

# Unindo as informações da Bolsa com o Dataframe do IPCA
bolsa_months = scaled_months_ipca
bolsa_months = pd.DataFrame(bolsa_months.reset_index())

bolsa_months["ibov"] = [row for row in ibov_mvar["Close"][2:]]
bolsa_months["usd"] = [row for row in usd_mvar["Close"][2:]]

# Reescalando o dataframe:
scaled_bolsa_months = minmax_scaling(bolsa_months.set_index("key_0"), 
                                    columns = ["newCases","newDeaths", "ipca", "ibov", "usd"])

#decimo segundo plot - Correlações Mensais: IBOV, USD, IPCA e Casos de Covid
fig_corr_m_ibov_usd_ipca = px.imshow(scaled_bolsa_months.dropna().corr().round(decimals=2),
                text_auto=True,
                width = 600, height = 600,
                color_continuous_scale='Portland',
                title = "Correlações Mensais: IBOV, USD, IPCA e Casos de Covid")

#decimo terceiro plot - Variações Mensais: IBOV, USD, IPCA e Casos de Covid
fig_vm_bolsas_covid_covid = go.Figure()
fig_vm_bolsas_covid_covid = fig_vm_bolsas_covid_covid.add_trace(go.Scatter(x = scaled_bolsa_months.dropna().index,
                               y =  scaled_bolsa_months.dropna()["ipca"], 
                               name = "IPCA no Brasil"))

fig_vm_bolsas_covid_covid = fig_vm_bolsas_covid_covid.add_trace(go.Scatter(x = scaled_bolsa_months.dropna().index,
                               y = scaled_bolsa_months.dropna()["newCases"], 
                               name = "Número de Infecções"))

fig_vm_bolsas_covid_covid = fig_vm_bolsas_covid_covid.add_trace(go.Scatter(x = scaled_bolsa_months.dropna().index,
                               y = scaled_bolsa_months.dropna()["newDeaths"], 
                               name = "Número de Óbitos"))

fig_vm_bolsas_covid_covid = fig_vm_bolsas_covid_covid.add_trace(go.Scatter(x = scaled_bolsa_months.dropna().index,
                               y = scaled_bolsa_months.dropna()["ibov"], 
                               name = "Bolsa de Valores"))

fig_vm_bolsas_covid_covid = fig_vm_bolsas_covid_covid.add_trace(go.Scatter(x = scaled_bolsa_months.dropna().index,
                               y = scaled_bolsa_months.dropna()["usd"], 
                               name = "Cotações do Dolar"))

fig_vm_bolsas_covid_covid.update_layout(
    title='Variações Mensais: IBOV, USD, IPCA e Casos de Covid'
)







########### CRIANDO UM DASHBOARD COM DASH

app = Dash(__name__)

app.layout = html.Div(children=[
    html.H2(children='Covid no Brasil com impacto no IPCA (Índice Nacional de Preços ao Consumidor Amplo)',
    style={'textAlign': 'center', 'color':'red' }),
    html.H3("Análise realizada como trabalho em grupo do Cusro - DiversidadeTech - Let's Code by ADA",
    style={'textAlign': 'center'}),
    html.Div(children='Professor - Alex Lima.',
    style={'textAlign': 'center'}),
    html.Div(children='Alunos - Alysson, Gleilson, Nivea, Renato e Tiago.',
    style={'textAlign': 'center'}),
    html.Div(children='----'*20,
    style={'textAlign': 'center'}),
    html.Div(children='No dia 17.11.2019 é confirmado o primeiro caso da CIVID-19 no mundo.',
    style={'textAlign': 'center'}),
    html.Div(children='Estudos do viroloigista Michael Worobey, identifica que se tratava de uma mulher',
    style={'textAlign': 'center'}),
    html.Div(children='vendedora de um mercado de animais, em Wuhan na China.',
    style={'textAlign': 'center'}),
        
#option = ['Infectados Mês', 'Mortes Mês', 'Suspeitos Mês', 'Vacinado Mês', 'Completa Mês']
    dcc.Dropdown(['Infectados Mês', 'Mortes Mês', 'Suspeitos Mês', 'Vacinado Mês', 'Completa Mês'],
                    placeholder="Selecione o Gráfico",
                    searchable=False,
                    value='Completa Mês',
                    id = 'Lista de Gráficos',
                    style = {'textAlign': 'center','margin-left': '25%',
                    'margin-top': '1em', 'width': '50%', 
                    'align-items': 'center'}),
    
    dcc.Graph(
        id='graph_01',
        figure=fig_infec_susp_vacin_mortes
    ),
    dcc.Graph(
        id='graph_02',
        figure=fig_infec_mortes_covid
        
    ),
  
    dcc.Graph(
        id='graph_05',
        figure=fig_boxplot,
        style = {'textAlign': 'center',
                    'margin-top': '1em',
                    'align-items': 'center'}
    ),
    dcc.Graph(
        id='graph_07',
        figure=fig_ipca_x_covid
    ),
    dcc.Graph(
        id='graph_08',
        figure=fig_line_covid_ipca
    ),
    dcc.Graph(
        id='graph_09',
        figure=fig_corr_mes_ipca_covid,
        style = {'textAlign': 'center','margin-left': '25%',
                    'margin-top': '1em', 'width': '50%', 
                    'align-items': 'center'}
    ),
    
    dcc.Graph(
        id='graph_10',
        figure=fig_vm_bolsas_covid_covid
    ),
    dcc.Graph(
        id='graph_11',
        figure=fig_corr_m_ibov_usd_ipca,
        style = {'textAlign': 'center','margin-left': '25%',
                    'margin-top': '1em', 'width': '50%', 
                    'align-items': 'center'}
    )

])

@app.callback(
    Output('graph_01', 'figure'),
    Input('Lista de Gráficos', 'value')

)
def update_output(value):
    if value == 'Infectados Mês':
        fig_infec_susp_vacin_mortes = px.line(months, x=months.index, y="newCases",
               markers= True,
               title='Infecções Divulgadas ao Mês',
               labels = {
                "newCases": "Quantidade",
                "date": "Data"
                },color_discrete_sequence=["royalblue"])    
    elif value == 'Mortes Mês':
        fig_infec_susp_vacin_mortes = px.line(months, x=months.index, y="newDeaths",
               markers= True,
               title='Óbitos Divulgados ao Mês',
               labels = {
                "deathsMS": "Quantidade",
                "date": "Data"
                },color_discrete_sequence=["red"])
    elif value == 'Suspeitos Mês':
        fig_infec_susp_vacin_mortes = px.line(months, x=months.index, y="suspects",
                markers= True,
                title='Casos Suspeitos Divulgados por Mês',
                labels  = {
                "newCases": "Quantidade",
                "date": "Data"
                },color_discrete_sequence=["orange"])
    elif value == 'Vacinado Mês':
        fig_infec_susp_vacin_mortes = px.line(months, x=months.index, y="vaccinated",
                markers= True,
                title='Quantidade de Vacinados por Mês',
                labels  = {
                "newCases": "Quantidade",
                "date": "Data"
                },color_discrete_sequence=["green"])
    elif value == 'Completa Mês':
        fig_infec_susp_vacin_mortes = go.Figure()
        fig_infec_susp_vacin_mortes = fig_infec_susp_vacin_mortes.add_trace(go.Scatter(x = months.index, 
                                    y = scaled_months["newCases"],
                                    mode = 'lines+markers',
                                    name = "Infecções",
                                    line = dict(color='royalblue',width=2,dash='dot')))
        fig_infec_susp_vacin_mortes = fig_infec_susp_vacin_mortes.add_trace(go.Scatter(x = months.index, 
                                    y = scaled_months["suspects"],
                                    mode = 'lines+markers',
                                    name = "Suspeitos",
                                    line = dict(color='orange',width=1,dash='dot')))
        fig_infec_susp_vacin_mortes = fig_infec_susp_vacin_mortes.add_trace(go.Scatter(x = months.index, 
                                    y = scaled_months["vaccinated"],
                                    mode = 'lines+markers',
                                    name = "Vacinados"))
        fig_infec_susp_vacin_mortes = fig_infec_susp_vacin_mortes.add_trace(go.Scatter(x = months.index, 
                                    y = scaled_months["newDeaths"],
                                    mode = 'lines+markers',
                                    name = "Óbitos",
                                    line = dict(color='red')
                                    ))
        fig_infec_susp_vacin_mortes.update_layout(
                                        title='Comparando Novos casos, suspeitos, vacinados e Óbitos Mês',
                                        title_x = 0.5)

         #f' Você Selecionou -> {value}'
    return fig_infec_susp_vacin_mortes



if __name__ == '__main__':
    app.run_server(debug=True)
