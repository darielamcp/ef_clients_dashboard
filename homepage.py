import streamlit as st
from streamlit_option_menu import option_menu
import datetime as dt
import finantial_performance as fp
import broker_section as bs
import dispatcher_section as ds
import equips_section as es
import distance_section as hds
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(layout="wide")

app = option_menu(
                menu_title=None,
                options=['Home', 'Financial Performance', 'Brokerage', 'Dispatchers', 'Equips', 'Hauling Performance'],
                menu_icon='cast',
                default_index=0,
                orientation='horizontal',
                styles={
                    "container": {"background-color": "#F5F5F5", "border-radius": "10px"},
                    "icon": {"color": "black", "font-size": "18px"},
                    "nav-link": {
                        "color": "black",
                        "font-size": "25px",
                        "border-radius": "5px",
                        "padding": "10px",
                    },
                    # Colores personalizados para cada pestaña
                    "nav-link-0-selected": {"background-color": "#33A8FF"},  # Rojo para Database
                    "nav-link-1": {"background-color": "#33A8FF"},  # Azul para Upload
                    "nav-link-2": {"background-color": "#33FF57"},  # Verde para Analytics
                    "nav-link-3": {"background-color": "#FF33A8"},  # Rosado para Settings
                    "nav-link-selected": {
                        "background-color": "#bebdbdff",
                        "color": "black",
                        "font-size": "25px",
                        "border-radius": "5px",
                        "--icon-color":"white",
                    },
                },
                )

with open('./styles/style_main.css', 'r') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


with st.sidebar:
    
    st.write("""Use the date picker to select the time period for the data analysis. 
             Adjust the frequency to view aggregated results over different time frames, 
             such as total, annual, quarterly, monthly, weekly, or daily insights.
             <hr style="margin: 5px 0; border: none; border-top: 1px solid #ddd;">""",
            unsafe_allow_html=True)

    date_range = st.date_input(
        "**Select a date range**",
        # (dt.datetime.now() - dt.timedelta(weeks=30), dt.datetime.now()),
        ('2024-07-01', '2024-07-31'),
        '2021-01-01',
        dt.datetime.now() + dt.timedelta(weeks=15),
        format="MM/DD/YYYY",
    )
    date_range = (date_range[0], date_range[0]) if len(date_range) == 1 else date_range

    freq = st.selectbox("**Select Date Frequency**", ['Total', 'Annual', 'Quarterly', 'Monthly', 'Weekly', 'Daily'])
    
st.session_state['date_range'] = date_range
st.session_state['freq'] = freq

if app == "Financial Performance":
    fp.app()
elif app == "Brokerage":
    bs.app()
elif app == "Dispatchers":
    ds.app()
elif app == "Equips":
    es.app()
elif app == 'Hauling Performance':
    hds.app()
