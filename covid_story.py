import pandas as pd
import numpy as np
import requests
import yfinance as yf
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import iplot
from plotly.subplots import make_subplots
from mlxtend.preprocessing import minmax_scaling

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
                            width=1000,
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
# Trocando os pontos por vírgulas:
ipca_df["valor"] = [row.replace(",", ".") for row in ipca_df["valor"]]
# Colocando o valor no formato float:
ipca_df["valor"] = ipca_df["valor"].astype(float)
# Separando um dataframe para analizar o IPCA entre 2020 e os dias atuais:
ipca = ipca_df.loc[ipca_df["data"]>="2020-03-01"]
# Dicionário para o Df:
dict_ipca = {"ipca" : ipca[2:], "covid": months_var[2:]}

# nnono plot - 'Variações Mensais: IPCA x Casos de Covid'
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
# comparação dos casos de covid bolsa de valores e dolar
ibov_month = yf.download('^bvsp', start='2020-01-01', end="2022-11-01", interval='1mo')
usd_month = yf.download('USDBRL=X', start='2020-01-01', end="2022-11-01", interval='1mo')

ibov_week = yf.download('^bvsp', start='2020-01-01', end="2022-11-01", interval='1wk')
usd_week = yf.download('USDBRL=X', start='2020-01-01', end="2022-11-01", interval='1wk')

# Obtendo as variações mensais e semanais:
ibov_mvar = ibov_month.pct_change()
usd_mvar = usd_month.pct_change()

ibov_wvar = ibov_week.pct_change()
usd_wvar = usd_week.pct_change()

# Criando o dicionário:
dict_ibov_m = {"ipca" : ipca[4:], "covid": months_var[2:], "ibov":ibov_mvar[4:], "usd":usd_mvar[4:]}

# décimo plot - 'Variações Mensais: IPCA, IBOV, USD e Casos de Covid'
fig_ipca_covid_ibov_usd = go.Figure()
fig_ipca_covid_ibov_usd = fig_ipca_covid_ibov_usd.add_trace(go.Scatter(x = dict_ibov_m["ipca"]["data"],
                               y = dict_ibov_m["ipca"]["valor"], 
                               name = "IPCA no Brasil",
                               line = dict(color='blue')))

fig_ipca_covid_ibov_usd = fig_ipca_covid_ibov_usd.add_trace(go.Scatter(x = dict_ibov_m["covid"].index,
                               y = dict_ibov_m["covid"]["newCases"], 
                               name = "Número de Infecções",
                               line = dict(color='orange')))

fig_ipca_covid_ibov_usd = fig_ipca_covid_ibov_usd.add_trace(go.Scatter(x = dict_ibov_m["covid"].index,
                               y = dict_ibov_m["covid"]["newDeaths"], 
                               name = "Número de Óbitos",
                               line = dict(color='red')))

fig_ipca_covid_ibov_usd = fig_ipca_covid_ibov_usd.add_trace(go.Scatter(x = dict_ibov_m["ibov"].index,
                               y = dict_ibov_m["ibov"]["Close"], 
                               name = "Variação na Bolsa de Valores",
                               line = dict(color='green')))

fig_ipca_covid_ibov_usd = fig_ipca_covid_ibov_usd.add_trace(go.Scatter(x = dict_ibov_m["usd"].index,
                               y = dict_ibov_m["usd"]["Close"], 
                               name = "Variação da Cotação do Dolar",
                               line = dict(color='purple')))


fig_ipca_covid_ibov_usd.update_layout(
                            title='Variações Mensais: IPCA, IBOV, USD e Casos de Covid',
                            title_font_size=20,
                            title_font_color='black',
                            title_x = 0.5)

# Criando o dicionário:
dict_ibov_w = {"covid": weeks_var[2:], "ibov":ibov_wvar[4:], "usd":usd_wvar[4:]}

# Pdecimo primeiro plot - 'Variações Semanais: IBOV, USD e Casos de Covid'
fig_ipca_covid_ibov_usd_week = go.Figure()

fig_ipca_covid_ibov_usd_week = fig_ipca_covid_ibov_usd_week.add_trace(go.Scatter(x = dict_ibov_m["covid"].index,
                               y = dict_ibov_m["covid"]["newCases"], 
                               name = "Número de Infecções"))

fig_ipca_covid_ibov_usd_week = fig_ipca_covid_ibov_usd_week.add_trace(go.Scatter(x = dict_ibov_m["covid"].index,
                               y = dict_ibov_m["covid"]["newDeaths"], 
                               name = "Número de Óbitos"))

fig_ipca_covid_ibov_usd_week = fig_ipca_covid_ibov_usd_week.add_trace(go.Scatter(x = dict_ibov_m["ibov"].index,
                               y = dict_ibov_m["ibov"]["Close"], 
                               name = "Variação na Bolsa de Valores"))

fig_ipca_covid_ibov_usd_week = fig_ipca_covid_ibov_usd_week.add_trace(go.Scatter(x = dict_ibov_m["usd"].index,
                               y = dict_ibov_m["usd"]["Close"], 
                               name = "Variação da Cotação do Dolar"))

fig_ipca_covid_ibov_usd_week.update_layout(
                                title='Variações Semanais: IBOV, USD e Casos de Covid',
                                title_font_size=20,
                                title_font_color='black',
                                title_x = 0.5)
# Avaliando a correlação Mensal:
# Os números entre colchetes "[]" são para ajustar as datas do período:

month_var_df = pd.DataFrame({
    "ipca": [row for row in ipca["valor"]],
    "ipca_data": [row for row in ipca["data"]],
    
    "covid_newCases": [row for row in months_var["newCases"][:-2]],
    "covid_newDeaths": [row for row in months_var["newDeaths"][:-2]],
    "covid_data": [row for row in months_var.index[:-2]],
    
    "ibov": [row for row in ibov_mvar["Close"][2:-1]], 
    "usd": [row for row in usd_mvar["Close"][2:]] 
    
})

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
                    style = {'width': '100%', 'align-items': 'center', 'justify-content': 'center'}),
    dcc.Graph(
        id='graph_01',
        figure=fig_infec_susp_vacin_mortes
    ),
    dcc.Graph(
        id='graph_02',
        figure=fig_infec_mortes_covid
    ),
    dcc.Graph(
        id='graph_03',
        figure=fig_var_novas_inf_divul
    ),
    dcc.Graph(
        id='graph_04',
        figure=fig_var_novos_obit_div
    ),
    dcc.Graph(
        id='graph_05',
        figure=fig_boxplot
    ),
    dcc.Graph(
        id='graph_06',
        figure=fig_ipca_covid_ibov_usd
    ),
    dcc.Graph(
        id='graph_07',
        figure=fig_ipca_covid_ibov_usd_week
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
