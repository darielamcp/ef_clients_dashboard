import streamlit as st
import utils.constants as c
import utils.dictionaries as dic
import services.plot_service as plot_service
import warnings
warnings.filterwarnings("ignore")

def get_frequency(freq):
    """Obtiene la frecuencia de agrupación basada en el diccionario."""
    return dic.fp_frequency[freq.lower()]

def render_filters(plus_tt=[], plus_aggt=[]):
    """Renderiza los filtros de selección en la interfaz de usuario."""
    
    
    type_trip = st.selectbox("**Select Type of Trip**", ['Inbound', 'Outbound']+plus_tt)
    
    if len(plus_tt) > 0:
        st.write("""<i><b>Inbound</b></i> for shipments coming into your network.<br>
                    <i><b>Outbound</b></i> for shipments leaving your network.<br>
                    <i><b>Relationship In/Out</b></i> to compare inbound and outbound performance.
                    <hr style="margin: 5px 0; border: none; border-top: 1px solid #ddd;">""",
                    unsafe_allow_html=True)
    else:
        st.write("""<i><b>Inbound</b></i> for shipments coming into your network.<br>
                    <i><b>Outbound</b></i> for shipments leaving your network.
                    <hr style="margin: 5px 0; border: none; border-top: 1px solid #ddd;">""",
                    unsafe_allow_html=True)
        
    col1, col2 = st.columns(2)
    with col1:
        
        variable = st.selectbox("**Select Variable**", ['Income', 'Profit', 'Cost'])
        st.write("""<i><b>Income</b></i> shows total revenue generated.<br>
                <i><b>Profit</b></i> represents the net earnings after costs.<br>
                <i><b>Cost</b></i> displays total operational expenses.
                <hr style="margin: 5px 0; border: none; border-top: 1px solid #ddd;">""",
                unsafe_allow_html=True)
    with col2:
        
        agg_type = st.selectbox("**Select Aggregation Type**", plus_aggt+['Per Day', 'Per Mile'])
        
        if len(plus_aggt) > 0:
            st.write("""<i><b>Total</b></i> for cumulative values over the selected period.<br>
                    <i><b>Per Day</b></i> to analyze per truck days traveled.<br>
                    <i><b>Per Mile</b></i> to analyze per distance traveled.
                    <hr style="margin: 5px 0; border: none; border-top: 1px solid #ddd;">""",
                    unsafe_allow_html=True)
        else:
            st.write("""<i><b>Per Day</b></i> to analyze per truck days traveled.<br>
                    <i><b>Per Mile</b></i> to analyze per distance traveled.
                    <hr style="margin: 5px 0; border: none; border-top: 1px solid #ddd;">""",
                    unsafe_allow_html=True)
        
    col_value_g = dic.fp_col_value[variable.lower()]
    col_agg_type = dic.fp_agg_type[agg_type.lower()]
    col_value = dic.bs_col_value.get(f"{variable.lower()}_{agg_type.lower().replace(' ','')}")

    return type_trip, variable, agg_type, col_value_g, col_agg_type, col_value

def update_state_options(states):
    """Actualiza la lista de estados disponibles en el selectbox."""
    return st.selectbox("**Select States**", ['ALL'] + states, index=0)

