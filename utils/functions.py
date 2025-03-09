import pandas as pd
import numpy as np
import requests
import streamlit as st
import datetime as dt
import boto3
import json
import requests
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

