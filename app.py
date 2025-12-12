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
@st.cache_data(ttl=60) # Guardamos en caché para que no lea Google Sheets a cada rato
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
        
        return imagenes, rutinas
    except Exception as e:
        return {}, {}

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
IMAGENES, RUTINAS = cargar_datos_config()
CLIENTE = get_client() # Cliente para guardar datos (no caché)

# --- TIMER MEJORADO ---
def timer(segundos):
    pl = st.empty(); bar = st.progress(0)
    for i in range(segundos, -1, -1):
        if segundos > 0: bar.progress((segundos-i)/segundos)
        pl.markdown(f"### ⏳ {i}s")
        time.sleep(1)
    pl.markdown("### 🔔 ¡SERIE LISTA!")
    bar.empty()
    st.audio("https://www.soundjay.com/buttons/sounds/beep-07.mp3", autoplay=True)
    time.sleep(3); pl.empty()

# --- FUNCIÓN DE EJERCICIO AISLADO (FRAGMENTO MÁGICO) ---
# Esto hace que cada ejercicio sea independiente y no recargue toda la página
@st.fragment
def mostrar_ejercicio(ejercicio, dia_rutina, tiempo_descanso):
    with st.expander(f"**{ejercicio}**", expanded=True):
        if ejercicio in IMAGENES: st.image(IMAGENES[ejercicio], width=150)
        
        kc = f"c_{dia_rutina}_{ejercicio}"
        if kc not in st.session_state: st.session_state[kc] = 1
        
        # Mostramos series
        datos_locales = []
        for i in range(1, st.session_state[kc] + 1):
            c1,c2,c3 = st.columns([2,2,1])
            kb = f"{ejercicio}_{i}"
            
            # Inputs
            p = c1.text_input(f"S{i}", key=f"p{kb}", placeholder="Kg", label_visibility="collapsed")
            r = c2.text_input(f"S{i}", key=f"r{kb}", placeholder="Reps", label_visibility="collapsed")
            
            # Checkbox y Timer
            with c3:
                if st.checkbox("✅", key=f"c{kb}"):
                    if f"t{kb}" not in st.session_state:
                        timer(tiempo_descanso)
                        st.session_state[f"t{kb}"] = True
                    # Guardamos temporalmente en session state para que el botón FINAL lo lea
                    if p and r:
                        st.session_state[f"DATA_{kb}"] = [dia_rutina, ejercicio, i, p, r]

        # Botón agregar serie (Solo recarga este fragmento)
        if st.button("➕", key=f"add{ejercicio}"):
            st.session_state[kc] += 1
            st.rerun()

# --- APP PRINCIPAL ---
st.title(f"Hola, {USUARIO} 💪")

with st.sidebar:
    if st.button("Cerrar Sesión"):
        st.session_state.user = None; st.rerun()

tab1, tab2, tab3 = st.tabs(["🏋️ Entrenar", "📈 Progreso", "⚙️ Configurar"])

# 1. ENTRENAR
with tab1:
    if not RUTINAS:
        st.info("⚠️ Crea una rutina en Configurar.")
    else:
        c_sel, c_time = st.columns([3, 1])
        with c_sel: dia = st.selectbox("Elige Rutina:", list(RUTINAS.keys()))
        with c_time: TIEMPO_SET = st.number_input("⏱️ (s)", min_value=10, value=60, step=10)

        st.divider()
        
        # Renderizamos cada ejercicio como un fragmento independiente
        for ej in RUTINAS[dia]:
            mostrar_ejercicio(ej, dia, TIEMPO_SET)

        st.divider()
        # Botón Guardar Global
        if st.button("💾 GUARDAR ENTRENAMIENTO", type="primary", use_container_width=True):
            datos_finales = []
            # Recopilamos datos de la memoria de la sesión
            for key in st.session_state:
                if key.startswith("DATA_"):
                    datos_finales.append(st.session_state[key])
            
            if datos_finales:
                sh = CLIENTE.open("Gym_Data").sheet1
                rows = [[datetime.now().strftime("%Y-%m-%d"), USUARIO] + d for d in datos_finales]
                sh.append_rows(rows)
                
                # Limpiamos datos guardados
                for key in list(st.session_state.keys()):
                    if key.startswith("DATA_") or key.startswith("t") or key.startswith("c") or key.startswith("p") or key.startswith("r"):
                        del st.session_state[key]
                
                st.balloons(); st.success("¡Guardado correctamente!")
                time.sleep(2); st.rerun()
            else: st.warning("No has marcado ninguna serie con ✅")

# 2. PROGRESO
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

# 3. CONFIGURAR
with tab3:
    st.header("⚙️ Configuración")
    t1, t2 = st.tabs(["Nuevo Ejercicio", "Nueva Rutina"])
    with t1:
        with st.form("ne"):
            n = st.text_input("Nombre"); u = st.text_input("URL GIF")
            if st.form_submit_button("Guardar"):
                CLIENTE.open("Gym_Data").worksheet("Ejercicios").append_row([n, u])
                st.success("Guardado. Recarga la app.")
    with t2:
        with st.form("nr"):
            n = st.text_input("Nombre Rutina")
            try: lista_ejs = CLIENTE.open("Gym_Data").worksheet("Ejercicios").col_values(1)[1:]
            except: lista_ejs = []
            ejs = st.multiselect("Ejercicios", lista_ejs)
            if st.form_submit_button("Crear"):
                CLIENTE.open("Gym_Data").worksheet("Rutinas_Config").append_rows([[n, e] for e in ejs])
                st.success("Creada.")
