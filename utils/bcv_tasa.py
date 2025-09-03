import requests
import json
import streamlit as st

def tasa_bs():
    url = "https://ve.dolarapi.com/v1/dolares/oficial"
    try:
        response = requests.get(url)  # Realiza la solicitud GET
        response.raise_for_status()  # Levanta una excepción para códigos de estado HTTP no exitosos (4xx, 5xx)
        data = response.json()
        tasa = data["promedio"]
        st.toast("Obteniendo tasa del Dolar...")
        return tasa
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
        return 1
