import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Gym Tracker", page_icon="💪")

# CONEXIÓN GOOGLE SHEETS
def conectar_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("Gym_Data").sheet1 
        return sheet
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# RUTINA
rutina = {
    "Día 1: Pecho-Hombro-Tríceps": ["Fondos", "Press Inclinado", "Pec Deck", "Elevaciones Lat", "Press Militar", "Tríceps Polea"],
    "Día 2: Espalda-Bicep": ["Dominadas", "Remo Barra", "Jalón Pecho", "Face Pull", "Curl Bayesiano", "Curl Martillo"],
    "Día 3: Pierna": ["Sentadilla", "Hip Thrust", "Peso Muerto Rumano", "Pantorrillas", "Femoral", "Abductores"],
    "Día 5: Torso": ["Press Inclinado", "Press Banca", "Remo Barra", "Jalón Pecho", "Fondos Lastre"],
    "Día 6: Brazos": ["Elevaciones Lat", "Press Militar", "Press Francés", "Tríceps Polea", "Curl Araña", "Curl Martillo"]
}

st.title("💪 Mi Gym Tracker")
sheet = conectar_google_sheet()

if sheet:
    st.success("Conectado a la Nube ☁️")
    dia = st.selectbox("Elige Rutina:", list(rutina.keys()))
    
    with st.form("gym_form"):
        inputs = {}
        for ej in rutina[dia]:
            st.write(f"**{ej}**")
            c1, c2 = st.columns(2)
            inputs[ej] = (c1.text_input("Kg", key=f"{ej}k"), c2.text_input("Reps", key=f"{ej}r"))
            st.divider()
        
        if st.form_submit_button("Guardar"):
            fecha = datetime.now().strftime("%Y-%m-%d")
            data = []
            for ej, (k, r) in inputs.items():
                if k and r:
                    data.append([fecha, dia, ej, k, r])
            if data:
                sheet.append_rows(data)
                st.success("¡Guardado!")
            else:
                st.warning("Escribe algo primero.")
