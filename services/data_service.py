import pandas as pd
import numpy as np
import utils.functions as fn
import utils.constants as c
import streamlit as st
import warnings
warnings.filterwarnings("ignore")

def load_data(date_range):
    """Carga y filtra los datos según el tipo de viaje."""
    
    df = fn.get_company_history(date_range)
    df_ind = fn.get_indicators(date_range)
    
    return df, df_ind

def filter_data(df, df_ind, type_trip):
    
    if type_trip == 'Inbound':
        col_state = 'destination'
        df_ind_filt = df_ind.query("res_origin == 'COUNTRY' & res_destination == 'STATE'")
    else:
        col_state = 'origin'
        df_ind_filt = df_ind.query("res_origin == 'STATE' & res_destination == 'COUNTRY'")

    return df, df_ind_filt, col_state

def process_data(df, df_ind_filt, col_group, f, freq, col_value_g, col_agg_type, col_value, round_value):
    """Agrega y fusiona los datos de la empresa y de la industria."""
    
    df, df_ind_agg = aggregate_data(df, df_ind_filt, col_group, f, freq)

    merge_cols = ["start_date", col_group, "equip", col_value_g] + ([col_agg_type] if col_agg_type else [])

    df_merged = pd.merge(
        df[merge_cols],
        df_ind_agg[merge_cols],
        on=["start_date", col_group, "equip"], suffixes=("_c", "_i")
    )

    if col_agg_type:
        df_merged[f"{col_value}_c"] = df_merged[f"{col_value_g}_c"] / df_merged[f"{col_agg_type}_c"]
        df_merged[f"{col_value}_i"] = df_merged[f"{col_value_g}_i"] / df_merged[f"{col_agg_type}_i"]
    else:
        df_merged[f"{col_value}_c"] = df_merged[f"{col_value_g}_c"]
        df_merged[f"{col_value}_i"] = df_merged[f"{col_value_g}_i"]

    df_merged["ratio"] = df_merged[f"{col_value}_c"] / df_merged[f"{col_value}_i"]
    df_merged["diff"] = df_merged[f"{col_value}_c"] - df_merged[f"{col_value}_i"]

    df_merged = df_merged.round({"ratio":2, "diff":round_value, f"{col_value}_c":round_value, f"{col_value}_i":round_value})

    return df_merged

def sort_day_week(df):
    """Ordena los días de la semana en el DataFrame."""
    
    df = df.set_index('day_of_week')
    valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    existing_days = df.index.intersection(valid_days)
    df = df.loc[existing_days].reset_index()
    
    return df

def aggregate_data(df, df_ind_filt, col_group, f, freq, raw_list=[]):
    """Realiza la agregación de datos según la frecuencia especificada."""

    df['start_date'] = pd.to_datetime(df['start_date'])
    df_ind_filt['start_date'] = pd.to_datetime(df_ind_filt['start_date'])
    
    if freq == 'Total':
        min_date = df['start_date'].min().date()
        df_agg = df.groupby([col_group, 'equip'])[['income', 'cost', 'profit', 'days', 'distance']].sum().reset_index()
        df_ind_agg = df_ind_filt.groupby([col_group, 'equip'])[['income', 'cost', 'profit', 'days', 'distance']].sum().reset_index()
        df_agg['start_date'] = min_date
        df_ind_agg['start_date'] = min_date
    elif freq == 'Daily':
        df['day_of_week'] = df['start_date'].dt.day_name()
        df_agg = df.groupby(['day_of_week', col_group, 'equip'])[['income', 'cost', 'profit', 'days', 'distance']].sum().reset_index()
        df_agg = sort_day_week(df_agg)
        df_agg = df_agg.rename(columns={'day_of_week': 'start_date'})
        
        df_ind_filt['day_of_week'] = df_ind_filt['start_date'].dt.day_name()
        df_ind_agg = df_ind_filt.groupby(['day_of_week', col_group, 'equip'])[['income', 'cost', 'profit', 'days', 'distance']].sum().reset_index()
        df_ind_agg = sort_day_week(df_ind_agg)
        df_ind_agg = df_ind_agg.rename(columns={'day_of_week': 'start_date'})
        
    else:
        df_agg = df.groupby([pd.Grouper(key='start_date', freq=f), col_group, 'equip'])[['income', 'cost', 'profit', 'days', 'distance']].sum().reset_index()
        df_ind_agg = df_ind_filt.groupby([pd.Grouper(key='start_date', freq=f), col_group, 'equip'])[['income', 'cost', 'profit', 'days', 'distance']].sum().reset_index()
    
    return df_agg, df_ind_agg

