import utils.graphs as grp
import streamlit as st
import numpy as np
import utils.constants as c
import warnings
warnings.filterwarnings("ignore")

def generate_violin_plot(df, col_value, variable, agg_type, color_dict):
    """Genera un gráfico de violín para visualizar la distribución de valores."""
    
    df_agg = df.groupby(['equip']).agg(
            median=(col_value, 'median'),
            count=(col_value, 'nunique')).reset_index().query("count > 6").sort_values(by='median', ascending=True)
    
    equips = list(df_agg['equip'].unique())
    df = df.set_index('equip')
    df = df.loc[equips].reset_index()
    
    title = f"{variable} {agg_type} distribution by Equip"
    y_label = f"{variable} {agg_type}"
    
    keep_ticks = False if agg_type == 'Per Mile' else True
    
    return grp.get_violinplot(
        df, "equip", col_value, title, y_label, "Equip", 
        cl=None, color_dict=color_dict, keep_tick=keep_ticks
    )

def generate_map_color_dis(df_pivot, col_state, color_dict, color_col, round_value):
    """Genera un mapa con colores diferenciados por mejor equipo."""
    return grp.get_map_color_dis(df_pivot, col_state, color_col, color_dict, round_value)

def generate_map_dis_bubble(df_pivot, col_group, color_dict, color_col, color_bubble):
    """Genera un mapa con burbujas indicando la mejor elección de equipo."""
    return grp.get_map_dis_bubble(df_pivot, col_group, color_dict, color_col, color_bubble)

def generate_state_maps(df_filtered, col_value, col_agg_type, col_state, variable, agg_type):
    """Genera mapas de estados para análisis de datos del cliente y la industria."""
    round_value = 2 if agg_type == 'Per Mile' else 0
    
    ttip_aggt = [] if col_agg_type == '' else [(f"{col_agg_type}_c", f'{col_agg_type.capitalize()}', 0)]
    tooltip_client = [(f"{col_value}_c", f"<b>{variable} {agg_type}</b>", round_value)] + ttip_aggt

    color_scale = 'Reds' if variable == 'Cost' else 'ylgn'
    
    client_map = grp.get_map_states(df_filtered, f"{col_value}_c", col_state, 'start_date', f"{variable} {agg_type}", round_value, tooltip_client, color_scale=color_scale)
    
    tooltip_ratio = [
        ("ratio", f"<b>Ratio</b>", 2),
        (f"{col_value}_c", f"{variable} {agg_type} {c.client}", round_value),
        (f"{col_value}_i", f"{variable} {agg_type} Ind", round_value)
    ]
    ratio_map = grp.get_map_states_h(df_filtered, 'ratio', col_state, 'start_date', 'Ratio', 2, tooltip_ratio, f"{col_value}_c")
    
    tooltip_diff = [
        ("diff", f"<b>Difference</b>", round_value),
        (f"{col_value}_c", f"{variable} {agg_type} {c.client}", round_value),
        (f"{col_value}_i", f"{variable} {agg_type} Ind", round_value)
    ]
    diff_map = grp.get_map_states_h(df_filtered, 'diff', col_state, 'start_date', 'Difference', round_value, tooltip_diff, f"{col_value}_c")
    
    return client_map, ratio_map, diff_map

def generate_io_map(df_in_out, col_value, variable, agg_type):
    """Genera un mapa de relación In/Out basado en los datos de entrada y salida."""
    
    round_value = 2 if agg_type == 'Per Mile' else 0
    
    tooltip_io = [
        ("ratio", f"<b>Relationship In/Out</b>", 2),
        (f"{col_value}_c_in", f"{variable} {agg_type} In", round_value),
        (f"{col_value}_c_out", f"{variable} {agg_type} Out", round_value)
    ]
    
    io_map = grp.get_map_states_h(
        df_in_out, 'ratio', 'destination', 'start_date', 'Relationship', 2, tooltip_io, f"{col_value}_c_in"
    )
    
    return io_map

