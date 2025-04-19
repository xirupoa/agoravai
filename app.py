import pandas as pd
from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

# Carrega os dados
df = pd.read_excel("bucharest.xlsx")
df['Date'] = pd.to_datetime(df['Date'])

# Corrigir inconsistências nos nomes dos times
correcoes = {
    "Astrals": "Astralis",
    "astrals": "Astralis",
    "3DMAX": "3Dmax",
    "3dmax": "3Dmax",
    "BIG": "Big",
    "big": "Big"
}
df['Team'] = df['Team'].astype(str).str.strip().replace(correcoes)
df['Opponent'] = df['Opponent'].astype(str).str.strip().replace(correcoes)

# Inicializa o app
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server  # ← adicione isso aqui

# Função de layout para cada painel
def layout_time(sufixo):
    return dbc.Col([
        html.Div([
            html.H4(f"Time {sufixo}", className="text-white text-center mb-3"),
            dcc.Dropdown(
                id=f'team-dropdown-{sufixo}',
                options=[{'label': team, 'value': team} for team in sorted(df['Team'].unique())],
                placeholder="Selecione o time",
                searchable=True,
                className="mb-2"
            ),
            dcc.Dropdown(
                id=f'map-dropdown-{sufixo}',
                options=[{'label': map_, 'value': map_} for map_ in sorted(df['Map'].unique())],
                placeholder="Selecione o mapa (opcional)",
                searchable=True,
                className="mb-2"
            ),
            dcc.Dropdown(
                id=f'event-dropdown-{sufixo}',
                options=[{'label': e, 'value': e} for e in sorted(df['Event'].dropna().unique())],
                placeholder="Filtrar por evento (opcional)",
                searchable=True,
                className="mb-3"
            ),
            dbc.Row([
                dbc.Col(dbc.Card(id=f'rank-atual-{sufixo}', body=True, className="card-custom"), width=6),
                dbc.Col(dbc.Card(id=f'rank-medio-oponente-{sufixo}', body=True, className="card-custom"), width=6),
            ], className="mb-2 g-1"),
            dbc.Row([
                dbc.Col(dbc.Card(id=f'qtd-mapas-jogados-{sufixo}', body=True, className="card-custom"), width=6),
                dbc.Col(dbc.Card(id=f'porcentagens-tr-ct-{sufixo}', body=True, className="card-custom"), width=6),
            ], className="mb-2 g-1"),
            dbc.Row([
                dbc.Col(dbc.Card(id=f'partidas-19-menor-{sufixo}', body=True, className="card-custom"), width=6),
                dbc.Col(dbc.Card(id=f'partidas-22-maior-{sufixo}', body=True, className="card-custom"), width=6),
            ], className="mb-2 g-1"),
            dbc.Row([
                dbc.Col(dbc.Card(id=f'media-rounds-time-{sufixo}', body=True, className="card-custom"), width=6),
                dbc.Col(dbc.Card(id=f'porcentagem-vitorias-{sufixo}', body=True, className="card-custom"), width=6),
            ], className="mb-3 g-1"),
            html.Div([
                dcc.Graph(id=f'grafico-vitorias-mapa-{sufixo}', config={"displayModeBar": False}, style={"height": "230px"}),
                dcc.Graph(id=f'grafico-evolucao-{sufixo}', config={"displayModeBar": False}, style={"height": "240px"}),
                dcc.Graph(id=f'grafico-distribuicao-rounds-{sufixo}', config={"displayModeBar": False}, style={"height": "240px"}),
                dcc.Graph(id=f'indicador-dificuldade-mapa-{sufixo}', config={"displayModeBar": False}, style={"height": "240px"}),
                html.Div(id=f'tabela-adversarios-{sufixo}', className="mt-3")
            ], style={"maxWidth": "380px", "margin": "30px auto 0 auto"})
        ], style={"maxWidth": "460px", "margin": "0 auto"})
    ], width=12, lg=5)

app.layout = dbc.Container([
    html.H2("Comparativo de Times", className="text-white text-center my-4"),
    html.Div(id='top-times-stats', className='my-5'),
    dbc.Row([
        layout_time('1'),
        html.Div(style={"width": "4px"}),
        layout_time('2')
    ], justify="center")
], fluid=True, className="bg-black")

app.index_string = app.index_string.replace(
    "</head>",
    '''
    <style>
        .card-custom {
            background-color: white;
            color: black;
            text-align: center;
            font-size: 14px;
            height: 70px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 8px;
        }
        .dash-table-container .dash-spreadsheet-container {
            background-color: white;
            font-size: 13px;
        }
    </style>
    </head>
    '''
)

