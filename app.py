import streamlit as st
import pandas as pd
from datetime import datetime
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gym Tracker Pro", page_icon="🏋️", layout="wide")

# --- CONEXIÓN ---
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error conexión: {e}")
        return None

# --- CARGA DE DATOS ---
def cargar_datos_config():
    client = get_client()
    if not client: return {}, {}
    try:
        sh = client.open("Gym_Data")
        # 1. Imágenes
        imagenes = {d["Nombre"]: d["URL_Imagen"] for d in sh.worksheet("Ejercicios").get_all_records() if d["URL_Imagen"]}
        # 2. Rutinas
        rutinas = {}
        for r in sh.worksheet("Rutinas_Config").get_all_records():
            if r["Rutina"] not in rutinas: rutinas[r["Rutina"]] = []
            rutinas[r["Rutina"]].append(r["Ejercicio"])
        return imagenes, rutinas, client
    except Exception as e:
        st.error(f"Faltan pestañas en Sheets: {e}")
        return {}, {}, client

# --- LOGIN ---
def login():
    if "user" in st.session_state and st.session_state.user: return True
    st.markdown("<h1 style='text-align: center;'>🔒 Gym Login</h1>", unsafe_allow_html=True)
    
    client = get_client()
    if not client: return False
    
    try:
        ws = client.open("Gym_Data").worksheet("Usuarios")
        t1, t2 = st.tabs(["Entrar", "Registrar"])
        with t1:
            with st.form("lo"):
                u = st.text_input("Usuario")
                p = st.text_input("Pass", type="password")
                if st.form_submit_button("Entrar"):
                    for x in ws.get_all_records():
                        if str(x["Usuario"]) == u and str(x["Password"]) == p:
                            st.session_state.user = u
                            st.rerun()
                    st.error("Error")
        with t2:
            with st.form("re"):
                nu = st.text_input("Nuevo User"); np = st.text_input("Nueva Pass", type="password")
                if st.form_submit_button("Crear"):
                    ws.append_row([nu, np])
                    st.success("Creado!")
    except: st.error("Falta pestaña Usuarios")
    return False

if not login(): st.stop()

# --- VARIABLES ---
USUARIO = st.session_state.user
IMAGENES, RUTINAS, CLIENTE = cargar_datos_config()

# --- BARRA LATERAL (CONFIGURACIÓN DEL TIEMPO) ---
with st.sidebar:
    st.write(f"Hola, **{USUARIO}** 👋")
    st.divider()
    st.header("⏱️ Cronómetro")
    # AQUÍ ESTÁ LA CONFIGURACIÓN DEL TIEMPO
    TIEMPO_DESCANSO = st.number_input("Segundos de descanso:", min_value=10, max_value=300, value=60, step=10)
    
    st.divider()
    if st.button("Cerrar Sesión"):
        st.session_state.user = None; st.rerun()

# --- TIMER MEJORADO ---
def timer(segundos):
    pl = st.empty(); bar = st.progress(0)
    
    # Cuenta regresiva
    for i in range(segundos, -1, -1):
        # Calculamos porcentaje (cuidado con dividir por 0)
        progreso = (segundos - i) / segundos if segundos > 0 else 0
        bar.progress(progreso)
        pl.markdown(f"### ⏳ Descansando: {i}s")
        time.sleep(1)
    
    # Al finalizar
    pl.markdown("### 🔔 ¡SERIE LISTA!")
    bar.empty()
    
    # SONIDO: Usamos un sonido de 'Beep' corto y efectivo
    # Nota: Si el navegador bloquea el autoplay, aparecerá el control para darle play manual
    st.audio("https://www.soundjay.com/buttons/sounds/beep-07.mp3", autoplay=True)
    
    time.sleep(3) # Espera un poco para que se escuche
    pl.empty() # Limpia el mensaje

# --- APP ---
st.title("Gym Tracker Pro 🏋️")

tab1, tab2, tab3 = st.tabs(["Entrenar", "Progreso", "Configurar"])

# 1. ENTRENAR
with tab1:
    if not RUTINAS: st.info("Crea una rutina en Configurar.")
    else:
        dia = st.selectbox("Rutina:", list(RUTINAS.keys()))
        st.divider()
        datos = []
        
        for ej in RUTINAS[dia]:
            # ESTA ES LA LÍNEA QUE TIENES QUE CORREGIR:
            with st.expander(f"**{ej}**", expanded=True): 
                
                if ej in IMAGENES: st.image(IMAGENES[ej], width=150)
                
                kc = f"c_{dia}_{ej}"

