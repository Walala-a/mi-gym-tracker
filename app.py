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
            with st.expander(f"**{ej}**", expanded=True):
                if ej in IMAGENES: st.image(IMAGENES[ej], width=150)
                
                kc = f"c_{dia}_{ej}"
                if kc not in st.session_state: st.session_state[kc] = 1
                
                for i in range(1, st.session_state[kc] + 1):
                    c1,c2,c3 = st.columns([2,2,1])
                    kb = f"{ej}_{i}"
                    with c1: p = st.text_input(f"S{i}", key=f"p{kb}", placeholder="Kg", label_visibility="collapsed")
                    with c2: r = st.text_input(f"S{i}", key=f"r{kb}", placeholder="Reps", label_visibility="collapsed")
                    with c3:
                        # CHECKBOX DEL TIMER
                        if st.checkbox("✅", key=f"c{kb}"):
                            if f"t{kb}" not in st.session_state:
                                # PASAMOS LA VARIABLE DEL SIDEBAR AL TIMER
                                timer(TIEMPO_DESCANSO)
                                st.session_state[f"t{kb}"] = True
                            if p and r: datos.append([dia, ej, i, p, r])
                
                if st.button(f"➕", key=f"add{ej}"):
                    st.session_state[kc] += 1; st.rerun()
                    
        if st.button("💾 GUARDAR", type="primary", use_container_width=True):
            if datos:
                sh = CLIENTE.open("Gym_Data").sheet1
                rows = [[datetime.now().strftime("%Y-%m-%d"), USUARIO] + d for d in datos]
                sh.append_rows(rows)
                st.balloons(); st.success("Guardado!")
            else: st.warning("Marca series ✅")

# 2. PROGRESO
with tab2:
    try:
        df = pd.DataFrame(CLIENTE.open("Gym_Data").sheet1.get_all_records())
        if not df.empty and "Usuario" in df.columns:
            df = df[df["Usuario"] == USUARIO]
            if not df.empty:
                df["Peso"] = pd.to_numeric(df["Peso"], errors='coerce')
                df["Fecha"] = pd.to_datetime(df["Fecha"])
                ej = st.selectbox("Ejercicio:", df["Ejercicio"].unique())
                st.line_chart(df[df["Ejercicio"] == ej], x="Fecha", y="Peso")
            else: st.info("Sin datos.")
    except: st.error("Error datos.")

# 3. CONFIGURAR
with tab3:
    st.header("⚙️ Config")
    t1, t2 = st.tabs(["Nuevo Ejercicio", "Nueva Rutina"])
    with t1:
        with st.form("ne"):
            n = st.text_input("Nombre"); u = st.text_input("URL GIF")
            if st.form_submit_button("Guardar"):
                CLIENTE.open("Gym_Data").worksheet("Ejercicios").append_row([n, u])
                st.success("Guardado")
    with t2:
        with st.form("nr"):
            n = st.text_input("Nombre Rutina")
            ejs = st.multiselect("Ejercicios", CLIENTE.open("Gym_Data").worksheet("Ejercicios").col_values(1)[1:])
            if st.form_submit_button("Crear"):
                CLIENTE.open("Gym_Data").worksheet("Rutinas_Config").append_rows([[n, e] for e in ejs])
                st.success("Creada")