def generate_days_boxplot(dfr_filtered, col_value, variable, agg_type):
    """Genera un boxplot de distribución del valor por días."""
    
    with st.expander("**See BoxPlot explanation**"):
        
        text_description = f"""
        <b>Understanding the {variable} Distribution by Days</b><br>

        This box plot provides a visual representation of the <b>distribution of {variable.lower()}</b> over different operational days. 
        It helps analyze the <b>variability, consistency, and potential outliers</b> in {variable} across different time frames.<br

        <b>How to Read This Chart:</b><br>
        - The <b>Y-axis represents different days</b>, grouping {variable.lower()} distributions for each period.<br>
        - The <b>X-axis represents {variable.lower()}</b>, showing how earnings vary on different days.<br>
        - The <b>box in each row</b> represents the <b>interquartile range (IQR)</b>, meaning the middle 50% of {variable.lower()} values.<br>
        - The <b>vertical line inside the box</b> is the <b>median {variable.lower()}</b>, indicating the central tendency.<br>
        - The <b>whiskers extending from the box</b> show the <b>full range</b> of values, excluding outliers.<br>
        - The <b>individual dots</b> represent <b>outliers</b>, meaning unusually high or low daily {variable.lower()} values that deviate significantly from the rest.<br>

        <b>Key Insights You Can Extract:</b><br>
        1. <b>Which days have the most stable {variable.lower()}?</b><br>
        - Days with <b>shorter boxes and whiskers</b> indicate <b>consistent {variable.lower()} levels</b>.<br>
        - Days with <b>wider distributions</b> experience <b>high variability</b> in earnings.<br>

        2. <b>Are there days with frequent outliers?</b><br>
        - Outliers (dots outside the whiskers) suggest <b>unusually high or low {variable.lower()}</b> on specific days.<br>
        - This may indicate <b>special events, market fluctuations, or operational inefficiencies</b>.<br>

        3. <b>Are there significant {variable.lower()} differences between days?</b><br>
        - Comparing different days helps assess <b>trends in earnings</b> and identify <b>optimal operational trucking days</b>.<br>

        <b>How to Use This Information?</b><br>
        - Identify <b>which days generate the most consistent {variable.lower()}</b> and optimize operations accordingly.<br>
        - Monitor <b>days with extreme outliers</b> to investigate and address irregular {variable.lower()} spikes or drops.<br>
        - Compare <b>{variable.lower()} trends over different trucking days</b> to make data-driven business decisions.<br>

        This visualization is essential for tracking <b>financial performance over trucking days</b> and making strategic adjustments to maximize revenue. 🚛📊
        """

        st.write(text_description, unsafe_allow_html=True)
        
    dfr_filtered['days'] = np.ceil(dfr_filtered['days'])
    dfr_filtered = dfr_filtered.sort_values(by='days', ascending=True)
    dfr_filtered['days'] = dfr_filtered['days'].astype(str)
    dfr_filtered['days_col'] = dfr_filtered['days'].apply(lambda x: f"{x.split('.')[0]}-")
    
    keep_ticks = False if agg_type == 'Per Mile' else True
    
    fig = grp.get_boxplot(
        dfr_filtered, "days_col", col_value, 
        f"{variable} {agg_type} distribution by Days", 
        f"{variable} {agg_type}", "Days", 
        cl=None, keep_tick=keep_ticks
    )
    
    return fig

