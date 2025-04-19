import pandas as pd
from dash import Dash, html
import dash_bootstrap_components as dbc

df = pd.read_excel("bucharest.xlsx")
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server

app.layout = dbc.Container([
    html.H1("Dashboard CS:GO"),
    html.P(f"Total de partidas carregadas: {len(df)}")
], className="p-4")

if __name__ == "__main__":
    app.run(debug=True)