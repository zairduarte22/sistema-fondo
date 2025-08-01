import streamlit as st
from utils.bcv_tasa import tasa_bs
from views.login import login_page

if 'tasa_bs' not in st.session_state:
    st.session_state['tasa_bs'] = tasa_bs()

# --- PAGE SETUP ---
style = 'style/style.css'
with open(style) as e:
    st.markdown(f'<style> {e.read()} </style>', unsafe_allow_html=True)

# Define logout function
def log_out():
    st.session_state.pop("user", None)  # Clear user session
    st.rerun()  # Trigger a rerun to redirect to the login page

# Check if user is logged in
if "user" not in st.session_state or st.session_state["user"] is None:
    # Redirect to login page
    login_page()
else:
    # Define navigation pages
    resumen = st.Page(
        page='views/resumen.py',
        title='Informe General',
        icon=':material/dashboard:',
        default=True,
    )

    miembros = st.Page(
        page='views/miembros.py',
        title='Miembros',
        icon=':material/group:'
    )

    facturas = st.Page(
        page='views/facturas.py',
        title='Facturas',
        icon=':material/receipt:'
    )

    ingresos = st.Page(
        page='views/ingresos.py',
        title='Ingresos',
        icon=':material/trending_up:'
    )

    gastos = st.Page(
        page='views/gastos.py',
        title='Gastos',
        icon=':material/trending_down:'
    )

    con_bs = st.Page(
        page='views/con_bs.py',
        title='Bancos',
        icon=':material/account_balance:'
    )

    con_divisas = st.Page(
        page='views/con_divisas.py',
        title='Divisas',
        icon=':material/attach_money:'
    )

    # Initialize navigation only if it doesn't exist
    pg = st.navigation(
            pages={
                ' Gestion de Miembros': [
                    resumen,
                    miembros,
                    facturas
                ],
                ' Contabilidad': [
                    ingresos,
                    gastos,
                    con_bs,
                    con_divisas
                ]
            }
        )

    # --- COMPARTIDO EN TODAS LAS PAGINAS ---
    st.logo('assets/images/LOGO.png', size='large')
    st.sidebar.write(f'**Tasa BCV: Bs. {st.session_state['tasa_bs']}**')
    st.sidebar.write(f'**Desarrollado por Zair Duarte**')
    st.sidebar.button("Cerrar Sesión", on_click=log_out)
    pg.run()
