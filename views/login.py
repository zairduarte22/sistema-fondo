import streamlit as st
from auth.firebase_auth import login_user, register_user

def login_page():
    col1, col2, col3 = st.columns([1, 7, 1], gap="small")
    with col2:
        with st.container(border=False):
            st.title("¡Bienvenido!")
            st.write("Bienvenido a la aplicación de gestión financiera. Por favor, inicie sesión para continuar.")
            email = st.text_input("Correo Electrónico", key="login_email")
            password = st.text_input("Contraseña", type="password")
            loginbutton = st.button("Entrar", key="login_button", type="primary")
            if loginbutton:
                user = login_user(email, password)
                if "error" in user:
                    if "INVALID_LOGIN_CREDENTIALS" in user["error"]:
                        st.toast("Credenciales inválidas. Por favor, intente nuevamente.")
                else:
                    st.toast("Inicio de sesión exitoso!, por favor espere...")
                    st.session_state["user"] = user
                    st.rerun()
