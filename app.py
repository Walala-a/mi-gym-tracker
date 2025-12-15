import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Gym Tracker", page_icon="💪")

# --- CONEXIÓN INTELIGENTE (PC O NUBE) ---
def conectar_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # 1. Intentamos leer de los SECRETOS de la nube
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        # 2. Si no hay secretos, buscamos el archivo local (Tu PC)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
            
        client = gspread.authorize(creds)
        sheet = client.open("Gym_Data").sheet1 
        return sheet
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- RUTINA ---
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
        st.subheader(f"Entrenando: {dia}")
        for ej in rutina[dia]:
            st.write(f"**{ej}**")
            c1, c2 = st.columns(2)
            inputs[ej] = (c1.text_input("Kg", key=f"{ej}k"), c2.text_input("Reps", key=f"{ej}r"))
            st.divider()
        
        if st.form_submit_button("Guardar en Google Sheets 🚀"):
            fecha = datetime.now().strftime("%Y-%m-%d")
            data = []
            for ej, (k, r) in inputs.items():
                if k and r:
                    data.append([fecha, dia, ej, k, r])
            if data:
                sheet.append_rows(data)
                st.success("¡Datos guardados!")
            else:
                st.warning("Escribe al menos un peso/rep.")
