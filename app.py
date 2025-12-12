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

# --- CARGA DE DATOS DINÁMICOS ---
def cargar_datos_config():
    client = get_client()
    if not client: return {}, {}
    
    try:
        sh = client.open("Gym_Data")
        
        # 1. Cargar Imágenes
        ws_ej = sh.worksheet("Ejercicios")
        lista_ej = ws_ej.get_all_records()
        imagenes = {d["Nombre"]: d["URL_Imagen"] for d in lista_ej if d["URL_Imagen"]}
        
        # 2. Cargar Rutinas
        ws_rut = sh.worksheet("Rutinas_Config")
        lista_rut = ws_rut.get_all_records()
        rutinas = {}
        for r in lista_rut:
            nombre = r["Rutina"]
            ejercicio = r["Ejercicio"]
            if nombre not in rutinas: rutinas[nombre] = []
            rutinas[nombre].append(ejercicio)
            
        return imagenes, rutinas, client
    except Exception as e:
        st.error(f"Faltan pestañas en Google Sheets: {e}")
        return {}, {}, client

# --- LOGIN ---
def login():
    if "user" in st.session_state and st.session_state.user: return True
    st.markdown("<h1 style='text-align: center;'>🔒 Gym Login</h1>", unsafe_allow_html=True)
    
    client = get_client()
    if not client: return False
    
    try:
        ws = client.open("Gym_Data").worksheet("Usuarios")
    except:
        st.error("Crea la pestaña 'Usuarios' en Sheets!")
        return False
        
    t1, t2 = st.tabs(["Entrar", "Registrar"])
    with t1:
        with st.form("lo"):
            u = st.text_input("Usuario")
            p = st.text_input("Pass", type="password")
            if st.form_submit_button("Entrar"):
                users = ws.get_all_records()
                for x in users:
                    if str(x["Usuario"]) == u and str(x["Password"]) == p:
                        st.session_state.user = u
                        st.rerun()
                st.error("Error")
    with t2:
        with st.form("re"):
            nu = st.text_input("Nuevo User")
            np = st.text_input("Nueva Pass", type="password")
            if st.form_submit_button("Crear"):
                ws.append_row([nu, np])
                st.success("Creado!")
    return False

if not login(): st.stop()

# --- VARIABLES ---
USUARIO = st.session_state.user
IMAGENES, RUTINAS, CLIENTE = cargar_datos_config()

# --- TIMER ---
def timer():
    pl = st.empty(); bar = st.progress(0)
    for i in range(60, -1, -1):
        bar.progress((60-i)/60)
        pl.markdown(f"### ⏳ {i}s")
        time.sleep(1)
    pl.markdown("### 🔔 DALE!")
    st.audio("https://cdn.pixabay.com/audio/2022/03/15/audio_243469c434.mp3", autoplay=True)
    time.sleep(2); pl.empty(); bar.empty()

# --- APP ---
st.title(f"Hola, {USUARIO} 💪")
if st.sidebar.button("Salir"): st.session_state.user = None; st.rerun()

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3 = st.tabs(["🏋️ Entrenar", "📈 Progreso", "⚙️ Configurar"])

# 1. ENTRENAR
with tab1:
    if not RUTINAS:
        st.info("⚠️ No hay rutinas creadas. Ve a la pestaña 'Configurar' para crear una.")
    else:
        dia = st.selectbox("Selecciona Rutina:", list(RUTINAS.keys()))
        st.divider()
        datos = []
        
        for ej in RUTINAS[dia]:
            with st.expander(f"**{ej}**", expanded=True):
                if ej in IMAGENES: st.image(IMAGENES[ej], width=150)
                
                key_c = f"c_{dia}_{ej}"
                if key_c not in st.session_state: st.session_state[key_c] = 1
                
                for i in range(1, st.session_state[key_c] + 1):
                    c1,c2,c3 = st.columns([2,2,1])
                    kb = f"{ej}_{i}"
                    with c1: p = st.text_input(f"S{i}", key=f"p{kb}", placeholder="Kg", label_visibility="collapsed")
                    with c2: r = st.text_input(f"S{i}", key=f"r{kb}", placeholder="Reps", label_visibility="collapsed")
                    with c3:
                        if st.checkbox("✅", key=f"c{kb}"):
                            if f"t{kb}" not in st.session_state:
                                timer(); st.session_state[f"t{kb}"] = True
                            if p and r: datos.append([dia, ej, i, p, r])
                
                if st.button(f"➕ Serie", key=f"add{ej}"):
                    st.session_state[key_c] += 1
                    st.rerun()
                    
        if st.button("💾 GUARDAR ENTRENAMIENTO", type="primary"):
            if datos:
                sh = CLIENTE.open("Gym_Data").sheet1
                now = datetime.now().strftime("%Y-%m-%d")
                rows = [[now, USUARIO] + d for d in datos]
                sh.append_rows(rows)
                st.balloons(); st.success("Guardado!")
            else: st.warning("Nada marcado")

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
                
                ej = st.selectbox("Ejercicio:", df["Ejercicio"].unique())
                df_c = df[df["Ejercicio"] == ej]
                st.line_chart(df_c, x="Fecha", y="Peso")
                st.dataframe(df_c.sort_values("Fecha", ascending=False))
            else: st.info("Sin datos.")
    except: st.error("Error leyendo datos.")

# 3. CONFIGURAR (NUEVO)
with tab3:
    st.header("⚙️ Gestión del Gym")
    
    st_conf1, st_conf2 = st.tabs(["➕ Nuevo Ejercicio", "📝 Crear Rutina"])
    
    # AGREGAR EJERCICIO
    with st_conf1:
        with st.form("add_ej"):
            ne_nombre = st.text_input("Nombre del Ejercicio (Ej: Curl Z)")
            ne_url = st.text_input("Link GIF/Imagen (Opcional)")
            if st.form_submit_button("Guardar Ejercicio"):
                try:
                    ws_ej = CLIENTE.open("Gym_Data").worksheet("Ejercicios")
                    ws_ej.append_row([ne_nombre, ne_url])
                    st.success(f"Ejercicio '{ne_nombre}' agregado! Recarga la app.")
                except: st.error("Error al guardar en hoja Ejercicios")

    # CREAR RUTINA
    with st_conf2:
        with st.form("add_rut"):
            nr_nombre = st.text_input("Nombre Nueva Rutina (Ej: Hombro Mortal)")
            
            # Obtenemos lista de ejercicios disponibles para elegir
            ws_ej = CLIENTE.open("Gym_Data").worksheet("Ejercicios")
            lista_raw = ws_ej.col_values(1)[1:] # Columna 1, quitando título
            
            ejercicios_selec = st.multiselect("Selecciona los ejercicios:", lista_raw)
            
            if st.form_submit_button("Crear Rutina"):
                if nr_nombre and ejercicios_selec:
                    try:
                        ws_rut = CLIENTE.open("Gym_Data").worksheet("Rutinas_Config")
                        # Preparamos filas: NombreRutina | Ejercicio
                        filas_rutina = [[nr_nombre, ej] for ej in ejercicios_selec]
                        ws_rut.append_rows(filas_rutina)
                        st.success(f"Rutina '{nr_nombre}' creada! Recarga la app para verla.")
                    except: st.error("Error guardando rutina")
                else:
                    st.warning("Escribe un nombre y elige ejercicios.")
