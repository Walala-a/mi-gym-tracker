import streamlit as st
import pandas as pd
from datetime import datetime
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gym Tracker Pro", page_icon="🏋️", layout="wide")

# --- 1. CONEXIÓN GOOGLE SHEETS ---
def get_google_sheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- 2. GESTIÓN DE USUARIOS ---
def gestion_usuarios():
    if "usuario_actual" not in st.session_state:
        st.session_state.usuario_actual = None

    if st.session_state.usuario_actual:
        return True

    st.markdown("<h1 style='text-align: center;'>🔒 Gym Tracker</h1>", unsafe_allow_html=True)
    
    client = get_google_sheet_client()
    if not client: return False

    try:
        hoja_usuarios = client.open("Gym_Data").worksheet("Usuarios")
    except:
        st.error("⚠️ Crea la pestaña 'Usuarios' en tu Google Sheet (Columnas: Usuario, Password)")
        return False

    tab_login, tab_registro = st.tabs(["Iniciar Sesión", "Crear Cuenta"])

    with tab_login:
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar ➡️", use_container_width=True):
                users = hoja_usuarios.get_all_records()
                for reg in users:
                    if str(reg["Usuario"]) == u and str(reg["Password"]) == p:
                        st.session_state.usuario_actual = u
                        st.rerun()
                st.error("Datos incorrectos")

    with tab_registro:
        with st.form("reg"):
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Contraseña", type="password")
            if st.form_submit_button("Crear 🆕", use_container_width=True):
                users = hoja_usuarios.get_all_records()
                if nu in [str(r["Usuario"]) for r in users]:
                    st.error("Ya existe")
                else:
                    hoja_usuarios.append_row([nu, np])
                    st.success("Creado! Logueate.")
    return False

if not gestion_usuarios(): st.stop()

# --- VARIABLES GLOBALES ---
USUARIO = st.session_state.usuario_actual
client = get_google_sheet_client()
sheet_datos = client.open("Gym_Data").sheet1

IMAGENES = {
    "Fondos": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Chest-Dips.gif",
    "Press Inclinado": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Incline-Barbell-Bench-Press.gif",
    "Pec Deck": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Pec-Deck-Fly.gif",
    "Elevaciones Laterales": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Lateral-Raise.gif",
    "Press Militar": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Military-Press.gif",
    "Tríceps Polea": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Push-Down.gif",
    "Dominadas
