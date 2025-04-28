import streamlit as st
from utils.bcv_tasa import tasa_bs
from views.login import login_page


# --- PAGE SETUP ---

st.set_page_config(layout='wide')
style = 'style/style.css'
with open(style) as e:
    st.markdown(f'<style> {e.read()} </style>', unsafe_allow_html=True)

# Check if user is logged in
if "user" not in st.session_state:
    login_page()
else:
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

    pg = st.navigation(
        pages={
            '👥 Gestion de Miembros' : [
                resumen,
                miembros,
                facturas
            ],
            '🪙 Contabilidad' : [
                ingresos,
                gastos,
                con_bs,
                con_divisas
            ]
        }
    )

    # --- COMPARTIDO EN TODAS LAS PAGINAS ---
    st.logo('assets/images/LOGO.png', size='large')
    st.sidebar.write(f'**Tasa BCV: Bs. {tasa_bs()}**')
    def logout():
        st.session_state.pop("user", None)
        st.rerun()
    st.sidebar.button("Cerrar Sesión", on_click=logout)
    pg.run()
    