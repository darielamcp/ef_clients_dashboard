import streamlit as st
import services.data_service as data_service
import services.ui_service as ui_service
import services.plot_service as plot_service
import warnings
warnings.filterwarnings("ignore")

def app():

    # Obtener datos de la sesión
    date_range, freq = st.session_state['date_range'], st.session_state['freq']
    f = ui_service.get_frequency(freq)
    
    # UI para seleccionar filtros
    type_trip, variable, agg_type, col_value_g, col_agg_type, col_value = ui_service.render_filters()
    round_value = 0 if col_agg_type == 'days' else 2
    
    # Cargar datos
    df, df_ind = data_service.load_data(date_range)
    df, df_ind_filt, col_state = data_service.filter_data(df, df_ind, type_trip)
    
    # UI para seleccionar estado
    states = sorted(list(df[col_state].unique()))
    state = st.selectbox("**Select States**", ['ALL'] + states)
    
    # Procesar datos
    df_merged = data_service.process_data(df, df_ind_filt, col_state, f, freq, col_value_g, col_agg_type, col_value, round_value)
    df_pivot = data_service.prepare_pivot_data(df_merged, col_state, f'{col_value}', round_value)

    # Filtrar datos por estado seleccionado
    df_filtered = data_service.filter_by_state(df, state, col_state)

    # Generar gráficos
    color_dict = data_service.get_equip_color_dict()
    violin_plot = plot_service.generate_violin_plot(df_filtered, col_value, variable, agg_type, color_dict)
    map_color_dis = plot_service.generate_map_color_dis(df_pivot, col_state, color_dict, 'best_equip_c', round_value)
    map_dis_bubble = plot_service.generate_map_dis_bubble(df_pivot, col_state, color_dict, 'best_equip_r', 'equip_color_r')
    
    # Renderizar UI
    ui_service.render_results_eq(violin_plot, map_color_dis, map_dis_bubble, variable)
