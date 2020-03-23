#!/usr/bin/env python3.6
#%% import 
from datetime import date
import pandas as pd
import os

#%% import raw data
link = 'https://sozialministerium.baden-wuerttemberg.de/fileadmin/redaktion/m-sm/intern/downloads/Downloads_Gesundheitsschutz/Tabelle_Coronavirus-Faelle-BW.xlsx'

df_raw = pd.read_excel(
    link,
    header = 6,
    nrows = 44
    )
df_raw

#%% tidy data
df_tidy = df_raw.rename(columns = {"Unnamed: 0": "Kreis"})
df_tidy = pd.melt(
    df_tidy, 
    id_vars = 'Kreis',
    value_vars = df_tidy.columns[1:]
)
df_tidy = df_tidy.rename(columns = {"variable": "Datum", "value": "Infizierte"})
df_tidy = df_tidy[['Datum', 'Kreis', 'Infizierte']]
df_tidy = df_tidy.sort_values(by=['Datum', 'Kreis'])
df_tidy

#%% add change
df_change = df_tidy
df_change = df_change.set_index('Kreis')
df_change = pd.concat([df_change, df_change.groupby('Kreis').shift()], axis = 1)
df_change.columns = ['Datum', 'Infizierte', 'Vortag', 'InfVortag']
df_change['VeraenderungVortag'] = df_change.Infizierte - df_change.InfVortag
df_change.reset_index(inplace = True)
df_change = df_change[['Datum', 'Kreis', 'Infizierte', 'VeraenderungVortag']]
df_change

#%% export
export_dir = os.path.abspath(os.path.dirname(__file__))

df_change.to_csv(
    path_or_buf = export_dir + "/app/corona.csv",
    sep = ";",
    header = True,
    index = False,
    encoding = 'utf-8'
)
df_change.to_csv(
    path_or_buf = export_dir + "/data_bak/corona_" + date.today().strftime("%Y%m%d") + ".csv",
    sep = ";",
    header = True,
    index = False,
    encoding = 'utf-8'
)

# %%
