import streamlit as st
import pandas as pd
from datetime import datetime
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gym Tracker Pro", page_icon="🏋️", layout="wide")

# --- 1. CONEXIÓN GOOGLE SHEETS (MEJORADA) ---
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

# --- 2. GESTIÓN DE USUARIOS (LOGIN Y REGISTRO) ---
def gestion_usuarios():
    """Maneja el Login y el Registro usando Google Sheets"""
    if "usuario_actual" not in st.session_state:
        st.session_state.usuario_actual = None

    if st.session_state.usuario_actual:
        return True # Ya está logueado

    st.markdown("<h1 style='text-align: center;'>🔒 Gym Tracker</h1>", unsafe_allow_html=True)
    
    # Conectamos para buscar usuarios
    client = get_google_sheet_client()
    if not client:
        return False

    try:
        # Abrimos la hoja de usuarios
        hoja_usuarios = client.open("Gym_Data").worksheet("Usuarios")
    except:
        st.error("⚠️ No encuentro la pestaña 'Usuarios' en tu Google Sheet. Por favor créala.")
        return False

    # Pestañas de Login / Crear Cuenta
    tab_login, tab_registro = st.tabs(["Iniciar Sesión", "Crear Cuenta Nueva"])

    # --- LOGIN ---
    with tab_login:
        with st.form("login_form"):
            user = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Entrar ➡️", use_container_width=True)

            if submit:
                try:
                    # Descargamos todos los usuarios
                    registros = hoja_usuarios.get_all_records()
                    # Buscamos coincidencia
                    usuario_encontrado = False
                    for registro in registros:
                        # Convertimos a string por si acaso Google Sheets lo detecta como número
                        if str(registro["Usuario"]) == user and str(registro["Password"]) == password:
                            st.session_state.usuario_actual = user
                            usuario_encontrado = True
                            break
                    
                    if usuario_encontrado:
                        st.success(f"¡Hola de nuevo, {user}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
                except Exception as e:
                    st.error(f"Error al leer usuarios: {e}")

    # --- REGISTRO ---
    with tab_registro:
        st.warning("⚠️ Recuerda tu contraseña, no se puede recuperar.")
        with st.form("register_form"):
            new_user = st.text_input("Elige un Usuario")
            new_pass = st.text_input("Elige una Contraseña", type="password")
            new_pass_confirm = st.text_input("Repite la Contraseña", type="password")
            submit_reg = st.form_submit_button("Crear Usuario 🆕", use_container_width=True)

            if submit_reg:
                if new_pass != new_pass_confirm:
                    st.error("Las contraseñas no coinciden.")
                elif len(new_user) < 3:
                    st.error("El usuario debe tener al menos 3 letras.")
                else:
                    # Comprobar si ya existe
                    registros = hoja_usuarios.get_all_records()
                    nombres_existentes = [str(r["Usuario"]) for r in registros]
                    
                    if new_user in nombres_existentes:
                        st.error("¡Ese usuario ya existe! Elige otro.")
                    else:
                        # Guardar en Google Sheets
                        hoja_usuarios.append_row([new_user, new_pass])
                        st.success("¡Cuenta creada! Ahora puedes iniciar sesión.")

    return False

# Si no está logueado, detenemos la app
if not gestion_usuarios():
    st.stop()

# --- USUARIO LOGUEADO ---
USUARIO = st.session_state.usuario_actual
client = get_google_sheet_client()
sheet_datos = client.open("Gym_Data").sheet1 # La hoja donde guardamos los entrenos

# --- 3. DICCIONARIO DE IMÁGENES ---
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

# --- 4. TIMER Y LÓGICA ---
def timer_descanso():
    placeholder = st.empty()
    progress_bar = st.progress(0)
    for i in range(60, -1, -1):
        progress_bar.progress((60 - i) / 60)
        placeholder.markdown(f"### ⏳ Descanso: {i}s")
        time.sleep(1)
    placeholder.markdown("### 🔔 ¡DALE!")
    st.audio("https://cdn.pixabay.com/audio/2022/03/15/audio_243469c434.mp3", autoplay=True)
    time.sleep(2)
    placeholder.empty()
    progress_bar.empty()

rutina = {
    "Día 1: Pecho-Hombro-Tríceps": ["Fondos", "Press Inclinado", "Pec Deck", "Elevaciones Laterales", "Press Militar", "Tríceps Polea"],
    "Día 2: Espalda-Bicep": ["Dominadas", "Remo Barra", "Jalón Pecho", "Face Pull", "Curl Bayesiano", "Curl Martillo"],
    "Día 3: Pierna": ["Sentadilla", "Hip Thrust", "Peso Muerto Rumano", "Elevacion de Pantorrillas", "Curl femoral sentado", "Abductores en maquina"],
    "Día 5: Torso": ["Press Inclinado", "Press Banca", "Remo Barra", "Jalón Pecho", "Fondos Lastre"],
    "Día 6: Brazos": ["Elevaciones Laterales", "Press Militar", "Press Francés", "Tríceps Polea", "Curl Araña", "Curl Martillo"]
}

# --- INTERFAZ PRINCIPAL ---
st.title(f"💪 Hola, {USUARIO}")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.usuario_actual = None
    st.rerun()

tab1, tab2 = st.tabs(["🏋️ Entrenar", "📈 Mi Progreso"])

with tab1:
    dia = st.selectbox("Elige tu rutina de hoy:", list(rutina.keys()))
    st.divider()
    
    datos_a_guardar = []
    
    for ej in rutina[dia]:
        with st.expander(f"**{ej}**", expanded=True):
            if ej in IMAGENES:
                st.image(IMAGENES[ej], width=150)
            
            st.markdown("---")
            for i in range(1, 5):
                c1, c2, c3 = st.columns([2, 2, 1])
                key_base = f"{ej}_s{i}"
                
                with c1:
                    peso = st.text_input(f"S{i}", key=f"{key_base}_p", placeholder="Kg", label_visibility="collapsed")
                with c2:
                    reps = st.text_input(f"S{i}", key=f"{key_base}_r", placeholder="Reps", label_visibility="collapsed")
                with c3:
                    if st.checkbox("✅", key=f"{key_base}_c"):
                        if f"t_{key_base}" not in st.session_state:
                            timer_descanso()
                            st.session_state[f"t_{key_base}"] = True
                        if peso and reps:
                             datos_a_guardar.append([dia, ej, i, peso, reps])
    
    st.divider()
    if st.button(f"💾 GUARDAR ENTRENAMIENTO DE {USUARIO.upper()}", type="primary", use_container_width=True):
        if datos_a_guardar:
            fecha = datetime.now().strftime("%Y-%m-%d")
            # Agregamos USUARIO a la fila
            filas = [[fecha, USUARIO] + f for f in datos_a_guardar]
            sheet_datos.append_rows(filas)
            st.balloons()
            st.success("¡Datos guardados!")
        else:
            st.warning("No hay series marcadas.")

with tab2:
    st.header(f"Progreso de {USUARIO}")
    data = sheet_datos.get_all_records()
    df = pd.DataFrame(data)
    
    if not df.empty and "Usuario" in df.columns:
        # FILTRO IMPORTANTE: SOLO DATOS DEL USUARIO
        df = df[df["Usuario"] == USUARIO]
        
        if not df.empty:
            df["Peso"] = pd.to_numeric(df["Peso"], errors='coerce')
            df["Fecha"] = pd.to_datetime(df["Fecha"])
            
            ejercicio = st.selectbox("Ver ejercicio:", df["Ejercicio"].unique())
            df_chart = df[df["Ejercicio"] == ejercicio]
            
            st.line_chart(df_chart, x="Fecha", y="Peso")
            st.metric("Récord Personal", f"{df_chart['Peso'].max()} Kg")
            st.dataframe(df_chart.sort_values("Fecha", ascending=False))
        else:
            st.info("No tienes datos registrados aún.")
    else:
        st.info("Base de datos vacía o sin formato de usuarios.")
