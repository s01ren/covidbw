#!/usr/bin/env python3.6
# -----------------------------------------------
# imports
# -----------------------------------------------
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
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
# app
# -----------------------------------------------
app = dash.Dash(__name__, requests_pathname_prefix="/labs/covid/app/", routes_pathname_prefix="/labs/covid/app/")

app.layout = html.Div([

    html.Div(
        children = [
            html.H1('Corona in Baden Württemberg'),
        ]
    ),

    html.Div(
        className = 'FooterDiv',
        children = [
            html.Div(
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
        ]
    ),

     

    

    

    # -----------------------------------------------
    html.Div(className = 'row', children = [html.Div(html.Br())]),

    # -----------------------------------------------
    html.Div(
        className = 'ChartDiv',
        children = [
            dcc.Graph(id = 'InfectsTotal'),
        ],
    ),

    # -----------------------------------------------
    html.Div(className = 'row', children = [html.Div(html.Br())]),

    # -----------------------------------------------
    html.Div(
        className = 'ChartDiv',
        children = [
            dcc.Graph(id = 'InfectsPerDay'),
        ],
    ),

    # -----------------------------------------------
    html.Div(className = 'row', children = [html.Div(html.Br())]),

    # -----------------------------------------------
    html.Div(
        className = 'ChartDiv',
        children = [
            dcc.Graph(id = 'InfectsPerThousand'),
        ],
    ),

    # -----------------------------------------------
    html.Div(className = 'row', children = [html.Div(html.Br())]),

    # -----------------------------------------------
    html.Div(
        className = 'FooterDiv',
        children = [
            html.Label(['Quelle: ', html.A('Ministerium für Soziales und Integration', href = "https://sozialministerium.baden-wuerttemberg.de/de/gesundheit-pflege/gesundheitsschutz/infektionsschutz-hygiene/informationen-zu-coronavirus/", target = "_blank")]), 
            html.P('Datenstand: ' + coronatime)
        ]
    ),
    

])

# -----------------------------------------------
# Infects Per Thousand
# -----------------------------------------------
@app.callback(
    Output('InfectsPerThousand', 'figure'),
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
    df_filtered['InfProTausend'] = round(df_filtered.Infizierte / df_filtered.Anzahl * 1000, 2)

    dfChart = df_filtered.groupby(['Datum', 'Kreis']).sum().reset_index()


    fig = go.Figure()
    fig.update_layout(
        title = "Infizierte pro 1.000 Einwohnern in " + label_title,
        xaxis_title = "",
        yaxis_title = "",
        template = 'simple_white'
    )

    for k in dfChart.Kreis.unique():
        dfChartK = dfChart[(dfChart.Kreis == k)]
        fig.add_trace(go.Scatter(x = dfChartK.Datum, y = dfChartK.InfProTausend, name = k))



    fig.update_traces(textposition='top center')
    fig.data[0].update(mode='markers+lines')
    return fig

# -----------------------------------------------
# New Infects Per Day
# -----------------------------------------------
@app.callback(
    Output('InfectsPerDay', 'figure'),
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

    dfChart = df_filtered.groupby(['Datum']).sum().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x = dfChart.Datum, y = dfChart.VeraenderungVortag, text = dfChart.VeraenderungVortag, name = 'Neuinfektionen'))
    fig.update_layout(
        title = "Neuinfektionen ggü. Vortag in {}".format(label_title),
        xaxis_title = "",
        yaxis_title = "",
        template = 'simple_white'
    )
    fig.update_traces(textposition='top center')
    fig.data[0].update(mode='markers+lines+text')
    return fig


# -----------------------------------------------
# Infects Total
# -----------------------------------------------
@app.callback(
    Output('InfectsTotal', 'figure'),
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

    dfChart = df_filtered.groupby(['Datum']).sum().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x = dfChart.Datum, y = dfChart.Infizierte, text = dfChart.Infizierte, name = 'Infizierte'))
    fig.update_layout(
        title = "Infizierte in {}".format(label_title),
        xaxis_title = "",
        yaxis_title = "",
        template = 'simple_white'
    )
    fig.data[0].update(mode='markers+lines+text')
    fig.update_traces(textposition='top center')
    fig.add_annotation(
        x = "2020-03-22",
        y = dfChart[(dfChart.Datum == "2020-03-22")]['Infizierte'].max(),
        text="verschärftes <br>Kontaktverbot"
    )
    fig.add_annotation(
        x = "2020-03-17",
        y = dfChart[(dfChart.Datum == "2020-03-17")]['Infizierte'].max(),
        text="Schulschließungen",
    )
    fig.add_annotation(
        x = "2020-03-11",
        y = dfChart[(dfChart.Datum == "2020-03-11")]['Infizierte'].max(),
        text="Verbot Veranstaltungen<br>>1.000 Personen",
    )
    fig.update_annotations(
        dict(
            showarrow=True,
            arrowhead=7,
            ax=0,
            ay=40
        )
    )
    return fig




# -----------------------------------------------
# run app
# -----------------------------------------------
if __name__ == '__main__':
    app.run_server(debug = False, host='0.0.0.0')