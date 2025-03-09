import pandas as pd
import streamlit as st
import services.data_service as data_service
import services.ui_service as ui_service
import services.plot_service as plot_service
import utils.dictionaries as dic
import warnings
warnings.filterwarnings("ignore")

def app():
    
    # Obtener datos de la sesión
    date_range, freq = st.session_state['date_range'], st.session_state['freq']
    f = ui_service.get_frequency(freq)
    
    # UI para seleccionar filtros
    type_trip, variable, agg_type, col_value_g, col_agg_type, col_value = ui_service.render_filters(plus_tt=['Relationship In/Out'],
                                                                                                    plus_aggt=['Total'])
    equip = st.radio("Select Equip:", options=['REEFER', 'VAN', 'FLATBED'], horizontal=True)
    round_value = 2 if col_agg_type == 'distance' else 0
    
    df, df_ind = data_service.load_data(date_range)
    
    ui_service.display_financial_metrics(df, equip, agg_type, round_value)

    if type_trip == 'Relationship In/Out':

        df_tt = []
        for tt in ['Inbound', 'Outbound']:
            # Cargar datos
            df, df_ind_filt, col_state = data_service.filter_data(df, df_ind, tt)

            # Procesar datos
            df_merged = data_service.process_data(df, df_ind_filt, col_state, f, freq, col_value_g, col_agg_type, col_value, round_value)
            
            # Filtrar datos por equipo seleccionado
            df_filtered = data_service.filter_by_equip(df_merged, equip)
            
            df_tt.append(df_filtered)
            
        df_in_out = pd.merge(df_tt[0], df_tt[1], left_on=['start_date', 'destination', 'equip'], right_on=['start_date', 'origin', 'equip'], suffixes=('_in', '_out'))
        df_in_out = df_in_out[['start_date', 'destination', 'equip', f'{col_value}_c_in', f'{col_value}_c_out']]
        
        if variable == 'Profit':
            df_in_out['ratio'] = df_in_out[f'{col_value}_c_in'] + df_in_out[f'{col_value}_c_out']
        else:  
            df_in_out['ratio'] = df_in_out[f'{col_value}_c_in'] / df_in_out[f'{col_value}_c_out']
        
        io_map = plot_service.generate_io_map(df_in_out, col_value, variable, agg_type)
        
        st.divider()
        st.write("<b>Relationship between the client Inbound trips and Outbound trips.</b>", unsafe_allow_html=True)
        st.plotly_chart(io_map, use_container_width=True)
        
    else:
        
        # Cargar datos
        df, df_ind_filt, col_state = data_service.filter_data(df, df_ind, type_trip)

        # Procesar datos
        df_merged = data_service.process_data(df, df_ind_filt, col_state, f, freq, col_value_g, col_agg_type, col_value, round_value)

        # Filtrar datos por equipo seleccionado
        df_filtered = data_service.filter_by_equip(df_merged, equip)

        client_map, ratio_map, diff_map = plot_service.generate_state_maps(df_filtered, col_value, col_agg_type, col_state, variable, agg_type)
        ui_service.render_results_fp(client_map, ratio_map, diff_map, variable, agg_type)