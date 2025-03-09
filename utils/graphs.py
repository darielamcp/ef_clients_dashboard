import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import json
import numpy as np
import utils.constants as c


class MapConfig:
    """Encapsula la configuración de mapas para reutilización."""
    WIDTH = 1400
    HEIGHT = 700
    MARGIN = dict(l=0, r=0, t=50, b=0)
    HOVERLABEL_CONFIG = dict(
        font_size=25,
        font_family="Arial",
        bgcolor="white",
        bordercolor="black",
    )
    XBX_AXIS_CONFIG = dict(
        xaxis_tickangle=-45, height=600,
        showline=True,
        linewidth=2,
        linecolor='grey',
        showgrid=True,
        tickangle=0,
        tickmode='linear',
        dtick=150,
        tickfont=dict(size=30),
        title_font=dict(size=30)
    )
    YBX_AXIS_CONFIG = dict(
        tickfont=dict(size=30), title_font=dict(size=30)  # Ajusta el tamaño de la fuente aquí
    )


class ChoroplethMap:
    """Clase base para la generación de mapas coropléticos."""

    def __init__(self, df, state_id, variable, namevar, round_value, min_val, max_val, color_scale="ylgn"):
        self.df = df
        self.state_id = state_id
        self.variable = variable
        self.namevar = namevar
        self.round_value = round_value
        self.min_val = min_val
        self.max_val = max_val
        self.color_scale = color_scale

    def generate_map(self, animation_frame, tooltip):
        
        labels_org = {'start_date': 'Date', 'origin': 'State', 'destination': 'State'}
        
        hover_data = {col:f":,.{round_value}f" for col, name, round_value in tooltip}
        labels = {col:name for col, name, round_value in tooltip}
        labels.update(labels_org)

        fig = px.choropleth(
            self.df,
            locations=self.state_id,
            color=self.variable,
            locationmode="USA-states",
            color_continuous_scale=self.color_scale,
            range_color=(self.min_val, self.max_val),
            hover_data=hover_data,
            scope="usa",
            animation_frame=animation_frame,
            labels=labels,
        )
        
        self.tick_vals = np.linspace(self.min_val, self.max_val, 5)
        self.tick_texts = [f"{v:,.{self.round_value}f}" for v in self.tick_vals]
        
        fig.update_layout(
            width=MapConfig.WIDTH,
            height=MapConfig.HEIGHT,
            margin=MapConfig.MARGIN,
            coloraxis_colorbar=dict(
                tickvals=self.tick_vals,
                ticktext=self.tick_texts,
                title=f"<b>{self.namevar}</b>",
                title_font_size=30,
                thickness=40,
                len=0.75,
                tickfont=dict(size=20),
            ),
        )
        
        fig.update_traces(hoverlabel=MapConfig.HOVERLABEL_CONFIG)
        return fig


@st.cache_resource(ttl=84600, show_spinner="Creating map for states...")
def get_map_states(df, variable, state_id, anm_col, namevar, round_value, tooltip, state=None, color_scale="ylgn"):
    """Función de alto nivel para obtener el mapa de estados estándar."""
    df[anm_col] = df[anm_col].astype(str)
    
    min_val = df[variable].min()
    max_val = df[variable].max()

    if color_scale != "rdylgn":
        if "profit" in variable.lower():
            color_scale = "rdylgn"
            sup = max(abs(min_val), abs(max_val))
            min_val, max_val = -sup, sup
        else:
            min_val, max_val = min_val, max_val
    
    choropleth = ChoroplethMap(df, state_id, variable, namevar, round_value, min_val, max_val, color_scale)
    fig = choropleth.generate_map(anm_col, tooltip)
    
    if state != None:
        with open("files/state_coords.json", "r") as json_file:
            state_coords = json.load(json_file)

        if state in state_coords:
            fig.add_trace(go.Scattergeo(
                lon=[state_coords[state][0]],
                lat=[state_coords[state][1]],
                marker=dict(size=20, symbol="circle", opacity=1, color='orange'),
                mode="markers",
                showlegend=False
        ))
                
    return fig