def aggregate_data_distance(df, col_group, f, freq, col_value, col_value_g, col_agg_type):
    """Realiza la agregación de datos según la frecuencia especificada."""

    df['start_date'] = pd.to_datetime(df['start_date'])

    if freq == 'Total':
        min_date = df['start_date'].min().date()
        df_agg = df.groupby([col_group, 'equip']).agg(
            income=('income', 'sum'),
            profit=('profit', 'sum'),
            cost=('cost', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            days_mean=('days', 'mean')).reset_index()
        df_agg['start_date'] = min_date
        
    elif freq == 'Daily':
        df['day_of_week'] = df['start_date'].dt.day_name()
        df_agg = df.groupby(['day_of_week', col_group, 'equip'])[['income', 'cost', 'profit', 'days', 'distance']].agg(
            income=('income', 'sum'),
            profit=('profit', 'sum'),
            cost=('cost', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            days_mean=('days', 'mean')).reset_index()
        df_agg = sort_day_week(df_agg)
        df_agg = df_agg.rename(columns={'day_of_week': 'start_date'})
        df_ind_agg = sort_day_week(df_ind_agg)
        df_ind_agg = df_ind_agg.rename(columns={'day_of_week': 'start_date'})
        
    else:
        df_agg = df.groupby([pd.Grouper(key='start_date', freq=f), col_group, 'equip']).agg(
            income=('income', 'sum'),
            profit=('profit', 'sum'),
            cost=('cost', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            days_mean=('days', 'mean')).reset_index()
        
    df_agg[col_value] = df_agg[col_value_g] / df_agg[col_agg_type]
    
    df_agg['days_mean'] = np.ceil(df_agg['days_mean'])
    df_agg['comb'] =df_agg[col_value] / df_agg['days_mean']
    comb_min, comb_max = df_agg['comb'].min(), df_agg['comb'].max()
    df_agg['comb2'] = df_agg['comb'].apply(lambda x: (x-comb_min)/(comb_max-comb_min))
    df_agg['comb2'] = df_agg['comb2']*90
    df_agg['comb2'] = df_agg['comb2'] + 10
           
    return df_agg

def aggregate_data_raw(df, col_group, f, freq, raw_list=[]):
    """Realiza la agregación de datos según la frecuencia especificada."""

    df['start_date'] = pd.to_datetime(df['start_date'])

    if freq == 'Total':
        min_date = df['start_date'].min().date()
        df_agg = df.groupby([col_group, 'equip'] + raw_list)[['income', 'cost', 'profit', 'days', 'distance']].sum().reset_index()
        df_agg['start_date'] = min_date
    elif freq == 'Daily':
        df['day_of_week'] = df['start_date'].dt.day_name()
        df_agg = df.groupby(['day_of_week', col_group, 'equip'] + raw_list)[['income', 'cost', 'profit', 'days', 'distance']].sum().reset_index()
        df_agg = sort_day_week(df_agg)
        df_agg = df_agg.rename(columns={'day_of_week': 'start_date'})
    else:
        df_agg = df.groupby([pd.Grouper(key='start_date', freq=f), col_group, 'equip'] + raw_list)[['income', 'cost', 'profit', 'days', 'distance']].sum().reset_index()

    return df_agg

def get_top_categories(df, col_value, cat_col):
    """Realiza la agregación de datos según broker_shipper."""

    for i in range(6, -1, -1):
        
        df_agg = df.groupby([cat_col]).agg(
            median=(col_value, 'median'),
            count=(col_value, 'nunique')).reset_index().query("count >= @i").sort_values(by='median', ascending=False)
    
        df_agg_out = df.groupby([cat_col]).agg(
                median=(col_value, 'median'),
                count=(col_value, 'nunique')).reset_index().query("count < @i").sort_values(by='median', ascending=False)

        if len(df_agg) > 5:
            break

    cat = list(df_agg[cat_col].unique())
    cat_out = list(df_agg_out[cat_col].unique())
    
    categories = cat + cat_out
       
    return cat, categories

def prepare_pivot_data(df_merged, col_group, col_value, round_value):
    """Prepara los datos pivoteados para visualización en gráficos."""
    df_pivot_i = df_merged.pivot_table(index=[col_group, 'start_date'], values=f"{col_value}_i", columns="equip").reset_index()
    df_pivot_c = df_merged.pivot_table(index=[col_group, 'start_date'], values=f"{col_value}_c", columns="equip").reset_index()
    df_pivot_r = df_merged.pivot_table(index=[col_group, 'start_date'], values='ratio', columns="equip").reset_index()
    
    df_pivot = pd.merge(df_pivot_c, df_pivot_i, on=[col_group, 'start_date'], suffixes=('_c', '_i'))
    df_pivot = pd.merge(df_pivot, df_pivot_r, on=[col_group, 'start_date'], suffixes=('', '_r'))

    if 'cost' in col_value:
        df_pivot["best_equip_c"] = df_pivot[['REEFER_c', 'VAN_c', 'FLATBED_c']].idxmin(axis=1)
    else:
        df_pivot["best_equip_c"] = df_pivot[['REEFER_c', 'VAN_c', 'FLATBED_c']].idxmax(axis=1)
        
    df_pivot["best_equip_c"] = df_pivot["best_equip_c"].apply(lambda x: x.split('_')[0])
    df_pivot["best_equip_r"] = df_pivot[['REEFER', 'VAN', 'FLATBED']].idxmax(axis=1)
    df_pivot['equip_color_r'] = df_pivot[['REEFER', 'VAN', 'FLATBED']].max(axis=1) > 1
    df_pivot['equip_color_r'] = df_pivot['equip_color_r'].map({True: 'green', False: 'red'})
    
    df_pivot = df_pivot.fillna(0)
    
    for equip in ['REEFER', 'VAN', 'FLATBED']:
        df_pivot[f'{equip}_r'] = df_pivot.apply(lambda x: 
                            f"{x[equip]}({c.client}:{x[f'{equip}_c']:,.{round_value}f}/Ind:{x[f'{equip}_i']:,.{round_value}f})" 
                            if x[equip] > 0 else '', axis=1)
 
    return df_pivot

def merge_raw_agg(df_agg, df_agg_sp_filt, df_ind_agg, col_state, freq, col_value, col_value_g, col_agg_type):
        
    cols_group = [col_state] if freq == 'Total' else [col_state, 'start_date']
    df_merged = pd.merge(df_agg_sp_filt, df_agg, on=cols_group, how='left', suffixes=('_b', '_cf'))
    df_merged = pd.merge(df_merged, df_ind_agg, on=cols_group, how='left', suffixes=('', '_if'))
 
    if col_agg_type != '':
        cols_keep = [col_state, 'start_date', 'equip', 
                           f'{col_value_g}_b', f'{col_agg_type}_b',
                           f'{col_value_g}_cf', f'{col_agg_type}_cf',
                           f'{col_value_g}', f'{col_agg_type}']
    else:
        cols_keep = [col_state, 'start_date', 'equip', 
                           f'{col_value_g}_b',
                           f'{col_value_g}_cf',
                           f'{col_value_g}']
        
    if 'start_date_b' in df_merged.columns:
        df_merged['start_date'] = df_merged['start_date_b']

    df_merged = df_merged[cols_keep]

    for suff in ['_b', '_cf', '']:
        if col_agg_type:
            df_merged[f"{col_value}{suff}"] = df_merged[f"{col_value_g}{suff}"] / df_merged[f"{col_agg_type}{suff}"]
        else:
            df_merged[f"{col_value}{suff}"] = df_merged[f"{col_value_g}{suff}"]
            
    df_merged['ratio_bc'] = df_merged[f"{col_value}_b"] / df_merged[f"{col_value}_cf"]
    df_merged['ratio_bi'] = df_merged[f"{col_value}_b"] / df_merged[f"{col_value}"]
    
    df_merged['diff_bc'] = df_merged[f"{col_value}_b"] - df_merged[f"{col_value}_cf"]
    df_merged['diff_bi'] = df_merged[f"{col_value}_b"] - df_merged[f"{col_value}"]

    return df_merged

def filter_by_equip(df, equip):
    """Filtra los datos por el equipo seleccionado."""
    return df.query(f"equip == '{equip}'")

def filter_by_state(df, state, col_state):
    """Filtra los datos por el estado seleccionado."""
    if state != 'ALL':
        return df.query(f"{col_state} == '{state}'")
    return df

def filter_by_cat(df, col_cat, value):
    """Filtra los datos por el equipo seleccionado."""
    return df.query(f"{col_cat} == '{value}'")

def get_equip_color_dict():
    """Devuelve un diccionario con los colores asociados a cada tipo de equipo."""
    return {
        "FLATBED": "#a920f5",
        "REEFER": "#00d9fc",
        "VAN": "#ffbf00"
    }