def render_results_eq(violin_plot, map_color_dis, map_dis_bubble, variable):
    """Renderiza los resultados y gráficos en la interfaz de usuario."""
    
    y_label = 'Equip'
    
    with st.expander("**See violin explanation**"):
        text_description = f"""
            <b>Understanding the {variable} Distribution by Equipment</b><br>

            This <b>violin plot</b> provides a detailed view of <b>{variable.lower()} distribution</b> across different equipment types (<b>Flatbed, Reefer, and Van</b>). 
            It helps assess the <b>variability, consistency, and potential outliers</b> in {variable.lower()} margins for each type of equipment.<br>

            <b>How to Read This Chart:</b><br>
            - <b>Each row represents an equipment type</b>, showing the range of {variable.lower()}s associated with it.<br>
            - The <b>shape of the plot</b> represents the <b>distribution of {variable.lower()} values</b>, where wider areas indicate <b>more frequent {variable.lower()} values</b>.<br>
            - The <b>central box inside the plot</b> represents the <b>interquartile range (IQR)</b>, meaning the middle 50% of {variable.lower()} values.<br>
            - The <b>vertical line inside the box</b> is the <b>median {variable.lower()}</b>, indicating the central tendency.<br>
            - The <b>whiskers extending from the box</b> show the <b>full range</b> of values, excluding outliers.<br>
            - The <b>individual dots</b> represent <b>outliers</b>, meaning unusually high or low {variable.lower()} values for that equipment type.<br>

            <b>Key Insights You Can Extract:</b><br>
            1. <b>Which equipment type has the most stable {variable.lower()}s?</b><br>
            - Equipment with <b>narrower distributions</b> and <b>shorter whiskers</b> have more <b>consistent</b> {variable.lower()} margins.<br>
            - Equipment with <b>wider distributions</b> experience <b>higher variability</b> in {variable.lower()}s.<br>

            2. <b>Are there any equipment types with frequent negative profits?</b><br>
            - If an equipment type’s distribution extends <b>far into the negative values</b>, it indicates <b>frequent losses</b>.<br>

            - Equipment types with <b>dots on the far right</b> have <b>some exceptionally high-{variable.lower()} trips</b> that may need further investigation.<br>

            4. <b>How does a selected equipment type compare?</b><br>
            - This visualization helps in analyzing <b>which equipment type is performing best in terms of {variable.lower()}</b>.<br>
            """

        st.write(text_description, unsafe_allow_html=True)

    st.plotly_chart(violin_plot, use_container_width=True)
    
    tab1, tab2 = st.tabs([f"{c.client} Overview Map", f"{c.client} vs Industry Ratio"])
    
    with tab1:
        with st.expander("**See map explanation**"):
            text_overview = f"""
            This map displays the best equipment for each state based on the selected variable ({variable}). 
            Each state is <b>color-coded</b> to indicate which equipment type performed the best.<br>

            <b>How to Read This Map:</b><br>
            - <b>Each state is filled with a color</b> corresponding to the equipment type that achieved the highest value for the selected variable.<br>
            - The legend on the right provides the <b>color reference</b> for each equipment type:<br>
            - <span style="color: #00BFFF;"><b>Blue</b></span> → Reefer<br>
            - <span style="color: #8A2BE2;"><b>Purple</b></span> → Flatbed<br>
            - <span style="color: #FFD700;"><b>Yellow</b></span> → Van<br>
            
            - By hovering over a state, a tooltip shows:<br>
            - The **best-performing equipment type**.<br>
            - The **numerical values** for each equipment type in that state.<br>
            - The **selected date** for the displayed data.<br>

            <b>Key Insights You Can Extract:</b><br>
            1. <b>Which equipment type is most profitable in different regions?</b><br>
            - Identify states where **a specific equipment type consistently outperforms the others**.<br>

            2. <b>Are there regional trends?</b><br>
            - If a single color dominates multiple states, it suggests that **a particular equipment type is more efficient in those areas**.<br>

            3. <b>Where should resources be allocated?</b><br>
            - Use this data to **optimize fleet deployment** by prioritizing the most profitable equipment for each region.<br>

            <b>How to Use This Information?</b><br>
            - Select different variables (e.g., Profit, Income, Cost) to analyze which equipment type is the best for each state.<br>
            - Identify <b>regions where certain equipment types perform better</b> and adjust strategies accordingly.<br>
            - Allocate resources efficiently based on data-driven insights.<br>

            This visualization helps in making <b>strategic decisions</b> for optimizing **fleet allocation, profitability, and operational efficiency**. 🚛📊
            """

            st.write(text_overview, unsafe_allow_html=True)
        st.plotly_chart(map_color_dis, use_container_width=True)
    
    with tab2:
        with st.expander("**See map explanation**"):
            text_bubble = f"""
            <b>Understanding the Best Equipment Based on Industry Comparison</b><br>

            This map highlights the <b>equipment type with the highest industry ratio</b> in each state. 
            The industry ratio compares the client's performance against industry benchmarks, helping identify where the company is performing above or below market standards.<br>

            <b>How to Read This Map:</b><br>
            - <b>Each state is filled with a color</b> representing the equipment type that achieved the highest ratio:<br>
            - <span style="color: #00BFFF;"><b>Blue</b></span> → Reefer<br>
            - <span style="color: #8A2BE2;"><b>Purple</b></span> → Flatbed<br>
            - <span style="color: #FFD700;"><b>Yellow</b></span> → Van<br>
            - <b>Each state contains a dot indicating industry performance:</b><br>
            - <span style="color: green;"><b>Green dot</b></span> → The best equipment ratio is **greater than 1**, meaning the client is outperforming the industry.<br>
            - <span style="color: red;"><b>Red dot</b></span> → The best equipment ratio is **less than 1**, meaning the client is underperforming compared to the industry.<br>

            <b>Tooltip Information:</b><br>
            By hovering over a state, users can see:<br>
            - The **best-performing equipment type** in that state.<br>
            - The **industry ratio** for each equipment type.<br>
            - The **actual {c.client} (client performance) vs. industry benchmark**.<br>

            <b>Key Insights You Can Extract:</b><br>
            1. <b>Which equipment type has the highest market efficiency?</b><br>
            - Identify states where **a specific equipment type consistently outperforms industry standards**.<br>

            2. <b>Are there areas where the client is underperforming?</b><br>
            - States with **red dots** indicate where the company may need to improve efficiency or reconsider equipment use.<br>

            3. <b>Where should resources be allocated?</b><br>
            - Focus operations on states with **high ratios and green dots**, as they indicate **competitive advantages** over the industry.<br>

            <b>How to Use This Information?</b><br>
            - Identify **strong-performing regions** and expand operations there.<br>
            - Address underperforming states by analyzing cost structures or operational inefficiencies.<br>
            - Optimize fleet deployment based on **data-driven performance insights**.<br>

            This visualization is essential for **strategic planning, benchmarking, and operational efficiency optimization**. 🚛📊
            """

            st.write(text_bubble, unsafe_allow_html=True)

        st.plotly_chart(map_dis_bubble, use_container_width=True)
        
