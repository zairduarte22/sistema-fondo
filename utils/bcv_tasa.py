import requests
import json
import streamlit as st

def tasa_bs():
    url = "https://pydolarve.org/api/v2/dollar?page=bcv"
    try:
        response = requests.get(url)  # Realiza la solicitud GET
        response.raise_for_status()  # Levanta una excepción para códigos de estado HTTP no exitosos (4xx, 5xx)
        data = response.json()
        tasa = data["monitors"]["usd"]["price"]
        st.toast("Obteniendo tasa del Dolar...")
        return tasa
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
        return 1