@st.cache_resource(ttl=84600, show_spinner="Creating map for states...")
def get_map_states_h(df, variable, state_id, anm_col, namevar, round_value, tooltip, var_plot):
    """Genera un mapa coroplético con diferencias o ratios."""
    df[anm_col] = df[anm_col].astype(str)
    
    color_scale="rdylgn"
    value = max(abs(df[variable].min()), abs(df[variable].max()))
    min_val, max_val = (-value, value) if 'diff' in variable else (0, 2)
    
    choropleth = ChoroplethMap(df, state_id, variable, namevar, round_value, min_val, max_val, color_scale)
    fig = choropleth.generate_map(anm_col, tooltip)

    with open("files/state_coords.json", "r") as json_file:
        state_coords = json.load(json_file)
    
    if "profit" in var_plot.lower() and 'diff' in variable:
        for _, row in df.iterrows():
            state = row[state_id]
            if state in state_coords:
                fig.add_trace(go.Scattergeo(
                    lon=[state_coords[state][0]],
                    lat=[state_coords[state][1]],
                    marker=dict(size=40, symbol="square", opacity=1, color='white'),
                    mode="markers",
                    showlegend=False
                ))
                fig.add_trace(go.Scattergeo(
                    lon=[state_coords[state][0]],
                    lat=[state_coords[state][1]],
                    text=f"{row[var_plot]:.{round_value}f}",
                    mode="text",
                    textfont=dict(
                        color="blue" if row[var_plot] > 0 else "red",
                        size=15,
                    ),
                    showlegend=False
                ))
                
    return fig


@st.cache_resource(ttl=84600, show_spinner="Creating map for states...")
def get_map_states_rh(df, variable, state_id, anm_col, namevar, round_value):
    """Genera un mapa coroplético para relaciones In/Out."""
    df[anm_col] = df[anm_col].astype(str)
    org_var = variable.split("_io")[0]
    round_variable = round_value if org_var == "profit" else 2
    
    choropleth = ChoroplethMap(df, state_id, variable, namevar, round_variable, "rdylgn")
    return choropleth.generate_map(anm_col)


@st.cache_resource(ttl=84600, show_spinner="Creating map for states...")
def get_map_states_brk(df, variable, state_id, anm_col, namevar, suffix, round_value):
    """Genera un mapa de estados con datos segmentados."""
    df[anm_col] = df[anm_col].astype(str)
    min_val, max_val = (0, 2) if variable == "Ratio" else (df[variable].min(), df[variable].max())
    round_variable = 2 if namevar == "Ratio" else round_value
    
    choropleth = ChoroplethMap(df, state_id, variable, namevar, round_variable, color_scale="rdylgn")
    return choropleth.generate_map(anm_col)


@st.cache_resource(ttl=84600, show_spinner="Creating map for states...")
def get_map_color_dis(df_pivot, state_id, color_col, color_dict, round_value):
    """Genera un mapa coroplético con colores discretos."""
    fig = px.choropleth(
        df_pivot,
        locations=state_id,
        locationmode="USA-states",
        color=color_col,
        animation_frame="start_date",
        hover_data={state_id: True},
        scope="usa",
        color_discrete_map=color_dict,
    )
    
    fig.update_layout(width=MapConfig.WIDTH, height=MapConfig.HEIGHT, margin=MapConfig.MARGIN)
    fig.update_traces(hoverlabel=MapConfig.HOVERLABEL_CONFIG)
    return fig

@st.cache_resource(ttl=84600, show_spinner="Creating violin plot...")
def get_violinplot(df, x_var, y_var, title, y_title, x_title, cl='category', color_dict=None, keep_tick=True):
    df = df.dropna(subset=[x_var])
    fig = px.violin(df, x=y_var, y=x_var, title=title, color=cl, box=True, color_discrete_map=color_dict)
    fig.update_layout(xaxis_tickangle=-45, height=600)
    fig.update_layout(xaxis_title=y_title, yaxis_title=x_title)
    if keep_tick:
        fig.update_layout(
            xaxis=dict(showline=True, linewidth=2, linecolor='grey', showgrid=True, tickmode='linear', dtick=250, tickangle=0, tickfont=dict(size=23), title_font=dict(size=30)),
            yaxis=dict(tickfont=dict(size=30), title_font=dict(size=30)),
            showlegend=False,
        )
    else:
        fig.update_layout(
            xaxis=dict(showline=True, linewidth=2, linecolor='grey', showgrid=True, tickangle=0, tickfont=dict(size=30), title_font=dict(size=30)),
            yaxis=dict(tickfont=dict(size=30), title_font=dict(size=30)),
            showlegend=False,
        )
    return fig

@st.cache_resource(ttl=84600, show_spinner="Creating map for states...")
def get_map_dis_bubble(df_pivot_m, state_id, color_dict, color_col, color_bubble):
    fig = px.choropleth(
        df_pivot_m,
        locations=state_id,
        locationmode="USA-states",
        color=color_col,
        animation_frame='start_date',
        hover_data={state_id: True, 'REEFER_r': True, 'VAN_r': True, 'FLATBED_r': True},
        scope="usa",
        color_discrete_map=color_dict,
        labels={'best_equip_r': '<b>Best Equip</b>', 'origin': 'State', 'destination': 'State', 'start_date': 'Start Date', 'REEFER_r': 'REEFER', 'VAN_r': 'VAN', 'FLATBED_r': 'FLATBED'},
    )
    with open("files/state_coords.json", "r") as json_file:
        state_coords = json.load(json_file)
    for i, row in df_pivot_m.iterrows():
        state = row[state_id]
        if state in state_coords:
            fig.add_trace(go.Scattergeo(lon=[state_coords[state][0]], lat=[state_coords[state][1]], marker=dict(size=20, symbol="circle", opacity=1, color=row[color_bubble]), mode="markers", showlegend=False))
    fig.update_layout(width=MapConfig.WIDTH, height=MapConfig.HEIGHT, margin=MapConfig.MARGIN, legend=dict(title_font=dict(size=38), font=dict(size=30)))
    fig.update_traces(hoverlabel=MapConfig.HOVERLABEL_CONFIG)
    return fig

