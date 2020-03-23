#!/usr/bin/env python3.6
# -----------------------------------------------
# imports
# -----------------------------------------------
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime as dt
import os
from pathlib import Path

# -----------------------------------------------
# find directory & file
# -----------------------------------------------
pathwd = os.path.abspath(os.path.dirname(__file__))
coronafile = Path(pathwd, "corona.csv")
coronatime = dt.fromtimestamp(os.path.getmtime(coronafile)).strftime("%d.%m.%Y %H:%M:%S")

# -----------------------------------------------
# load data
# -----------------------------------------------
df = pd.read_csv(coronafile, sep = ';')


# -----------------------------------------------
# generate table
# -----------------------------------------------
def generate_table(dataframe, max_rows=50):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])

# -----------------------------------------------
# app
# -----------------------------------------------
app = dash.Dash(__name__, requests_pathname_prefix="/labs/covid/app/", routes_pathname_prefix="/labs/covid/app/")

app.layout = html.Div([

    html.Div(
        className = 'row',
        children = [
            html.H1('Corona in Baden Württemberg'),
            html.P('Letztes Update: ' + coronatime)
        ]
    ),

    html.Div(
        className = 'row',
        children = [
            html.H4('Filter'),
        ]
    ),

    html.Div(
        className = 'row',
        children = [
            html.Div(
                className = 'one columns',
                children = [
                    html.P('Kreise')
                ]
            ),
            html.Div(
                className = 'four columns',
                children = [
                    dcc.Dropdown(
                        id = 'FilterKreis',
                        options = [
                            {'label': k, 'value': k} for k in df.Kreis.unique()
                        ],
                        multi = True,
                        placeholder = 'Kreise ...'
                    )
                ]
            ),
        ]
    ),

    html.Div(className = 'row', children = [html.P()]),

    html.Div(
        className = 'row',
        children = [
            html.Div(
                className = 'one columns',
                children = [
                    html.P('Datum')
                ]
            ),
            html.Div(
                className = 'four columns',
                children = [
                    dcc.DatePickerRange(
                        id = 'FilterDatum',
                        end_date = df.Datum.max(),
                        start_date = df.Datum.min(),
                        display_format = 'DD. MMM YY'
                    ),
                ]
            ),
        ]
    ),

    html.Div(
        className = 'twelve columns',
        children = [
            dcc.Graph(id = 'LineChartInfectsPerDay'),
        ]
    ),

    html.Div(
        className = 'five columns',
        children = [
            dcc.Graph(id = 'LineChartInfectsChange'),
        ]
    ),

    html.Div(
        className = 'six columns',
        children = [
            #dcc.Graph(id = 'PieChartPerCounty'),
            dcc.Graph(id = 'LinePerThousand'),
        ]
    ),


])

# -----------------------------------------------
# Lines Per Thousand
# -----------------------------------------------
@app.callback(
    Output('LinePerThousand', 'figure'),
    [
        Input('FilterKreis', 'value'),
        Input('FilterDatum', 'start_date'),
        Input('FilterDatum', 'end_date')
    ]
)
def update_testgraph(kreis, start_date, end_date):
    if kreis is None or kreis == []:
        df_filtered = df
        label_title = 'Baden Württemberg'
    else:
        df_filtered = df[df.Kreis.isin(kreis)]
        label_title = ', '.join(kreis)
    
    df_filtered = df_filtered[
        (df.Datum >= start_date) & 
        (df.Datum <= end_date)
    ]

    dfpop = pd.read_csv(Path(pathwd, "population.csv"), sep = ';', usecols=['Kreis', 'Anzahl'])
    df_filtered = df_filtered.merge(dfpop, on = ('Kreis'))
    df_filtered['InfProTausend'] = df_filtered.Infizierte / df_filtered.Anzahl * 1000

    fig = px.line(
        data_frame = df_filtered,
        x = "Datum",
        y = "InfProTausend",
        color = "Kreis",
        title = "Infizierte pro 1.000 Einwohnern in " + label_title,
        labels = {
            'x': 'Datum',
            'y': 'Infizierte pro 1.000 EW'
        }
    )

    return fig

# -----------------------------------------------
# Infects total
# -----------------------------------------------
@app.callback(
    Output('LineChartInfectsPerDay', 'figure'),
    [
        Input('FilterKreis', 'value'),
        Input('FilterDatum', 'start_date'),
        Input('FilterDatum', 'end_date')
    ]
)
def update_lineGraph(kreis, start_date, end_date):
    if kreis is None or kreis == []:
        df_filtered = df
        label_title = 'Baden Württemberg'
    else:
        df_filtered = df[df.Kreis.isin(kreis)]
        label_title = ', '.join(kreis)
    
    df_filtered = df_filtered[
        (df.Datum >= start_date) & 
        (df.Datum <= end_date)
    ]

    InfPerDateAndCountry = df_filtered.groupby(['Datum']).sum().reset_index()

    fig = px.line(
        data_frame = InfPerDateAndCountry,
        x = "Datum",
        y = "Infizierte",
        text = "Infizierte",
        title = "Infizierte in {}".format(label_title)
    )
    fig.data[0].update(mode='markers+lines+text')
    fig.update_traces(textposition='top center')
    fig.add_annotation(
        x = "2020-03-22",
        y = InfPerDateAndCountry[(InfPerDateAndCountry.Datum == "2020-03-22")]['Infizierte'].max(),
        text="verschärftes <br>Kontaktverbot"
    )
    fig.add_annotation(
        x = "2020-03-17",
        y = InfPerDateAndCountry[(InfPerDateAndCountry.Datum == "2020-03-17")]['Infizierte'].max(),
        text="Schulschließungen",
    )
    fig.add_annotation(
        x = "2020-03-11",
        y = InfPerDateAndCountry[(InfPerDateAndCountry.Datum == "2020-03-11")]['Infizierte'].max(),
        text="Verbot Veranstaltungen<br>>1.000 Personen",
    )

    fig.update_annotations(
        dict(
            showarrow=True,
            arrowhead=7,
            ax=0,
            ay=-40
        )
    )
    return fig
    

# -----------------------------------------------
# Infects per day
# -----------------------------------------------
@app.callback(
    Output('LineChartInfectsChange', 'figure'),
    [
        Input('FilterKreis', 'value'),
        Input('FilterDatum', 'start_date'),
        Input('FilterDatum', 'end_date')
    ]
)
def update_lineGraphChange(kreis, start_date, end_date):
    if kreis is None or kreis == []:
        df_filtered = df
        label_title = 'Baden Württemberg'
    else:
        df_filtered = df[df.Kreis.isin(kreis)]
        label_title = ', '.join(kreis)
    
    df_filtered = df_filtered[
        (df.Datum >= start_date) & 
        (df.Datum <= end_date)
    ]

    InfPerDateAndCountry = df_filtered.groupby(['Datum']).sum().reset_index()

    fig = px.line(
        data_frame = InfPerDateAndCountry,
        x = "Datum",
        y = "VeraenderungVortag",
        text = "VeraenderungVortag",
        title = "Neuinfektionen ggü. Vortag in {}".format(label_title)
    )
    fig.data[0].update(mode='markers+lines+text')
    fig.update_traces(textposition='top center')

    return fig




# -----------------------------------------------
# run app
# -----------------------------------------------
if __name__ == '__main__':
    app.run_server(debug = False, host='0.0.0.0')