import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db.conexion import ConciliacionBS, ConciliacionDivisas, obtener_df, Miembro

st.title('Resumen financiero')

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
col0, col1, col2, col3 = st.columns([1.5,1,1,1], border=False)
with col0:
    st.metric('Disponible en Bancos', f"Bs. {totalbs:.2f}")
with col1:
    st.metric('Disponible en Divisas', f"$ {totaldiv:.2f}")
with col2:
    st.metric('Total Miembros', total_miembros)
with col3:
    st.metric('Miembros Solventes', miembros_solventes)

col4, col5 = st.columns(2)
with col4:
    con_bs['FECHA'] = pd.to_datetime(con_bs['FECHA'])  # Asegurarse de que la fecha esté en formato datetime
    con_bs = con_bs.sort_values('FECHA')  # Ordenar por fecha
    fig_line_bs = px.line(con_bs, x='FECHA', y=['INGRESO', 'EGRESO'], title='Movimientos en Bolívares', labels={'value': 'Monto (Bs)', 'variable': 'Tipo'}, color_discrete_sequence=px.colors.sequential.Greens_r, line_shape='spline')
    fig_line_bs.update_traces(fill='tozeroy', fillcolor='rgba(15, 89, 16, 0.53)', line=dict(width=4))
    st.plotly_chart(fig_line_bs)
with col5:
    # Gráfico de líneas: Movimientos de conciliación en divisas
    con_div['FECHA'] = pd.to_datetime(con_div['FECHA'])  # Asegurarse de que la fecha esté en formato datetime
    con_div = con_div.sort_values('FECHA')  # Ordenar por fecha
    fig_line_div = px.line(con_div, x='FECHA', y=['INGRESO', 'EGRESO'], title='Movimientos en Divisas', labels={'value': 'Monto ($)', 'variable': 'Tipo'}, color_discrete_sequence=px.colors.sequential.Greens_r, line_shape='spline')
    fig_line_div.update_traces(fill='tozeroy', fillcolor='rgba(15, 89, 16, 0.53)', line=dict(width=4))
    st.plotly_chart(fig_line_div)