def render_results_fp(client_map, ratio_map, diff_map, variable, agg_type):
    """Renderiza los resultados y gráficos en la interfaz de usuario."""
    
    if variable == 'Income':
        text_overview = """Displays the total or daily revenue generated from trucking operations across different states.
                                Darker green areas indicate higher income levels, while lighter shades represent lower earnings."""
    elif variable == 'Cost':
        text_overview = """Shows the total or daily operational costs incurred in each state.
                            Darker red indicates higher costs, while lighter shades represent lower expenses."""
    elif variable == 'Profit':
        text_overview = """Highlights the net earnings after subtracting costs from income in each state.
                            Green areas represent profitable regions, while red areas may indicate loss-making locations."""
    
    text_ratio = f"""Compares the {c.client} financial performance against industry benchmarks.
                    <b>Color Interpretation:</b><br>
                    <i><b>Green Areas</b></i> → A ratio above 1.0, means {c.client} is outperforming the industry standard.<br>
                    <i><b>Yellow Areas</b></i> → A ratio as 1.0, means {c.client} performance is in line with the industry standard.<br>
                    <i><b>Red Areas</b></i> → A ratio above 1.0, below {c.client} is underperforming, meaning they are losing money compared to the industry standard."""
    
    text_diff = f"""Displays the absolute difference between the {c.client} financial metrics and industry benchmarks.<br>
                    <b>Color Interpretation:</b><br>
                    <i><b>Green Areas</b></i> → {c.client} is outperforming the industry standard.<br>
                    <i><b>Yellow Areas</b></i> → {c.client} performance is in line with the industry standard.<br>
                    <i><b>Red Areas</b></i> → {c.client} is underperforming, meaning they are losing money compared to the industry standard.
                    """
    
    if agg_type == 'Total':

        st.divider()
        st.write(text_overview, unsafe_allow_html=True)
        st.plotly_chart(client_map, use_container_width=True)
        
    else:
        
        if variable == 'Profit':
            
            tab1, tab2 = st.tabs([f"{c.client} Overview Map", f"{c.client} vs Industry Difference"])
        
            with tab1:
                st.write(text_overview, unsafe_allow_html=True)
                st.plotly_chart(client_map, use_container_width=True)
            with tab2:
                text_diff_adds = f"""<b>Label Colors (Inside Each State)</b><br>
                                    <i><b>Red Labels</b></i> → Indicate negative profit for {c.client} in that state.<br>
                                    <i><b>Blue Labels</b></i> → Indicate positive profit for {c.client} in that state."""
                                    
                st.write(text_diff, unsafe_allow_html=True)
                st.write(text_diff_adds, unsafe_allow_html=True)
                st.plotly_chart(diff_map, use_container_width=True)
        else:
            
            tab1, tab2, tab3 = st.tabs([f"{c.client} Overview Map", f"{c.client} vs Industry Ratio", f"{c.client} vs Industry Difference"])
            
            with tab1:
                st.write(text_overview, unsafe_allow_html=True)
                st.plotly_chart(client_map, use_container_width=True)
            with tab2:
                st.write(text_ratio, unsafe_allow_html=True)
                st.plotly_chart(ratio_map, use_container_width=True)
            with tab3:
                st.write(text_diff, unsafe_allow_html=True)
                st.plotly_chart(diff_map, use_container_width=True)
        
