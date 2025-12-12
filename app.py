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
        try:
            ws_img = sh.worksheet("Ejercicios")
            imagenes = {d["Nombre"]: d["URL_Imagen"] for d in ws_img.get_all_records() if d["URL_Imagen"]}
        except: imagenes = {}
        
        # 2. Rutinas
        try:
            ws_rut = sh.worksheet("Rutinas_Config")
            rutinas = {}
            for r in ws_rut.get_all_records():
                nombre = r["Rutina"]
                if nombre not in rutinas: rutinas[nombre] = []
                rutinas[nombre].append(r["Ejercicio"])
        except: rutinas = {}
        
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

# --- TIMER MEJORADO ---
def timer(segundos):
    pl = st.empty(); bar = st.progress(0)
    for i in range(segundos, -1, -1):
        if segundos > 0: bar.progress((segundos-i)/segundos)
        pl.markdown(f"### ⏳ {i}s")
        time.sleep(1)
    
    pl.markdown("### 🔔 ¡SERIE LISTA!")
    bar.empty()
    # Sonido corto tipo 'Beep'
    st.audio("https://www.soundjay.com/buttons/sounds/beep-07.mp3", autoplay=True)
    time.sleep(3); pl.empty()

# --- APP PRINCIPAL ---
st.title(f"Hola, {USUARIO} 💪")

# Botón Salir en la barra lateral
with st.sidebar:
    if st.button("Cerrar Sesión"):
        st.session_state.user = None; st.rerun()

tab1, tab2, tab3 = st.tabs(["🏋️ Entrenar", "📈 Progreso", "⚙️ Configurar"])

# 1. PESTAÑA ENTRENAR
with tab1:
    if not RUTINAS:
        st.info("⚠️ No tienes rutinas. Ve a 'Configurar' para crear una.")
    else:
        # --- ZONA DE CONFIGURACIÓN DEL ENTRENAMIENTO ---
        c_sel, c_time = st.columns([3, 1])
        with c_sel:
            dia = st.selectbox("Elige Rutina:", list(RUTINAS.keys()))
        with c_time:
            # AQUÍ ESTÁ EL RELOJ EDITABLE
            TIEMPO_SET = st.number_input("⏱️ Tiempo Descanso (s)", min_value=10, value=60, step=10)

        st.divider()
        datos = []
        
        for ej in RUTINAS[dia]:
            # --- AQUÍ ESTABA EL ERROR, YA CORREGIDO ---
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
                        if st.checkbox("✅", key=f"c{kb}"):
                            if f"t{kb}" not in st.session_state:
                                # Usamos el tiempo que definiste arriba
                                timer(TIEMPO_SET)
                                st.session_state[f"t{kb}"] = True
                            if p and r: datos.append([dia, ej, i, p, r])
                
                # Botón pequeño para añadir serie
                if st.button("➕", key=f"add{ej}"):
                    st.session_state[kc] += 1; st.rerun()
                    
        st.divider()
        if st.button("💾 GUARDAR ENTRENAMIENTO", type="primary", use_container_width=True):
            if datos:
                sh = CLIENTE.open("Gym_Data").sheet1
                rows = [[datetime.now().strftime("%Y-%m-%d"), USUARIO] + d for d in datos]
                sh.append_rows(rows)
                st.balloons(); st.success("¡Guardado correctamente!")
            else: st.warning("No has marcado ninguna serie con ✅")

# 2. PESTAÑA PROGRESO
with tab2:
    try:
        sh = CLIENTE.open("Gym_Data").sheet1
        df = pd.DataFrame(sh.get_all_records())
        if not df.empty and "Usuario" in df.columns:
            df = df[df["Usuario"] == USUARIO]
            if not df.empty:
                df["Peso"] = pd.to_numeric(df["Peso"], errors='coerce')
                df["Fecha"] = pd.to_datetime(df["Fecha"])
                ej = st.selectbox("Ver ejercicio:", df["Ejercicio"].unique())
                st.line_chart(df[df["Ejercicio"] == ej], x="Fecha", y="Peso")
                st.dataframe(df[df["Ejercicio"] == ej].sort_values("Fecha", ascending=False))
            else: st.info("No hay datos tuyos todavía.")
    except: st.error("Error leyendo datos.")

# 3. PESTAÑA CONFIGURAR
with tab3:
    st.header("⚙️ Configuración")
    t1, t2 = st.tabs(["Nuevo Ejercicio", "Nueva Rutina"])
    
    with t1:
        with st.form("ne"):
            n = st.text_input("Nombre Ejercicio"); u = st.text_input("URL Imagen/GIF")
            if st.form_submit_button("Guardar"):
                CLIENTE.open("Gym_Data").worksheet("Ejercicios").append_row([n, u])
                st.success("Guardado. Recarga la app.")
    
    with t2:
        with st.form("nr"):
            n = st.text_input("Nombre Rutina")
            # Carga dinámica de ejercicios para elegir
            try:
                lista_ejs = CLIENTE.open("Gym_Data").worksheet("Ejercicios").col_values(1)[1:]
            except: lista_ejs = []
            
            ejs = st.multiselect("Selecciona Ejercicios", lista_ejs)
            
            if st.form_submit_button("Crear Rutina"):
                if n and ejs:
                    CLIENTE.open("Gym_Data").worksheet("Rutinas_Config").append_rows([[n, e] for e in ejs])
                    st.success("Rutina Creada. Recarga la app.")
                else: st.error("Faltan datos")
