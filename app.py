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
    "Dominadas": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Pull-up.gif",
    "Remo Barra": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Bent-Over-Row.gif",
    "Jalón Pecho": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Lat-Pulldown.gif",
    "Face Pull": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Face-Pull.gif",
    "Curl Bayesiano": "https://i.pinimg.com/originals/ce/0f/36/ce0f365d9539260195d8527a2068bf86.gif",
    "Curl Martillo": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Hammer-Curl.gif",
    "Sentadilla": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Squat.gif",
    "Hip Thrust": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Hip-Thrust.gif",
    "Peso Muerto Rumano": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Romanian-Deadlift.gif",
    "Elevacion de Pantorrillas": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Calf-Raise.gif",
    "Curl femoral sentado": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Seated-Leg-Curl.gif",
    "Abductores en maquina": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Seated-Hip-Abduction.gif",
    "Press Banca": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Bench-Press.gif",
    "Fondos Lastre": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Chest-Dips.gif",
    "Press Francés": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Triceps-Extension.gif",
    "Curl Araña": "https://d205bpvrqc9yn1.cloudfront.net/0309.gif",
}

rutina = {
    "Día 1: Pecho-Hombro-Tríceps": ["Fondos", "Press Inclinado", "Pec Deck", "Elevaciones Laterales", "Press Militar", "Tríceps Polea"],
    "Día 2: Espalda-Bicep": ["Dominadas", "Remo Barra", "Jalón Pecho", "Face Pull", "Curl Bayesiano", "Curl Martillo"],
    "Día 3: Pierna": ["Sentadilla", "Hip Thrust", "Peso Muerto Rumano", "Elevacion de Pantorrillas", "Curl femoral sentado", "Abductores en maquina"],
    "Día 5: Torso": ["Press Inclinado", "Press Banca", "Remo Barra", "Jalón Pecho", "Fondos Lastre"],
    "Día 6: Brazos": ["Elevaciones Laterales", "Press Militar", "Press Francés", "Tríceps Polea", "Curl Araña", "Curl Martillo"]
}

# --- 4. TIMER ---
def timer_descanso():
    place = st.empty()
    bar = st.progress(0)
    for i in range(60, -1, -1):
        bar.progress((60-i)/60)
        place.markdown(f"### ⏳ Descanso: {i}s")
        time.sleep(1)
    place.markdown("### 🔔 ¡DALE!")
    st.audio("https://cdn.pixabay.com/audio/2022/03/15/audio_243469c434.mp3", autoplay=True)
    time.sleep(2)
    place.empty(); bar.empty()

# --- APP ---
st.title(f"💪 Hola, {USUARIO}")
if st.sidebar.button("Salir"):
    st.session_state.usuario_actual = None; st.rerun()

tab1, tab2 = st.tabs(["🏋️ Entrenar", "📈 Progreso"])

with tab1:
    dia = st.selectbox("Rutina:", list(rutina.keys()))
    st.divider()
    datos_guardar = []

    for ej in rutina[dia]:
        with st.expander(f"**{ej}**", expanded=True):
            if ej in IMAGENES: st.image(IMAGENES[ej], width=150)
            
            # --- LÓGICA DINÁMICA DE SERIES ---
            # Creamos una variable en memoria para contar series de este ejercicio
            key_count = f"count_{dia}_{ej}"
            if key_count not in st.session_state:
                st.session_state[key_count] = 1 # Empezamos con 1 serie
            
            # Mostramos las series actuales
            for i in range(1, st.session_state[key_count] + 1):
                c1, c2, c3 = st.columns([2, 2, 1])
                kb = f"{ej}_s{i}"
                with c1: p = st.text_input(f"S{i}", key=f"{kb}_p", placeholder="Kg", label_visibility="collapsed")
                with c2: r = st.text_input(f"S{i}", key=f"{kb}_r", placeholder="Reps", label_visibility="collapsed")
                with c3:
                    if st.checkbox("✅", key=f"{kb}_c"):
                        if f"t_{kb}" not in st.session_state:
                            timer_descanso()
                            st.session_state[f"t_{kb}"] = True
                        if p and r: datos_guardar.append([dia, ej, i, p, r])

            # BOTÓN PARA AGREGAR SERIE (+)
            if st.button(f"➕ Serie a {ej}", key=f"add_{ej}"):
                st.session_state[key_count] += 1
                st.rerun()
            
    st.divider()
    if st.button("💾 GUARDAR TODO", type="primary", use_container_width=True):
        if datos_guardar:
            now = datetime.now().strftime("%Y-%m-%d")
            filas = [[now, USUARIO] + d for d in datos_guardar]
            sheet_datos.append_rows(filas)
            st.balloons()
            st.success("Guardado!")
        else:
            st.warning("Marca alguna serie ✅")

with tab2:
    st.header(f"Historial de {USUARIO}")
    try:
        df = pd.DataFrame(sheet_datos.get_all_records())
        if not df.empty and "Usuario" in df.columns:
            df = df[df["Usuario"] == USUARIO] # Solo mis datos
            if not df.empty:
                df["Peso"] = pd.to_numeric(df["Peso"], errors='coerce')
                df["Fecha"] = pd.to_datetime(df["Fecha"])
                
                sel = st.selectbox("Ejercicio:", df["Ejercicio"].unique())
                df_c = df[df["Ejercicio"] == sel]
                
                st.line_chart(df_c, x="Fecha", y="Peso")
                st.metric("Récord", f"{df_c['Peso'].max()} Kg")
                st.dataframe(df_c.sort_values("Fecha", ascending=False))
            else: st.info("Sin datos aún.")
    except: st.error("Error leyendo datos.")
