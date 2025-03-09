import streamlit as st
import services.data_service as data_service
import services.ui_service as ui_service
import services.plot_service as plot_service
import utils.constants as c
import utils.graphs as grp
import warnings
warnings.filterwarnings("ignore")
       
def app():
    
    # Obtener datos de la sesión
    date_range, freq = st.session_state['date_range'], st.session_state['freq']
    f = ui_service.get_frequency(freq)
    
    # UI para seleccionar filtros
    type_trip, variable, agg_type, col_value_g, col_agg_type, col_value = ui_service.render_filters(plus_aggt=['Total'])
    equip = st.radio("**Select Equip**", options=['REEFER', 'VAN', 'FLATBED'], horizontal=True)
    round_value = 0 if col_agg_type == 'days' else 2
    
    # Cargar datos
    df, df_ind = data_service.load_data(date_range)
    df, df_ind_filt, col_state = data_service.filter_data(df, df_ind, type_trip)

    # Filtrar datos por equipo seleccionado
    df_eq = data_service.filter_by_equip(df, equip)
    df_ind_eq = data_service.filter_by_equip(df_ind_filt, equip)
    
    brk_bx, brk_full = data_service.get_top_categories(df_eq, col_value, 'broker_shipper')
    
    st.header(f"Total Brokers/Shippers: {len(brk_full)}")
    
    if len(brk_bx) > 0:
        ui_service.render_boxplot_cat(df_eq, 'broker_shipper', brk_bx, col_value, variable, agg_type, 'Broker/Shipper')

    # Agrupar datos clientes e industria
    df_agg, df_ind_agg = data_service.aggregate_data(df_eq, df_ind_eq, col_state, f, freq)
    
    # Agrupar datos clientes por broker
    df_agg_brk = data_service.aggregate_data_raw(df_eq, col_state, f, freq, raw_list=['broker_shipper'])
    
    # UI para brokers
    broker_select = st.selectbox("**Select Broker**", brk_full, index=0)
    
    # Filtrar datos por broker seleccionado
    df_agg_brk_filt = data_service.filter_by_cat(df_agg_brk, 'broker_shipper', broker_select)
    
    df_merged = data_service.merge_raw_agg(df_agg, df_agg_brk_filt, df_ind_agg, col_state, freq, col_value, col_value_g, col_agg_type)

    round_value = 2 if agg_type == 'Per Mile' else 0
    
    overview_map, ratio_map_bc, ratio_map_bi, diff_map_bc, diff_map_bi = plot_service.generate_state_sp_maps(df_merged, col_value, col_agg_type, col_state, variable, agg_type, round_value, 'Broker')
    
    ui_service.render_results_sp(overview_map, ratio_map_bc, ratio_map_bi, diff_map_bc, diff_map_bi, variable, agg_type, broker_select)

    

    
    