def gerar_callbacks(sufixo):
    @app.callback(
        [
            Output(f'rank-atual-{sufixo}', 'children'),
            Output(f'rank-medio-oponente-{sufixo}', 'children'),
            Output(f'qtd-mapas-jogados-{sufixo}', 'children'),
            Output(f'porcentagens-tr-ct-{sufixo}', 'children'),
            Output(f'partidas-19-menor-{sufixo}', 'children'),
            Output(f'partidas-22-maior-{sufixo}', 'children'),
            Output(f'media-rounds-time-{sufixo}', 'children'),
            Output(f'porcentagem-vitorias-{sufixo}', 'children'),
            Output(f'grafico-vitorias-mapa-{sufixo}', 'figure'),
            Output(f'grafico-evolucao-{sufixo}', 'figure'),
            Output(f'grafico-distribuicao-rounds-{sufixo}', 'figure'),
            Output(f'tabela-adversarios-{sufixo}', 'children'),
            Output(f'indicador-dificuldade-mapa-{sufixo}', 'figure')
        ],
        [
            Input(f'team-dropdown-{sufixo}', 'value'),
            Input(f'map-dropdown-{sufixo}', 'value'),
            Input(f'event-dropdown-{sufixo}', 'value')
        ]
    )
    def update_dashboard(team, map_, event):
        fig_empty = lambda title: go.Figure().update_layout(title=title, plot_bgcolor='black', paper_bgcolor='black', font_color='white')
        if not team:
            return ["-"] * 8 + [fig_empty("Histórico de Vitórias"), fig_empty("Evolução do Desempenho"), fig_empty("Distribuição de Rounds"), None, fig_empty("Dificuldade dos Mapas")]

        df_filtered = df[df['Team'] == team].copy()
        if map_: df_filtered = df_filtered[df_filtered['Map'] == map_]
        if event: df_filtered = df_filtered[df_filtered['Event'] == event]

        df_filtered['rounds_team'] = pd.to_numeric(df_filtered['rounds_team'], errors='coerce').fillna(0)
        df_filtered['rounds_opponent'] = pd.to_numeric(df_filtered['rounds_opponent'], errors='coerce').fillna(0)
        df_filtered['Placar_Total'] = df_filtered['rounds_team'] + df_filtered['rounds_opponent']

        rank_atual = df_filtered['rank_team'].iloc[-1] if not df_filtered.empty else '-'
        rank_medio_oponente = round(df_filtered['rank_opponent'].mean(), 2) if not df_filtered.empty else '-'
        qtd_jogados = len(df_filtered)
        tr_pct = round(df_filtered['tr_team_porcent'].mean(), 2) if not df_filtered.empty else '-'
        ct_pct = round(df_filtered['ct_team_porcent'].mean(), 2) if not df_filtered.empty else '-'
        porcentagens = f"TR: {tr_pct}% | CT: {ct_pct}%"
        pct_19_menor = round((df_filtered['Placar_Total'] <= 19).mean() * 100, 2) if qtd_jogados else '-'
        pct_22_maior = round((df_filtered['Placar_Total'] >= 22).mean() * 100, 2) if qtd_jogados else '-'
        media_rounds = round(df_filtered['rounds_team'].sum() / qtd_jogados, 2) if qtd_jogados else '-'
        pct_vitorias = round(df_filtered['Venceu'].mean() * 100, 2) if qtd_jogados else '-'

        mapa_stats = df_filtered.groupby('Map').agg(partidas=('Winner', 'count'), vitorias=('Venceu', 'sum')).reset_index()
        mapa_stats['pct_vitorias'] = (mapa_stats['vitorias'] / mapa_stats['partidas'] * 100).round(0).astype(int)
        fig_bar = px.bar(mapa_stats, x='Map', y='pct_vitorias', text='pct_vitorias')
        fig_bar.update_layout(title="Histórico de Vitórias", plot_bgcolor='black', paper_bgcolor='black', font_color='white', margin=dict(t=120, l=20, r=20, b=20), xaxis=dict(showgrid=False), yaxis=dict(showgrid=False, title='', range=[0, 110]), height=230)
        fig_bar.update_traces(marker_color='white', textposition='outside', texttemplate='%{text}%')

        df_sorted = df_filtered.sort_values('Date')
        df_sorted['pct_vitoria_acumulada'] = df_sorted['Venceu'].expanding().mean() * 100
        df_sorted['media_rolling_rounds'] = df_sorted['Placar_Total'].rolling(window=3, min_periods=1).mean()
        fig_line = px.line(df_sorted, x='Date', y=['pct_vitoria_acumulada', 'media_rolling_rounds'], labels={'value': 'Valor', 'variable': 'Métrica', 'Date': 'Data'}, title="Evolução do Desempenho")
        fig_line.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='white', margin=dict(t=80, l=20, r=20, b=20), height=240)

        bins = [0, 19, 24, 29, 100]
        labels = ['≤19', '20–24', '25–29', '30+']
        df_filtered['Faixa Rounds'] = pd.cut(df_filtered['Placar_Total'], bins=bins, labels=labels, right=True)
        fig_hist = px.histogram(df_filtered, x='Faixa Rounds', title="Distribuição de Rounds")
        fig_hist.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='white', margin=dict(t=80, l=20, r=20, b=20), height=240, xaxis_title='Faixa de Rounds', yaxis_title='Partidas')
        fig_hist.update_traces(marker_color='white')

        dificuldade = df_filtered.groupby('Map').agg(rank_medio_oponente=('rank_opponent', 'mean')).reset_index()
        fig_dificuldade = px.bar(dificuldade, x='Map', y='rank_medio_oponente', text='rank_medio_oponente', title="Dificuldade dos Mapas (Rank Médio dos Oponentes)", color='rank_medio_oponente', color_continuous_scale='RdBu_r')
        fig_dificuldade.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='white', margin=dict(t=60, l=20, r=20, b=20), coloraxis_showscale=False, height=240)
        fig_dificuldade.update_traces(texttemplate='%{text:.1f}', textposition='outside')

        adversarios = df_filtered.groupby('Opponent').agg(Partidas=('Opponent', 'count'), Vitorias=('Venceu', 'sum')).reset_index()
        adversarios['% Vitórias'] = (adversarios['Vitorias'] / adversarios['Partidas'] * 100).round(1)
        adversarios = adversarios.sort_values('Partidas', ascending=False).head(5)
        tabela = dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in adversarios.columns],
            data=adversarios.to_dict("records"),
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center"},
            style_header={"backgroundColor": "#e1e1e1", "fontWeight": "bold"},
            style_data={"backgroundColor": "white", "color": "black"}
        )

        return (
            f"Rank Atual: {rank_atual}",
            f"Rank Médio Oponente: {rank_medio_oponente}",
            f"Qtd. Mapas Jogados: {qtd_jogados}",
            porcentagens,
            f"% Partidas <= 19 rounds: {pct_19_menor}%",
            f"% Partidas >= 22 rounds: {pct_22_maior}%",
            f"Média de Rounds: {media_rounds}",
            f"% Vitórias: {pct_vitorias}%",
            fig_bar, fig_line, fig_hist, tabela, fig_dificuldade
        )