def generate_distance_maps(var_order, df_agg, col_value, col_agg_type, col_ostate, variable, agg_type, state):
    
    """Renderiza los mapas en función de la selección de var_order."""
    round_value = 2 if agg_type == 'Per Mile' else 0
    
    if var_order == f"{variable} {agg_type}":
        
        if variable == 'Income':
            text_overview = f"""Displays the total or daily revenue generated from trucking operations across different states for {state}.
                                    Darker green areas indicate higher income levels, while lighter shades represent lower earnings."""
        elif variable == 'Cost':
            text_overview = f"""Shows the total or daily operational costs incurred in each state for {state}.
                                Darker red indicates higher costs, while lighter shades represent lower expenses."""
        elif variable == 'Profit':
            text_overview = f"""Highlights the net earnings after subtracting costs from income in each state for {state}.
                                Green areas represent profitable regions, while red areas may indicate loss-making locations."""
        
        st.write(text_overview, unsafe_allow_html=True)
        
        tooltip_client = [
            (f"{col_value}", f"<b>{variable} {agg_type}</b>", round_value),
            (f"{col_agg_type}", f'{col_agg_type.capitalize()}', 0)
        ]
        
        color_scale = 'Reds' if variable == 'Cost' else 'ylgn'
        map = grp.get_map_states(df_agg, f"{col_value}", col_ostate, 'start_date', f"{variable} {agg_type}", round_value, tooltip_client, state, color_scale)

    elif var_order == 'Time':
        
        with st.expander("**See map explanation**"):
            
            text_description = f"""
            <b>Understanding the Truck Day Between States for {state}</b><br>

            This map visualizes the <b>time (in days) required to move freight</b> from the selected state to its destinations. 
            The color gradient represents the travel duration, helping identify <b>nearby vs. distant delivery points</b>.<br>

            <b>How to Read This Map:</b><br>
            - <b>Each state is color-coded</b> based on the number of days it takes to transport freight from the selected state.<br>
            - The legend on the right provides the <b>color reference</b> for transit times:<br>
            - <span style="color: #66FF00;"><b>Bright Green</b></span> → **1-truckday** (short-distance shipments).<br>
            - <span style="color: #CCFF00;"><b>Light Green</b></span> → **2-truckday**.<br>
            - <span style="color: #FFFF00;"><b>Yellow</b></span> → **3-truckday**.<br>
            - <span style="color: #FFAA00;"><b>Orange</b></span> → **4-truckday**.<br>
            - <span style="color: #FF5500;"><b>Dark Orange</b></span> → **5-truckday**.<br>
            - <span style="color: #FF0000;"><b>Red</b></span> → **6+ truckdays** (long-distance routes).<br>

            <b>Key Insights You Can Extract:</b><br>
            1. <b>Which states have the fastest deliveries?</b><br>
            - **Bright green states (1 day)** indicate **quick truckday** for shipments.<br>

            2. <b>Which regions require longer transit times?</b><br>
            - **Yellow, orange, and red states** highlight **longer-distance routes** where transit time is extended.<br>

            3. <b>How does distance affect operations?</b><br>
            - Identifying which routes take longer can help in **adjusting delivery schedules** and **improving logistics planning**.<br>

            <b>How to Use This Information?</b><br>
            - Optimize **dispatching strategies** by prioritizing short-haul vs. long-haul shipments.<br>
            - Adjust **pricing models** based on transit time and distance.<br>
            - Improve **efficiency by analyzing frequent routes** and their corresponding delivery times.<br>

            This visualization is essential for enhancing **route planning, delivery efficiency, and overall logistics performance**. 🚛📊
            """

            st.write(text_description, unsafe_allow_html=True)
        
        df_agg = df_agg.query(f"{col_ostate} != '{state}'")
        df_agg = df_agg.sort_values(by='days_mean', ascending=True)
        df_agg['days_mean'] = df_agg['days_mean'].astype(str)
        df_agg['days_mean'] = df_agg['days_mean'].apply(lambda x: f"{x.split('.')[0]}-")
        color_dict = {
            '1-': "#66FF00",
            '2-': "#CCFF00",
            '3-': "#FFFF00",
            '4-': "#FFAA00",
            '5-': "#FF5500",
            '6-': "#FF0000",
            '7-': "#FF0000",
            '8-': "#FF0000"
        }
        map = grp.get_map_color_hdistance(df_agg, col_ostate, 'days_mean', color_dict, state)

    else:
        
        with st.expander("**See map explanation**"):
            
            text_description = f"""
            <b>Understanding the KPI Interaction Between States</b><br>

            This map visualizes a <b>Key Performance Indicator (KPI)</b> that evaluates the efficiency of freight movement 
            from the selected state (<b>{state}</b>) to its related states. The KPI is calculated based on the <b>{variable} {agg_type}</b> and 
            the <b>truck days</b> to each state.<br><br>

            <b>How is the KPI Calculated?</b><br>
            The KPI is computed as follows:<br>
            1. The <b>{variable} {agg_type}</b> is divided by the <b>average truck days</b> to normalize efficiency.<br>
            2. The resulting values are scaled between **10 and 100**, ensuring clear visualization.<br>
            3. A <b>higher KPI</b> means **better efficiency** in terms of value per day, while a <b>lower KPI</b> suggests inefficiencies or high transit times relative to value.<br>

            <b>How to Read This Map:</b><br>
            - <b>Each state is shaded in blue</b> according to its KPI score.<br>
            - The color gradient represents the efficiency level:<br>
            - <span style="color: #003366;"><b>Dark Blue</b></span> → **High KPI (More efficient, better value per day)**.<br>
            - <span style="color: #6699CC;"><b>Medium Blue</b></span> → **Moderate KPI (Balanced efficiency)**.<br>
            - <span style="color: #D6EAF8;"><b>Light Blue</b></span> → **Low KPI (Less efficient, longer transit times relative to value)**.<br>
            - The legend on the right provides the **KPI scale**, ranging from **10 (least efficient) to 100 (most efficient)**.<br>

            <b>Key Insights You Can Extract:</b><br>
            1. <b>Which destinations have the highest efficiency?</b><br>
            - **Dark blue states** indicate **highly efficient lanes**, where the value per day is optimized.<br>

            2. <b>Which states have lower efficiency?</b><br>
            - **Lighter blue states** suggest that the transit time is relatively high compared to the {variable} {agg_type} value.<br>

            3. <b>How can this data improve logistics?</b><br>
            - By analyzing KPI trends can **prioritize more efficient routes** and **optimize scheduling strategies**.<br>

            <b>How to Use This Information?</b><br>
            - Focus on **maximizing operations** in states with **high KPI scores**.<br>
            - Investigate **low-KPI states** to find opportunities for **route optimization or cost reduction**.<br>
            - Adjust **pricing, logistics, and fleet allocation** based on KPI performance.<br>

            This visualization is essential for **evaluating operational efficiency, optimizing logistics, and improving overall profitability**. 🚛📊
            """

            st.write(text_description, unsafe_allow_html=True)

        
        tooltip_client = [
            (f"{col_value}", f"<b>{variable} {agg_type}</b>", round_value),
            (f"{col_agg_type}", f'{col_agg_type.capitalize()}', 0),
            ('comb2', 'KPI', 2)
        ]
        map = grp.get_map_states(df_agg, 'comb2', col_ostate, 'start_date', "KPI", 2, tooltip_client, state, color_scale='Blues')

    return map