@st.cache_resource(ttl=84600, show_spinner="Creating map for states...")
def get_map_color_dis(df_pivot, state_id, color_col, color_dict, round_value):
    fig = px.choropleth(
        df_pivot,
        locations=state_id,
        locationmode="USA-states",
        color=color_col,
        animation_frame='start_date',
        hover_data={state_id: True, 'REEFER_c': f':,.{round_value}f', 'VAN_c': f':,.{round_value}f', 'FLATBED_c': f':,.{round_value}f'},
        scope="usa",
        color_discrete_map=color_dict,
        labels={'best_equip_c': '<b>Best Equip</b>', 'origin': 'State', 'destination': 'State', 'start_date': 'Start Date', 'REEFER_c': 'REEFER', 'VAN_c': 'VAN', 'FLATBED_c': 'FLATBED'},
    )
    fig.update_layout(width=MapConfig.WIDTH, height=MapConfig.HEIGHT, margin=MapConfig.MARGIN, legend=dict(title_font=dict(size=38), font=dict(size=30)))
    fig.update_traces(hoverlabel=MapConfig.HOVERLABEL_CONFIG)
    return fig

@st.cache_resource(ttl=84600, show_spinner="Creating box plot...")
def get_boxplot(df, x_var, y_var, title, y_title, x_title, cl=None, keep_tick=True):
    """Genera un boxplot con opciones de personalización."""
    fig = px.box(df, x=y_var, y=x_var, title=title, color=cl)

    fig.update_traces(
    boxpoints='outliers',
    hovertemplate="{x_title}: %{x}<br>Q1: %{q1}<br>Median: %{median}<br>Q3: %{q3}<br>Min: %{min}<br>Max: %{max}"
    )

    if keep_tick:
        fig.update_layout(
        xaxis_tickangle=-45,height=600,
        xaxis_title=y_title,
        yaxis_title=x_title,
        xaxis=dict(
            showline=True, linewidth=2, linecolor='grey', showgrid=True, 
            tickmode='linear', dtick=250, tickangle=0, tickfont=dict(size=30),
            title_font=dict(size=30)
        ),
        showlegend=False,
        hoverlabel=dict(font_size=30),
        yaxis=dict(
            tickfont=dict(size=30), title_font=dict(size=30)
        )
        )
    else:
        fig.update_layout(
        xaxis_tickangle=-45,height=600,
        xaxis_title=y_title,
        yaxis_title=x_title,
        xaxis=dict(
            showline=True, linewidth=2, linecolor='grey', showgrid=True, 
            tickangle=0, tickfont=dict(size=30),
            title_font=dict(size=30)
        ),
        showlegend=False,
        hoverlabel=dict(font_size=30),
        yaxis=dict(
            tickfont=dict(size=30), title_font=dict(size=30)
        )
        )
        
    
    return fig


@st.cache_resource(ttl=84600, show_spinner="Creating distance heat map...")
def get_map_color_hdistance(df_pivot, state_id, color_col, color_dict, state=None):
    """Genera un mapa coroplético con colores discretos basado en la distancia."""
    fig = px.choropleth(
        df_pivot,
        locations=state_id,
        locationmode="USA-states",
        color=color_col,
        animation_frame='start_date',
        hover_data={state_id: True, 'days_mean': True},
        scope="usa",
        color_discrete_map=color_dict,
        labels={'state_origin': 'State', 'state_destination': 'State', 'days_mean': 'Days', 'start_date': 'Start Date'},
    )
    
    if state != None:
        with open("files/state_coords.json", "r") as json_file:
            state_coords = json.load(json_file)

        if state in state_coords:
            fig.add_trace(go.Scattergeo(
                lon=[state_coords[state][0]],
                lat=[state_coords[state][1]],
                marker=dict(size=20, symbol="circle", opacity=1, color='orange'),
                mode="markers",
                showlegend=False
        ))
    
    fig.update_layout(
        width=MapConfig.WIDTH,
        height=MapConfig.HEIGHT,
        margin=MapConfig.MARGIN,
        coloraxis_showscale=False,
        legend=dict(
            title_font=dict(size=38),
            font=dict(size=30)
        )
    )
    
    fig.update_traces(hoverlabel=MapConfig.HOVERLABEL_CONFIG)
    return fig