for sufixo in ['1', '2']:
    gerar_callbacks(sufixo)

# Top 5 ataque/defesa SEM depender de seleção
def plot_top_times():
    top_defesa = df.groupby('Team')['ct_team_porcent'].mean().sort_values(ascending=False).head(5).reset_index()
    top_ataque = df.groupby('Team')['tr_team_porcent'].mean().sort_values(ascending=False).head(5).reset_index()

    fig_defesa = px.bar(top_defesa, x='Team', y='ct_team_porcent', text='ct_team_porcent', title='Top 5 Times mais Defensivos (CT)', labels={'ct_team_porcent': 'Winrate CT'})
    fig_defesa.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='white', height=300)
    fig_defesa.update_traces(marker_color='skyblue', texttemplate='%{text:.1f}%', textposition='outside')

    fig_ataque = px.bar(top_ataque, x='Team', y='tr_team_porcent', text='tr_team_porcent', title='Top 5 Times mais Ofensivos (TR)', labels={'tr_team_porcent': 'Winrate TR'})
    fig_ataque.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='white', height=300)
    fig_ataque.update_traces(marker_color='orangered', texttemplate='%{text:.1f}%', textposition='outside')

    return dbc.Row([
        dbc.Col(dcc.Graph(figure=fig_defesa, config={"displayModeBar": False}), width=6),
        dbc.Col(dcc.Graph(figure=fig_ataque, config={"displayModeBar": False}), width=6)
    ], justify="center")

@app.callback(
    Output('top-times-stats', 'children'),
    Input(f'team-dropdown-1', 'value')
)
def render_top(_):
    return plot_top_times()

if __name__ == '__main__':
    app.run(debug=True)