def display_financial_metrics(df, equip, agg_type, round_value):
    """Genera y muestra métricas financieras (Income, Cost, Profit) de manera optimizada."""
    
    # Obtener nombres de columnas dinámicamente
    col_i, col_c, col_p = [
        dic.bs_col_value.get(f"{metric.lower()}_{agg_type.lower().replace(' ', '')}")
        for metric in ['income', 'cost', 'profit']
    ]
    
    opt = 'sum' if agg_type == 'Total' else 'mean'
    df['aux'] = 'aux'
    df_agg = df.query("equip == @equip").groupby(['aux']).agg({col_i: opt, col_c: opt, col_p: opt}).reset_index()
    
    # Definir información de métricas
    metrics = [
        ("Income", col_i, "green"),
        ("Cost", col_c, "red"),
        ("Profit", col_p, "green" if df_agg[col_p].iloc[0] > 0 else "red")
    ]
    
    # Renderizar métricas en columnas
    cols = st.columns(3)
    for col, (label, col_val, color) in zip(cols, metrics):
        formatted_value = f"<span style='color:{color}; font-size:40px; font-weight:bold;'>$ {df_agg[col_val].iloc[0]:,.{round_value}f}</span>"
        col.markdown(f"""    
            <div style="text-align: center;">
                <span style="font-size:24px; font-weight:bold;">{label} {agg_type}</span>
                <h1>{formatted_value}</h1>
            </div>
        """, unsafe_allow_html=True)
        
def render_distance_maps(map):
    """Renderiza los mapas en función de la selección de var_order."""
    st.plotly_chart(map, use_container_width=True)
    

