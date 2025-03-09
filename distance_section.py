import pandas as pd
import numpy as np
import streamlit as st
import services.data_service as data_service
import services.ui_service as ui_service
import services.plot_service as plot_service
import utils.graphs as grp
import warnings
warnings.filterwarnings("ignore")

def app():
    
    # Obtener datos de la sesión
    date_range, freq = st.session_state['date_range'], st.session_state['freq']
    f = ui_service.get_frequency(freq)
    
    # UI para seleccionar filtros
    type_trip, variable, agg_type, col_value_g, col_agg_type, col_value = ui_service.render_filters(plus_tt=['Relationship In/Out'])
    equip = st.radio("Select Equip:", options=['REEFER', 'VAN', 'FLATBED'], horizontal=True)
    round_value = 0 if col_agg_type == 'days' else 2
    
    df, df_ind = data_service.load_data(date_range)
    
    col_state = 'destination' if type_trip == 'Inbound' else 'origin'
    col_ostate = 'origin' if type_trip == 'Inbound' else 'destination'
    states = sorted(list(df[col_state].unique()))
    state = st.selectbox("Select States", states)
    
    # Filtrar datos por estado y equipo seleccionado
    df_filtered = data_service.filter_by_state(df, state, col_state)
    df_filtered = data_service.filter_by_equip(df_filtered, equip)

    df_agg = data_service.aggregate_data_distance(df_filtered, col_ostate, f, freq, col_value, col_value_g, col_agg_type)
    df_agg[col_value] = df_agg[col_value_g] / df_agg[col_agg_type]

    bx_days = plot_service.generate_days_boxplot(df_filtered, col_value, variable, agg_type)
    st.plotly_chart(bx_days, use_container_width=True)
    st.divider()

    var_order = st.radio("**Select variable to plot:**", options=[f"{variable} {agg_type}", 'Time', f'KPI Interaction'], horizontal=True)
    round_value = 2 if agg_type == 'Per Mile' else 0
    
    map_distance = plot_service.generate_distance_maps(var_order, df_agg, col_value, col_agg_type, col_ostate, variable, agg_type, state)
    ui_service.render_distance_maps(map_distance)   
    