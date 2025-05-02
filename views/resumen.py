import streamlit as st
import pandas as pd
import plotly.express as px
from db.conexion import ConciliacionBS, ConciliacionDivisas, obtener_df, Miembro


st.title('Resumen Financiero')

# Lista de meses en español
MES_EN_ESPANOL = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# Obtener datos
con_bs = obtener_df(ConciliacionBS)
con_div = obtener_df(ConciliacionDivisas)
miembros = obtener_df(Miembro)

# Cálculos
total_miembros = miembros['ID_MIEMBRO'].count()
miembros_solventes = miembros[miembros['ESTADO'] == 'SOLVENTE']['ID_MIEMBRO'].count()
miembros_insolventes = total_miembros - miembros_solventes
totalbs = ((con_bs['INGRESO'].sum()) - (con_bs['EGRESO'].sum()))
totaldiv = ((con_div['INGRESO'].sum()) - (con_div['EGRESO'].sum()))

# Métricas
col0, col1, col2, col3 = st.columns([1.5, 1, 1, 1], border=False)
with col0:
    st.metric('Disponible en Bancos', f"Bs. {totalbs:.2f}")
with col1:
    st.metric('Disponible en Divisas', f"$ {totaldiv:.2f}")
with col2:
    st.metric('Total Miembros', total_miembros)
with col3:
    st.metric('Miembros Solventes', miembros_solventes)
    
st.subheader('Movimientos Mensuales')

col4, col5 = st.columns(2)
with col4:
    # Procesar datos para gráfico de barras en bolívares
    con_bs['FECHA'] = pd.to_datetime(con_bs['FECHA'])  # Asegurarse de que la fecha esté en formato datetime
    con_bs['MES'] = con_bs['FECHA'].dt.month  # Extraer el número del mes
    con_bs['AÑO'] = con_bs['FECHA'].dt.year  # Extraer el año
    con_bs['Mes'] = con_bs['MES'].apply(lambda x: f"{MES_EN_ESPANOL[x - 1]} {con_bs['AÑO'].iloc[0]}")  # Mes en español
    con_bs_grouped = con_bs.groupby('Mes')[['INGRESO', 'EGRESO']].sum().reset_index()  # Agrupar por mes y sumar ingresos y egresos
    fig_bar_bs = px.bar(
        con_bs_grouped,
        x='Mes',
        y=['INGRESO', 'EGRESO'],
        title='Bolívares',
        labels={'value': 'Monto (Bs)', 'variable': 'Tipo'},
        barmode='group',
        color_discrete_sequence=px.colors.sequential.Greens_r
    )
    st.plotly_chart(fig_bar_bs)

with col5:
    # Procesar datos para gráfico de barras en divisas
    con_div['FECHA'] = pd.to_datetime(con_div['FECHA'])  # Asegurarse de que la fecha esté en formato datetime
    con_div['MES'] = con_div['FECHA'].dt.month  # Extraer el número del mes
    con_div['AÑO'] = con_div['FECHA'].dt.year  # Extraer el año
    con_div['Mes'] = con_div['MES'].apply(lambda x: f"{MES_EN_ESPANOL[x - 1]} {con_div['AÑO'].iloc[0]}")  # Mes en español
    con_div_grouped = con_div.groupby('Mes')[['INGRESO', 'EGRESO']].sum().reset_index()  # Agrupar por mes y sumar ingresos y egresos
    fig_bar_div = px.bar(
        con_div_grouped,
        x='Mes',
        y=['INGRESO', 'EGRESO'],
        title='Divisas',
        labels={'value': 'Monto ($)', 'variable': 'Tipo'},
        barmode='group',
        color_discrete_sequence=px.colors.sequential.Greens_r
    )
    st.plotly_chart(fig_bar_div)