import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gym Tracker Pro", page_icon="💪")

# --- CONEXIÓN CON GOOGLE SHEETS ---
# Esta función conecta con la nube de forma segura
def conectar_google_sheet():
    # Definimos el alcance de los permisos
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Intentamos leer las credenciales desde los "Secretos" de Streamlit (para la nube)
    # O desde el archivo local si estás en tu PC
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            # SI ESTÁS EN TU PC: Asegúrate de que tu archivo descargado se llame 'credenciales.json'
            creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
            
        client = gspread.authorize(creds)
        # AQUÍ PON EL NOMBRE EXACTO DE TU HOJA DE GOOGLE SHEETS
        sheet = client.open("Gym_Data").sheet1 
        return sheet
    except Exception as e:
        st.error(f"Error conectando a Google Sheets: {e}")
        return None

# --- TU RUTINA (Igual que antes) ---
rutina = {
    "Día 1: Pecho-Hombro-Tríceps": ["Fondos", "Press Inclinado", "Pec Deck", "Elevaciones Laterales", "Press Militar", "Tríceps Polea"],
    "Día 2: Espalda-Bíceps": ["Dominadas", "Remo Barra", "Jalón Pecho", "Face Pull", "Curl Bayesiano", "Curl Martillo"],
    "Día 3: Pierna": ["Sentadilla", "Hip Thrust", "Peso Muerto Rumano", "Pantorrillas", "Femoral", "Abductores"],
    "Día 5: Torso": ["Press Inclinado", "Press Banca", "Remo Barra", "Jalón Pecho", "Fondos Lastre"],
    "Día 6: Brazos": ["Elevaciones Laterales", "Press Militar", "Press Francés", "Tríceps Polea", "Curl Araña", "Curl Martillo"]
}

st.title("☁️ Gym Tracker (Nube)")

# --- CARGAR DATOS EXISTENTES ---
sheet = conectar_google_sheet()

if sheet:
    # Leemos los datos para mostrar el historial
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
else:
    df = pd.DataFrame()
    st.warning("⚠️ No se pudo conectar. Revisa tus credenciales.")

# --- SELECCIÓN ---
dia_seleccionado = st.selectbox("Rutina de hoy:", list(rutina.keys()))

# --- FORMULARIO ---
with st.form("entry_form"):
    st.subheader(f"Entrenando: {dia_seleccionado}")
    inputs = {}
    
    # Creamos los campos
    for ejercicio in rutina[dia_seleccionado]:
        st.markdown(f"**{ejercicio}**")
        c1, c2 = st.columns(2)
        peso = c1.text_input("Kg", key=f"{ejercicio}_k")
        reps = c2.text_input("Reps", key=f"{ejercicio}_r")
        inputs[ejercicio] = (peso, reps)
        st.divider()

    submitted = st.form_submit_button("Subir a la Nube 🚀")

    if submitted and sheet:
        fecha = datetime.now().strftime("%Y-%m-%d")
        filas_a_insertar = []
        
        for ejercicio, (peso, reps) in inputs.items():
            if peso and reps: # Solo si escribiste algo
                # Estructura: Fecha, Día, Ejercicio, Serie(Puse 1 por simplificar), Peso, Reps
                filas_a_insertar.append([fecha, dia_seleccionado, ejercicio, "Serie Única", peso, reps])
        
        if filas_a_insertar:
            # Enviamos todo de golpe a Google Sheets
            sheet.append_rows(filas_a_insertar)
            st.success("✅ ¡Guardado en Google Sheets!")
            st.rerun() # Recarga la página para ver los datos nuevos
        else:
            st.warning("Escribe al menos un peso/rep.")

# --- HISTORIAL ---
st.divider()
st.subheader("📊 Tu Progreso Global")
if not df.empty:
    st.dataframe(df.tail(10)) # Muestra los últimos 10