def render_boxplot_cat(df_full, cat_col, cat_list, col_value, variable, agg_type, y_label):
    """Renderiza los resultados y gráficos en la interfaz de usuario."""

    with st.expander("**See BoxPlot explanation**"):
        text_description = f"""
        <b>Understanding the {variable} Total Distribution by {y_label}</b><br>
        This <b>box plot</b> provides a detailed view of <b>{variable.lower()} distribution</b> across different {y_label}. 
        It helps assess the <b>variability, consistency, and potential outliers</b> in {variable.lower()} margins.<br>
        
        <b>How to Read This Chart:</b><br>
        - <b>Each row represents a {y_label}/b>, showing the range of {variable.lower()}s associated with them.<br>
        - The <b>box in each row</b> represents the <b>interquartile range (IQR)</b>, meaning the middle 50% of {variable.lower()} values.<br>
        - The <b>vertical line inside the box</b> is the <b>median {variable.lower()}</b>, indicating the central tendency.<br>
        - The <b>whiskers extending from the box</b> show the <b>full range</b> of values, excluding outliers.<br>
        - The <b>individual dots</b> represent <b>outliers</b>, meaning unusually high or low {variable.lower()} values.<br>
        
        <b>Key Insights You Can Extract:</b><br>
        1. <b>Which {y_label} have the most consistent {variable.lower()}s?</b><br>
        - {y_label} with <b>shorter boxes and whiskers</b> have more <b>stable</b> {variable.lower()} margins.<br>
        - {y_label} with <b>wide boxes</b> experience <b>high variability</b> in {variable.lower()}s.<br>
        2. <b>Are there any {y_label} with frequent negative profits?</b><br>
        - If a {y_label} distribution extends <b>far into the negative values</b>, it indicates <b>frequent losses</b>.<br>
        3. <b>Are there high-{variable.lower()} {y_label} with many outliers?</b><br>
        - {y_label} with <b>dots on the far right</b> have <b>some exceptionally high-{variable.lower()} trips</b> that may need further investigation.<br>
        4. <b>How does a selected {y_label} compare?</b><br>
        - The <b>dropdown filter</b> allows users to select a specific {y_label} and analyze their performance in detail.<br>
        
        <b>How to Use This Information?</b><br>
        - Identify <b>which {y_label} are the most profitable and stable</b> for the company.<br>
        - Spot <b>{y_label} with high risks</b> due to frequent losses or large variability.<br>
        - Compare <b>your company’s {variable.lower()} distribution</b> against industry trends.<br>
        - Use this data to <b>negotiate better terms</b> with high-performing {y_label} or reconsider partnerships with low-{variable.lower()} ones.<br>
        This visualization is essential for making <b>data-driven decisions</b> when selecting and managing {y_label}. 🚛📊
        """

        st.write(text_description, unsafe_allow_html=True)

    
    df = df_full.query(f"{cat_col} in {cat_list}")
    
    # Configuración de paginación
    items_per_page = 10  # Brokers por página
    total_pages = len(cat_list) // items_per_page

    # Estado de la página en Streamlit
    if "page_number" not in st.session_state:
        st.session_state.page_number = 0

    # Cálculo del índice de paginación
    start_idx = st.session_state.page_number * items_per_page
    end_idx = start_idx + items_per_page
    brokers_paginados = cat_list[start_idx:end_idx]

    # Filtrar el dataframe para la página actual
    df_paginado = df[df[cat_col].isin(brokers_paginados)]
    
    df_agg = df_paginado.groupby([cat_col]).agg(
            median=(col_value, 'median'),
            count=(col_value, 'nunique')).reset_index().sort_values(by='median', ascending=True)

    brk = list(df_agg[cat_col].unique())
    
    df_paginado = df_paginado.set_index(cat_col)
    df_paginado = df_paginado.loc[brk].reset_index()

    fig = plot_service.generate_pag_boxplot(df_paginado, col_value, cat_col, variable, agg_type, y_label)
    st.plotly_chart(fig, use_container_width=True)
    
    # Controles de paginación
    col1, col2 = st.columns(2)

    with col1:
        if st.session_state.page_number > 0:
            if st.button("Previous"):
                st.session_state.page_number -= 1
                st.rerun()

    with col2:
        if end_idx < len(cat_list):
            if st.button("Next"):
                st.session_state.page_number += 1
                st.rerun()
                
