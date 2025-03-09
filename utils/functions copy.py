import pandas as pd
import numpy as np
import requests
import streamlit as st
import datetime as dt
import boto3
import json
import utils.dictionaries as dic
import requests
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from index import token
import warnings
warnings.filterwarnings("ignore")

def get_resolution(df_full, col):
    
    df_full['resolution'] = np.nan

    df_full.loc[pd.to_numeric(df_full[col], errors='coerce').notna(), 'resolution'] = 'HUB'
    df_full.loc[df_full[col] == 'USA', 'resolution'] = 'COUNTRY'
    df_full.loc[df_full[col].isin(['SOUTHEAST', 'SOUTHWEST', 'WEST', 'MIDWEST', 'NORTHEAST']), 'resolution'] = 'REGION'
    df_full['resolution'] = df_full['resolution'].fillna('STATE')
    
    return df_full

def get_apikey():

    secret_name = "efdata/apikeys/indicators"
    region_name = 'us-east-1'
    client = boto3.client('secretsmanager',  region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secret_data = json.loads(response['SecretString'])
    key = secret_data['apikey']
    apikey=f'Apikey {key}'
    
    return apikey

class DaysCalculator:
    """Calculates trip duration in days."""
    
    @staticmethod
    def round_days(days):
        integer_part = int(days)
        decimal_part = days - integer_part
    
        if 0 < decimal_part <= 0.5:
            return integer_part + 0.5
        elif 0.5 < decimal_part < 1:
            return integer_part + 1
        else:
            return integer_part

    @staticmethod
    def calculate_days(df):
        """Estimate the number of days for trips."""
        base_days = ((df['distance']) / 50) / 11
        df['days'] = base_days
        df['days'] = np.where(df['days'] < 1, 1, df['days'])
        df['days'] = df['days'].apply(DaysCalculator.round_days)
        return df

class FinanceCalculator:
    """Calculates vehicle cost and profit."""

    @staticmethod
    def calculate_finance(df):
        """Calculate profit based on RatePerMile and vehicle cost."""
        
        van_cost, reefer_cost, flatbed_cost = 2.15, 2.3, 2.15
        df['vcost'] = np.where(df['equip'] == 'VAN', van_cost, 
                      np.where(df['equip'] == 'REEFER', reefer_cost, flatbed_cost))
        
        df['cost'] = df['vcost'] * df['distance']
        df['profit'] = df['income'] - df['cost']
        
        df = df.drop(columns=['vcost'])
        return df

@st.cache_resource(ttl=84600, show_spinner="Consulting API...")
def get_raw_client(date_range):
    
    start_date = date_range[0].strftime("%Y-%m-%d")
    end_date = date_range[1].strftime("%Y-%m-%d")
    
    conn = st.connection("sql")
    
    sql_query = f"""
                SELECT
                    c.load_reference_id as id,
                    c.load_posted_date AS start_date,
                    c.load_broker_shipper AS broker_shipper,
                    c.dispatcher_user,
                    c.load_equip_type AS equip,
                    c.load_origin_state as state_origin,
                    c.load_destination_state as state_destination,
                    ROUND(c.load_distance, 0) AS distance,
                    ROUND(c.load_rate_total, 0) AS income
                FROM
                    APL_History_staging.loads c
                WHERE
                    c.load_posted_date >= '{start_date}' 
                    AND c.load_posted_date <= '{end_date}'
                ORDER BY
                    start_date;
            """
            
    print(sql_query)

    df = conn.query(sql_query)
    df = FinanceCalculator.calculate_finance(df)
    df = DaysCalculator.calculate_days(df)
    
    for var in ['income', 'profit', 'cost']:
        
        df[f'{var}_dist'] = df[var] / df['distance']
        df[f'{var}_day'] = df[var] / df['days']
        df = df.round({f'{var}_dist': 2, f'{var}_day': 0})
    
    return df


@st.cache_resource(ttl=84600, show_spinner="Consulting API...")
def get_company_history(date_range):
    
    url = "https://fjz7bfmml2.execute-api.us-east-1.amazonaws.com/dev/company_history"
    apikey = get_apikey()

    start_date = dt.datetime.combine(date_range[0], dt.datetime.min.time())
    end_date = dt.datetime.combine(date_range[1], dt.datetime.min.time())
    start_date = int(start_date.timestamp())
    end_date = int(end_date.timestamp())

    truck_types = ['REF', 'DRY', 'FLT']
    
    headers = {
        'authorizationToken': token,
        'Content-Type': 'application/json'
    }

    def fetch_data(equip):
        params = {
            "origin": {
                "country": "USA",
                "mode": "country"
            },
            "destination": {
                "country": "USA",
                "mode": "country"
            },
            "truck_types": [equip],  # Se usa la variable `equip`
            "pickup_start": start_date,
            "pickup_end": end_date
        }

        session = requests.Session()
        session.headers.update(headers)
        response = session.post(url, json=params)

        if response.status_code == 200:
            data = json.loads(response.text)
            return pd.DataFrame(data['loads'])
        else:
            print(f"Error {response.status_code} para {equip}: {response.text}")
            return pd.DataFrame()

    # Ejecutar en paralelo con ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(fetch_data, truck_types))

    df_full = pd.concat(results, ignore_index=True)
    
    df_full = df_full[['posted', 'brokerShipper', 'dispatcherUser', 'equip', 'stateOrigin', 'stateDestination', 'distance', 'rateTotal']]
    df_full = df_full.rename(columns={'posted': 'start_date', 'brokerShipper': 'broker_shipper', 'dispatcherUser': 'dispatcher_user', 'equip': 'equip', 'stateOrigin': 'origin', 'stateDestination': 'destination', 'distance': 'distance', 'rateTotal': 'income'})

    df_full = df_full.query("origin != destination")
    df_full['start_date'] = pd.to_datetime(df_full['start_date'])
    df_full = FinanceCalculator.calculate_finance(df_full)
    df_full = DaysCalculator.calculate_days(df_full)
    
    for var in ['income', 'profit', 'cost']:
        
        df_full[f'{var}_dist'] = df_full[var] / df_full['distance']
        df_full[f'{var}_day'] = df_full[var] / df_full['days']
        df_full = df_full.round({f'{var}_dist': 2, f'{var}_day': 0})
    
    return df_full

@st.cache_resource(ttl=84600, show_spinner="Consulting API...")
def get_indicators(date_range):
    
    url = 'https://qisxbxcvh8.execute-api.us-east-1.amazonaws.com/dev/get-indicators'
    apikey = get_apikey()
    
    start_date = date_range[0].strftime("%Y-%m-%d")
    end_date = date_range[1].strftime("%Y-%m-%d")
    
    params = {
    "lanes": [
        {
        "resolution": "STATE",
        "vehicle": "REEFER",
        "indicator": "business_data_ind",
        "destination": "USA",
        "destination_alias": "USA",
        "start_date":  start_date,
        "end_date": end_date
        },
        {
        "resolution": "STATE",
        "vehicle": "VAN",
        "indicator": "business_data_ind",
        "destination": "USA",
        "destination_alias": "USA",
        "start_date":  start_date,
        "end_date": end_date
        },
        {
        "resolution": "STATE",
        "vehicle": "FLATBED",
        "indicator": "business_data_ind",
        "destination": "USA",
        "destination_alias": "USA",
        "start_date":  start_date,
        "end_date": end_date
        },
        {
        "origin": "USA",
        "destination": "ALL_STATES",
        "vehicle": "REEFER",
        "indicator": "business_data_ind",
        "start_date":  start_date,
        "end_date": end_date,
        "origin_alias": "USA",
        "destination_alias": "ALL_STATES"
        },
        {
        "origin": "USA",
        "destination": "ALL_STATES",
        "vehicle": "VAN",
        "indicator": "business_data_ind",
        "start_date":  start_date,
        "end_date": end_date,
        "origin_alias": "USA",
        "destination_alias": "ALL_STATES"
        },
        {
        "origin": "USA",
        "destination": "ALL_STATES",
        "vehicle": "FLATBED",
        "indicator": "business_data_ind",
        "start_date":  start_date,
        "end_date": end_date,
        "origin_alias": "USA",
        "destination_alias": "ALL_STATES"
        }
    ],
    "aggregates": {
        "average": False,
        "dayweek": False,
        "sum": False
    }
    }

    headers = {
        'authorizationToken': apikey,
        'Content-Type': 'application/json'
    }

    session = requests.Session()
    session.headers.update(headers)
    response = session.post(url, json=params)

    data = json.loads(response.text)
    df = pd.DataFrame(data)
    df = df.rename(columns={'vehicle': 'equip', 'dist':'distance'})
    
    df = get_resolution(df, 'origin').rename(columns={'resolution':'res_origin'})
    df = get_resolution(df, 'destination').rename(columns={'resolution':'res_destination'})
    
    return df


def fetch_data(url, params):
    response = requests.get(url, params=params)
    return response.json()

@st.cache_resource(ttl=84600, show_spinner="Consulting API...")
def get_api_data(equips, date_range, freq):
    
    f = dic.fp_frequency[freq.lower()]
    
    urls = [
    "http://localhost:5000/get_loads_agg",
    "http://localhost:5000/get_loads_agg",
    "http://localhost:5000/get_loads_agg",
    "http://localhost:5000/get_loads_agg",
    "http://localhost:5000/get_loads_agg",
    "http://localhost:5000/get_loads_agg",
    "http://localhost:5000/get_maps_ind",
    "http://localhost:5000/get_maps_ind"
    ]


    param_list = [
        {"type_trip": 'outbound', "equips": equips, "start_date": date_range[0].strftime("%Y-%m-%d"),
         "end_date": date_range[1].strftime("%Y-%m-%d"), "frequency": f, "add_disp": 'true', "add_eq": 'false'},
        {"type_trip": 'inbound', "equips": equips, "start_date": date_range[0].strftime("%Y-%m-%d"),
         "end_date": date_range[1].strftime("%Y-%m-%d"), "frequency": f, "add_disp": 'true', "add_eq": 'false'},
        {"type_trip": 'outbound', "equips": 'VAN;REEFER;FLATBED', "start_date": date_range[0].strftime("%Y-%m-%d"),
         "end_date": date_range[1].strftime("%Y-%m-%d"), "frequency": f, "add_disp": 'false', "add_eq": 'true'},
        {"type_trip": 'inbound', "equips": 'VAN;REEFER;FLATBED', "start_date": date_range[0].strftime("%Y-%m-%d"),
         "end_date": date_range[1].strftime("%Y-%m-%d"), "frequency": f, "add_disp": 'false', "add_eq": 'true'},
        {"type_trip": 'outbound', "equips": equips, "start_date": date_range[0].strftime("%Y-%m-%d"),
         "end_date": date_range[1].strftime("%Y-%m-%d"), "frequency": f, "add_disp": 'false', "add_eq": 'false'},
        {"type_trip": 'inbound', "equips": equips, "start_date": date_range[0].strftime("%Y-%m-%d"),
         "end_date": date_range[1].strftime("%Y-%m-%d"), "frequency": f, "add_disp": 'false', "add_eq": 'false'},
        {"equips": equips, "resolution_org": 'STATE', "resolution_dest": 'COUNTRY',
         "start_date": date_range[0].strftime("%Y-%m-%d"), "end_date": date_range[1].strftime("%Y-%m-%d"), "frequency": f},
        {"equips": equips, "resolution_org": 'COUNTRY', "resolution_dest": 'STATE',
         "start_date": date_range[0].strftime("%Y-%m-%d"), "end_date": date_range[1].strftime("%Y-%m-%d"), "frequency": f}
    ]

    responses = [None] * len(urls)  # Lista para almacenar respuestas en orden

    # Ejecutar las solicitudes en paralelo
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_index = {executor.submit(fetch_data, url, params): i for i, (url, params) in enumerate(zip(urls, param_list))}
        
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                responses[index] = future.result()
            except Exception as e:
                responses[index] = f"Error: {e}"

    return responses

@st.cache_resource(ttl=84600, show_spinner="Fetching data from Database...")
def get_data_state_map(response_c, response_i=None):

    data = pd.DataFrame()
    if len(response_c.get('data', {})) > 0:
        data_c = pd.DataFrame(response_c['data'])

        if response_i == None:
            data = data_c
        else:
            
            data_i = pd.DataFrame(response_i['data'])
            data = pd.merge(data_c, data_i, on=['origin', 'destination', 'start_date', 'broker_shipper'], 
                            how='outer', suffixes=('', '_i'))
            
        data['start_date'] = pd.to_datetime(data['start_date'])

    return data

@st.cache_resource(ttl=84600, show_spinner="Grouping  data...")
def agg_data(data_init, freq, col_value, col_agg_type):
    
    data_init['start_date'] = pd.to_datetime(data_init['start_date'])
    min_date = min(data_init['start_date'])
    # data_init[f'{col_value}_i'] = np.where(data_init['source'].notnull() & data_init['source_i'].notnull(), data_init[f'{col_value}_i'] - data_init[f'{col_value}'], data_init[f'{col_value}_i'])
    
    if freq == 'Total':
        data = data_init.groupby(['origin', 'destination', 'source', 'source_i']).agg(
            income=('income', 'sum'),
            profit=('profit', 'sum'),
            cost=('cost', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            income_i=('income_i', 'sum'),
            profit_i=('profit_i', 'sum'),
            cost_i=('cost_i', 'sum'),
            distance_i=('distance_i', 'sum'),
            days_i=('days_i', 'sum')
            
        ).reset_index()
        data['start_date'] = min_date #Colocar aca la fecha minima
    elif freq == 'Daily':
        data_init['day_of_week'] = data_init['start_date'].dt.day_name()
        data = data_init.groupby(['origin', 'destination', 'source', 'day_of_week']).agg(
            income=('income', 'sum'),
            profit=('profit', 'sum'),
            cost=('cost', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            income_i=('income_i', 'sum'),
            profit_i=('profit_i', 'sum'),
            cost_i=('cost_i', 'sum'),
            distance_i=('distance_i', 'sum'),
            days_i=('days_i', 'sum')
        ).reset_index()
        
        data = data.rename(columns={'day_of_week': 'start_date'})
        data = data.set_index('start_date')
        valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        existing_days = data.index.intersection(valid_days)

        data = data.loc[existing_days].reset_index()
    else:
        data = data_init.groupby(['origin', 'destination', 'start_date', 'source', 'source_i']).agg(
            income=('income', 'sum'),
            profit=('profit', 'sum'),
            cost=('cost', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            income_i=('income_i', 'sum'),
            profit_i=('profit_i', 'sum'),
            cost_i=('cost_i', 'sum'),
            distance_i=('distance_i', 'sum'),
            days_i=('days_i', 'sum')
            
        ).reset_index()
        data = data.sort_values(by='start_date').reset_index(drop=True)
        data['start_date'] = data['start_date'].dt.strftime('%b %Y')
    
    # data['income'] = abs(data['income'])
    # data['income_i'] = abs(data['income_i'])

    if col_agg_type != '':
        value_round =  2 if col_agg_type == 'distance' else 0
        for var in ['profit', 'income', 'cost']:
            data[var] = data[var] / data[col_agg_type]
            data[f'{var}_i'] = data[f'{var}_i'] / data[f'{col_agg_type}_i']
    
            data = data.round({var: value_round, f'{var}_i': value_round})
    
    data[f'{col_value}_ratio'] = (data[f'{col_value}'] / data[f'{col_value}_i'])
    data[f'{col_value}_diff'] = data[f'{col_value}'] - data[f'{col_value}_i']
    data = data.round({f'{col_value}_ratio': 2, f'{col_value}_diff': 2})
    

    return  data

@st.cache_resource(ttl=84600, show_spinner="Grouping  data...")
def io_states_map(data_in, data_out, col_value, freq, col_agg_type):

    data_in = agg_data(data_in, freq, col_value, col_agg_type)
    data_out = agg_data(data_out, freq, col_value, col_agg_type)

    data_in_out = pd.merge(data_in, data_out,
                            left_on=['destination', 'start_date'],
                            right_on=['origin', 'start_date'], 
                            how='inner', suffixes=('-in', '-out'))


    data_in_out['destination-in'] = data_in_out['destination-in'].fillna(data_in_out['origin-out'])
    data_in_out = data_in_out.drop(columns=['source-in', 'source_i-in', 'source-out', 'source_i-out'])
    data_in_out = data_in_out.fillna(0)

    data_in_out = data_in_out.drop(columns=['origin-in', 'origin-out', 'destination-out']).rename(columns={'destination-in':'destination'})
    data_in_out['origin'] = data_in_out['destination']
    
    if col_value != 'profit':   
        data_in_out[f"{col_value}_io"] = (data_in_out[f"{col_value}-in"]/data_in_out[f"{col_value}-out"])
    else:
        data_in_out[f"{col_value}_io"] = (data_in_out[f"{col_value}-in"]+data_in_out[f"{col_value}-out"])
        

    return data_in_out

@st.cache_resource(ttl=84600, show_spinner="Classifying brokers...")
def classify_brokers(df):
    # Calcular umbrales
    income_threshold = df["income"].median()
    avb_threshold = df.loc[df["income"] >= income_threshold, "avb"].mean()
    avb_i_threshold = df.loc[(df["income"] >= income_threshold) & (df["avb"] <= avb_threshold), "avb_i"].mean()

    # Identificar brokers "Potencial"
    brok_pot = df.loc[
        (df["income"] >= income_threshold) & 
        (df["avb"] <= avb_threshold) & 
        (df["avb_i"] >= avb_i_threshold),
        "broker_shipper"
    ].tolist()

    # Excluir brokers "Potencial" y recalcular umbrales para "Good"
    remaining_df = df[~df["broker_shipper"].isin(brok_pot)]
    avb_threshold_good = remaining_df.loc[remaining_df["income"] >= income_threshold, "avb"].mean()

    # Identificar brokers "Good"
    brok_good = remaining_df.loc[
        (remaining_df["income"] >= income_threshold) & 
        (remaining_df["avb"] >= avb_threshold_good),
        "broker_shipper"
    ].tolist()

    # Asignar categorías
    df["category"] = "bad"  # Categoría por defecto
    df.loc[df["broker_shipper"].isin(brok_pot), "category"] = "potencial"
    df.loc[df["broker_shipper"].isin(brok_good), "category"] = "good"

    return df

@st.cache_resource(ttl=84600, show_spinner="Grouping  data...")
def agg_data_brk(data, freq, col_value, col_agg_type, broker=[], agg_loct=False, date=[], add_brok=True):
    
    data = data.query("income.notna()")
    min_date = min(data['start_date'])
    data = data.fillna(0)
    
    if len(broker) > 0:
        data = data.query('broker_shipper in @broker') if len(broker) > 0 else data
    if len(date) > 0:
        data = data.query('start_date in @date') if len(date) > 0 else data
        
    agg_cols = ['broker_shipper'] if add_brok else []
        
    if agg_loct:
        data['origin'] = 'USA'
        data['destination'] = 'USA'
                
    data['start_date'] = pd.to_datetime(data['start_date'])
    if freq == 'Total': 
        data = data.groupby(['origin', 'destination', 'source', 'source_i', 'lat_org', 'lng_org', 'lat_dest', 'lng_dest'] + agg_cols).agg(
            avb=('avb', 'sum'),
            income=('income', 'sum'),
            profit=('profit', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            avb_i=('avb_i', 'sum'),
            income_i=('income_i', 'sum'),
            profit_i=('profit_i', 'sum'),
            distance_i=('distance_i', 'sum'),
            days_i=('days_i', 'sum')
            
        ).reset_index()
        data['start_date'] = min_date
    elif freq == 'Daily':
        data['day_of_week'] = data['start_date'].dt.day_name()
        data = data.groupby(['origin', 'destination', 'source', 'lat_org', 'lng_org', 'lat_dest', 'lng_dest', 'day_of_week'] + agg_cols).agg(
            avb=('avb', 'sum'),
            avb_i=('avb_i', 'sum'),
            income=('income', 'sum'),
            profit=('profit', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum')
        ).reset_index()
        
        data = data.rename(columns={'day_of_week': 'start_date'})
        data = data.set_index('start_date')
        data = data.loc[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']].reset_index()
    else:
        data = data.groupby(['origin', 'destination', 'start_date', 'source', 'source_i', 'lat_org', 'lng_org', 'lat_dest', 'lng_dest'] + agg_cols).agg(
            avb=('avb', 'sum'),
            income=('income', 'sum'),
            profit=('profit', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            avb_i=('avb_i', 'sum'),
            income_i=('income_i', 'sum'),
            profit_i=('profit_i', 'sum'),
            distance_i=('distance_i', 'sum'),
            days_i=('days_i', 'sum')
            
        ).reset_index()
        data = data.sort_values(by='start_date').reset_index(drop=True)
        data['start_date'] = data['start_date'].dt.strftime('%b %Y')

    data['cost'] = data['income'] - data['profit']
    data['cost_i'] = data['income_i'] - data['profit_i']
        
    if col_agg_type != '':
        data[col_value] = data[col_value] / data[col_agg_type]
        data[f'{col_value}_i'] = data[f'{col_value}_i'] / data[f'{col_agg_type}_i']
    
    value_round =  2 if col_agg_type == 'distance' else 0
    data = data.round({col_value: value_round, f'{col_value}_i': value_round})

    return  data

@st.cache_resource(ttl=84600, show_spinner="Grouping  data...")
def get_comparision_brok(data, freq, col_value, col_agg_type, broker_select):
        
    data_f = agg_data_brk(data, freq, col_value, col_agg_type, add_brok=False)
    data_b = agg_data_brk(data, freq, col_value, col_agg_type, broker_select, add_brok=False)
    
    df_agg = pd.merge(data_b, data_f, on=['origin', 'destination', 'start_date'], 
                    how='left', suffixes=('-e', '-a'))
    
    df_agg[f'{col_value}_ratio-ceie'] = (df_agg[f'{col_value}-e'] / df_agg[f'{col_value}_i-e'])
    df_agg[f'{col_value}_diff-ceie'] = df_agg[f'{col_value}-e'] - df_agg[f'{col_value}_i-e']
    
    df_agg[f'{col_value}_ratio-ceca'] = (df_agg[f'{col_value}-e'] / df_agg[f'{col_value}-a'])
    df_agg[f'{col_value}_diff-ceca'] = df_agg[f'{col_value}-e'] - df_agg[f'{col_value}-a']
    
    df_agg[f'{col_value}_ratio-ceia'] = (df_agg[f'{col_value}-e'] / df_agg[f'{col_value}_i-a'])
    df_agg[f'{col_value}_diff-ceia'] = df_agg[f'{col_value}-e'] - df_agg[f'{col_value}_i-a']
    
    return df_agg

@st.cache_resource(ttl=84600, show_spinner="Grouping  data...")
def agg_data_dp(data, freq, col_value, col_agg_type, broker=[], agg_loct=False, date=[], add_brok=True):
    
    data = data.query("income.notna()")
    min_date = min(data['start_date'])
    
    if len(broker) > 0:
        data = data.query('dispatcher in @broker') if len(broker) > 0 else data
    if len(date) > 0:
        data = data.query('start_date in @date') if len(date) > 0 else data
        
    agg_cols = ['dispatcher'] if add_brok else []
        
    if agg_loct:
        data['origin'] = 'USA'
        data['destination'] = 'USA'
                
    data['start_date'] = pd.to_datetime(data['start_date'])
    if freq == 'Total': 
        data = data.groupby(['origin', 'destination', 'source', 'lat_org', 'lng_org', 'lat_dest', 'lng_dest'] + agg_cols).agg(
            avb=('avb', 'sum'),
            income=('income', 'sum'),
            profit=('profit', 'sum'),
            cost=('cost', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            
        ).reset_index()
        data['start_date'] = min_date
    elif freq == 'Daily':
        data['day_of_week'] = data['start_date'].dt.day_name()
        data = data.groupby(['origin', 'destination', 'source', 'lat_org', 'lng_org', 'lat_dest', 'lng_dest', 'day_of_week'] + agg_cols).agg(
            avb=('avb', 'sum'),
            income=('income', 'sum'),
            cost=('cost', 'sum'),
            profit=('profit', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum')
        ).reset_index()
        
        data = data.rename(columns={'day_of_week': 'start_date'})
        data = data.set_index('start_date')
        data = data.loc[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']].reset_index()
    else:
        data = data.groupby(['origin', 'destination', 'start_date', 'source', 'lat_org', 'lng_org', 'lat_dest', 'lng_dest'] + agg_cols).agg(
            avb=('avb', 'sum'),
            income=('income', 'sum'),
            cost=('cost', 'sum'),
            profit=('profit', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            
        ).reset_index()
        data = data.sort_values(by='start_date').reset_index(drop=True)
        data['start_date'] = data['start_date'].dt.strftime('%b %Y')

    if col_agg_type != '':
        data[col_value] = data[col_value] / data[col_agg_type]

    value_round =  2 if col_agg_type == 'distance' else 0
    data = data.round({col_value: value_round, f'{col_value}_i': value_round})

    return  data

@st.cache_resource(ttl=84600, show_spinner="Grouping  data...")
def get_comparision_dp(data, data_dp, freq, col_value, col_agg_type, broker_select):
        
    data_b = agg_data_dp(data_dp, freq, col_value, col_agg_type, broker_select, add_brok=False)
    data_f = agg_data_brk(data, freq, col_value, col_agg_type, add_brok=False)
    
    df_agg = pd.merge(data_b, data_f, on=['origin', 'destination', 'start_date'], 
                    how='left', suffixes=('-e', '-a'))
    
    df_agg[f'{col_value}_ratio-ceca'] = (df_agg[f'{col_value}-e'] / df_agg[f'{col_value}-a'])
    df_agg[f'{col_value}_diff-ceca'] = df_agg[f'{col_value}-e'] - df_agg[f'{col_value}-a']
    
    df_agg[f'{col_value}_ratio-ceia'] = (df_agg[f'{col_value}-e'] / df_agg[f'{col_value}_i'])
    df_agg[f'{col_value}_diff-ceia'] = df_agg[f'{col_value}-e'] - df_agg[f'{col_value}_i']
    
    return df_agg


@st.cache_resource(ttl=84600, show_spinner="Grouping  data...")
def agg_data_eq(data, freq, col_value, col_agg_type, broker=[], agg_loct=False, date=[], add_brok=True):
    
    data = data.query("income.notna()")
    min_date = min(data['start_date'])
    
    if len(broker) > 0:
        data = data.query('equip in @broker') if len(broker) > 0 else data
    if len(date) > 0:
        data = data.query('start_date in @date') if len(date) > 0 else data
        
    agg_cols = ['equip'] if add_brok else []
        
    if agg_loct:
        data['origin'] = 'USA'
        data['destination'] = 'USA'
                
    data['start_date'] = pd.to_datetime(data['start_date'])
    if freq == 'Total': 
        data = data.groupby(['origin', 'destination', 'source', 'lat_org', 'lng_org', 'lat_dest', 'lng_dest'] + agg_cols).agg(
            avb=('avb', 'sum'),
            income=('income', 'sum'),
            profit=('profit', 'sum'),
            cost=('cost', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            
        ).reset_index()
        data['start_date'] = min_date
    elif freq == 'Daily':
        data['day_of_week'] = data['start_date'].dt.day_name()
        data = data.groupby(['origin', 'destination', 'source', 'lat_org', 'lng_org', 'lat_dest', 'lng_dest', 'day_of_week'] + agg_cols).agg(
            avb=('avb', 'sum'),
            income=('income', 'sum'),
            cost=('cost', 'sum'),
            profit=('profit', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum')
        ).reset_index()
        
        data = data.rename(columns={'day_of_week': 'start_date'})
        data = data.set_index('start_date')
        data = data.loc[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']].reset_index()
    else:
        data = data.groupby(['origin', 'destination', 'start_date', 'source', 'lat_org', 'lng_org', 'lat_dest', 'lng_dest'] + agg_cols).agg(
            avb=('avb', 'sum'),
            income=('income', 'sum'),
            cost=('cost', 'sum'),
            profit=('profit', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            
        ).reset_index()
        data = data.sort_values(by='start_date').reset_index(drop=True)
        data['start_date'] = data['start_date'].dt.strftime('%b %Y')

    if col_agg_type != '':
        data[col_value] = data[col_value] / data[col_agg_type]

    value_round =  2 if col_agg_type == 'distance' else 0
    data = data.round({col_value: value_round, f'{col_value}_i': value_round})

    return  data

@st.cache_resource(ttl=84600, show_spinner="Grouping  data...")
def get_comparision_eq(data, data_dp, freq, col_value, col_agg_type, broker_select):
        
    data_b = agg_data_eq(data_dp, freq, col_value, col_agg_type, broker_select, add_brok=False)
    data_f = agg_data_brk(data, freq, col_value, col_agg_type, add_brok=False)
    
    df_agg = pd.merge(data_b, data_f, on=['origin', 'destination', 'start_date'], 
                    how='left', suffixes=('-e', '-a'))

    
    df_agg[f'{col_value}_ratio-ceca'] = (df_agg[f'{col_value}-e'] / df_agg[f'{col_value}-a'])
    df_agg[f'{col_value}_diff-ceca'] = df_agg[f'{col_value}-e'] - df_agg[f'{col_value}-a']
    
    df_agg[f'{col_value}_ratio-ceia'] = (df_agg[f'{col_value}-e'] / df_agg[f'{col_value}_i'])
    df_agg[f'{col_value}_diff-ceia'] = df_agg[f'{col_value}-e'] - df_agg[f'{col_value}_i']
    
    return df_agg


@st.cache_resource(ttl=84600, show_spinner="Grouping  data...")
def agg_data_eq(data, freq, col_value, col_agg_type, broker=[], agg_loct=False, date=[], add_brok=True):
    
    data = data.query("income.notna()")
    min_date = min(data['start_date'])
    
    if len(broker) > 0:
        data = data.query('equip in @broker') if len(broker) > 0 else data
    if len(date) > 0:
        data = data.query('start_date in @date') if len(date) > 0 else data
        
    agg_cols = ['equip'] if add_brok else []
        
    if agg_loct:
        data['origin'] = 'USA'
        data['destination'] = 'USA'
                
    data['start_date'] = pd.to_datetime(data['start_date'])
    if freq == 'Total': 
        data = data.groupby(['origin', 'destination', 'source', 'lat_org', 'lng_org', 'lat_dest', 'lng_dest'] + agg_cols).agg(
            avb=('avb', 'sum'),
            income=('income', 'sum'),
            profit=('profit', 'sum'),
            cost=('cost', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            
        ).reset_index()
        data['start_date'] = min_date
    elif freq == 'Daily':
        data['day_of_week'] = data['start_date'].dt.day_name()
        data = data.groupby(['origin', 'destination', 'source', 'lat_org', 'lng_org', 'lat_dest', 'lng_dest', 'day_of_week'] + agg_cols).agg(
            avb=('avb', 'sum'),
            income=('income', 'sum'),
            cost=('cost', 'sum'),
            profit=('profit', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum')
        ).reset_index()
        
        data = data.rename(columns={'day_of_week': 'start_date'})
        data = data.set_index('start_date')
        data = data.loc[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']].reset_index()
    else:
        data = data.groupby(['origin', 'destination', 'start_date', 'source', 'lat_org', 'lng_org', 'lat_dest', 'lng_dest'] + agg_cols).agg(
            avb=('avb', 'sum'),
            income=('income', 'sum'),
            cost=('cost', 'sum'),
            profit=('profit', 'sum'),
            distance=('distance', 'sum'),
            days=('days', 'sum'),
            
        ).reset_index()
        data = data.sort_values(by='start_date').reset_index(drop=True)
        data['start_date'] = data['start_date'].dt.strftime('%b %Y')

    if col_agg_type != '':
        data[col_value] = data[col_value] / data[col_agg_type]

    value_round =  2 if col_agg_type == 'distance' else 0
    data = data.round({col_value: value_round, f'{col_value}_i': value_round})

    return  data