def generate_pag_boxplot(df, col_value, cat_value, variable, agg_type, name_var):
    """Genera un boxplot de distribución del valor por días."""
    
    keep_ticks = False if agg_type == 'Per Mile' else True
    
    fig = grp.get_boxplot(
        df, cat_value, col_value, 
        f"{variable} {agg_type} distribution by {name_var}", 
        f"{variable} {agg_type}", name_var, 
        cl=None, keep_tick=keep_ticks
    )
    
    return fig

def generate_state_sp_maps(df_merged, col_value, col_agg_type, col_state, variable, agg_type, round_value, cat_name):
    """Genera mapas de estados para análisis de datos del cliente y la industria basado en una columna specifica."""
    
    ttip_aggt = [] if col_agg_type == '' else [(f"{col_agg_type}_b", f'{col_agg_type.capitalize()}', 0)]
    tooltip_client = [(f"{col_value}_b", f"<b>{variable} {agg_type}</b>", round_value)] + ttip_aggt
    
    color_scale = 'Reds' if variable == 'Cost' else 'ylgn'

    overview_map = grp.get_map_states(df_merged, f"{col_value}_b", col_state, 'start_date', f"{variable} {agg_type}", round_value, tooltip_client, color_scale=color_scale)

    tooltip_ratio_bc = [
        ("ratio_bc", f"<b>Ratio</b>", 2),
        (f"{col_value}_b", f"{variable} {agg_type} {cat_name}", round_value),
        (f"{col_value}_cf", f"{variable} {agg_type} {c.client}", round_value)
    ]
    ratio_map_bc = grp.get_map_states_h(df_merged, 'ratio_bc', col_state, 'start_date', 'Ratio', 2, tooltip_ratio_bc, f"{col_value}_b")

    tooltip_ratio_bi = [
        ("ratio_bi", f"<b>Ratio</b>", 2),
        (f"{col_value}_b", f"{variable} {agg_type} {cat_name}", round_value),
        (f"{col_value}", f"{variable} {agg_type} Ind", round_value)
    ]
    ratio_map_bi = grp.get_map_states_h(df_merged, 'ratio_bi', col_state, 'start_date', 'Ratio', 2, tooltip_ratio_bi, f"{col_value}_b")

    tooltip_diff_bc = [
        ("diff_bc", f"<b>Difference</b>", round_value),
        (f"{col_value}_b", f"{variable} {agg_type} {cat_name}", round_value),
        (f"{col_value}_cf", f"{variable} {agg_type} {c.client}", round_value)
    ]
    diff_map_bc = grp.get_map_states_h(df_merged, 'diff_bc', col_state, 'start_date', 'Difference', round_value, tooltip_diff_bc, f"{col_value}_b")

    tooltip_diff_bi = [
        ("diff_bi", f"<b>Difference</b>", round_value),
        (f"{col_value}_b", f"{variable} {agg_type} {cat_name}", round_value),
        (f"{col_value}", f"{variable} {agg_type} Ind", round_value)
    ]
    diff_map_bi = grp.get_map_states_h(df_merged, 'diff_bi', col_state, 'start_date', 'Difference', round_value, tooltip_diff_bi, f"{col_value}_b")

    return overview_map, ratio_map_bc, ratio_map_bi, diff_map_bc, diff_map_bi