def render_results_sp(overview_map, ratio_map_bc, ratio_map_bi, diff_map_bc, diff_map_bi, variable, agg_type, cat_value):
    """Renderiza los resultados y gráficos en la interfaz de usuario."""
    
    if variable == 'Income':
        text_overview = """Displays the total or daily revenue generated from trucking operations across different states.
                                Darker green areas indicate higher income levels, while lighter shades represent lower earnings."""
    elif variable == 'Cost':
        text_overview = """Shows the total or daily operational costs incurred in each state.
                            Darker red indicates higher costs, while lighter shades represent lower expenses."""
    elif variable == 'Profit':
        text_overview = """Highlights the net earnings after subtracting costs from income in each state.
                            Green areas represent profitable regions, while red areas may indicate loss-making locations."""
    
    text_ratio_i = f"""Compares the {cat_value} financial performance against industry benchmarks.<br>
                    <b>Color Interpretation:</b><br>
                    <i><b>Green Areas</b></i> → A ratio above 1.0, means {cat_value} is outperforming the industry standard.<br>
                    <i><b>Yellow Areas</b></i> → A ratio as 1.0, means {cat_value} performance is in line with the industry standard.<br>
                    <i><b>Red Areas</b></i> → A ratio above 1.0, below {cat_value} is underperforming, meaning they are losing money compared to the industry standard."""
    
    text_ratio_c = f"""Compares the {cat_value} financial performance against {c.client} benchmarks.<br>
                    <b>Color Interpretation:</b><br>
                    <i><b>Green Areas</b></i> → A ratio above 1.0, means {cat_value} is outperforming the {c.client} standard.<br>
                    <i><b>Yellow Areas</b></i> → A ratio as 1.0, means {cat_value} performance is in line with the {c.client} standard.<br>
                    <i><b>Red Areas</b></i> → A ratio above 1.0, below {cat_value} is underperforming, meaning they are losing money compared to the {c.client} standard."""
    
    text_diff_i = f"""Displays the absolute difference between the {cat_value} financial metrics and industry benchmarks.<br>
                    <b>Color Interpretation:</b><br>
                    <i><b>Green Areas</b></i> → {cat_value} is outperforming the industry standard.<br>
                    <i><b>Yellow Areas</b></i> → {cat_value} performance is in line with the industry standard.<br>
                    <i><b>Red Areas</b></i> → {cat_value} is underperforming, meaning they are losing money compared to the industry standard.
                    """

    text_diff_c = f"""Displays the absolute difference between the {cat_value} financial metrics and industry benchmarks.<br>
                    <b>Color Interpretation:</b><br>
                    <i><b>Green Areas</b></i> → {cat_value} is outperforming the {c.client} standard.<br>
                    <i><b>Yellow Areas</b></i> → {cat_value} performance is in line with the {c.client} standard.<br>
                    <i><b>Red Areas</b></i> → {cat_value} is underperforming, meaning they are losing money compared to the {c.client} standard.
                    """

    if agg_type == 'Total':

        st.divider()
        st.write(text_overview, unsafe_allow_html=True)
        st.plotly_chart(overview_map, use_container_width=True)
        
    else:
        
        if variable == 'Profit':
            
            tab1, tab2, tab3 = st.tabs([f"{cat_value} Overview Map", f"{cat_value} vs {c.client} Difference", f"{cat_value} vs Industry Difference"])

            text_diff_adds = f"""<b>Label Colors (Inside Each State)</b><br>
                                    <i><b>Red Labels</b></i> → Indicate negative profit for {c.client} in that state.<br>
                                    <i><b>Blue Labels</b></i> → Indicate positive profit for {c.client} in that state."""
                  
            with tab1:
                st.write(text_overview, unsafe_allow_html=True)
                st.plotly_chart(overview_map, use_container_width=True)
            with tab2:
                st.write(text_diff_c, unsafe_allow_html=True)
                st.write(text_diff_adds, unsafe_allow_html=True)
                st.plotly_chart(diff_map_bc, use_container_width=True)
            with tab3:
                st.write(text_diff_i, unsafe_allow_html=True)
                st.write(text_diff_adds, unsafe_allow_html=True)
                st.plotly_chart(diff_map_bi, use_container_width=True)    
            
        else:
            
            tab1, tab2, tab3 = st.tabs([f"{cat_value} Overview Map", f"{cat_value} vs {c.client} Ratio", f"{cat_value} vs Industry Ratio"])
        
            with tab1:
                st.write(text_overview, unsafe_allow_html=True)
                st.plotly_chart(overview_map, use_container_width=True)
            with tab2:
                st.write(text_ratio_c, unsafe_allow_html=True)
                st.plotly_chart(ratio_map_bc, use_container_width=True)
            with tab3:
                st.write(text_ratio_i, unsafe_allow_html=True)
                st.plotly_chart(ratio_map_bi, use_container_width=True)    
            