import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Gym Tracker Pro", page_icon="💪", layout="wide")

# --- 1. DICCIONARIO DE IMÁGENES (Pega aquí los links de tus fotos) ---
# Puedes subir tus fotos a imgur.com y pegar el link directo (que termine en .jpg o .png)
IMAGENES = {
    "Press Inclinado": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Incline-bench-press-2.png/640px-Incline-bench-press-2.png",
    "Pec Deck": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Pec_Deck_Machine.JPG/640px-Pec_Deck_Machine.JPG",
    "Dominadas": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Pullup_w_Supinated_Grip.JPG/357px-Pullup_w_Supinated_Grip.JPG",
    "Sentadilla": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Squats.png/640px-Squats.png",
    # ... Si un ejercicio no tiene foto, no saldrá nada (no rompe la app)
}

# --- 2. CONEXIÓN INTELIGENTE (Igual que antes) ---
def conectar_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
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

# --- INTERFAZ PRINCIPAL ---
st.title("💪 Mi Gym Tracker")
sheet = conectar_google_sheet()

# Creamos dos pestañas
tab1, tab2 = st.tabs(["🏋️ Registrar Entrenamiento", "📈 Ver Mi Progreso"])

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    if sheet:
        dia = st.selectbox("¿Qué toca hoy?", list(rutina.keys()))
        
        with st.form("gym_form"):
            st.subheader(f"Rutina: {dia}")
            inputs = {}
            
            for ej in rutina[dia]:
                st.markdown(f"### {ej}")
                
                # Muestra foto si existe en el diccionario
                if ej in IMAGENES:
                    st.image(IMAGENES[ej], width=200)
                
                c1, c2 = st.columns(2)
                inputs[ej] = (c1.text_input("Kg", key=f"{ej}k"), c2.text_input("Reps", key=f"{ej}r"))
                st.divider()
            
            if st.form_submit_button("Guardar en la Nube ☁️"):
                fecha = datetime.now().strftime("%Y-%m-%d")
                data = []
                for ej, (k, r) in inputs.items():
                    if k and r:
                        # Convertimos a número para asegurar que el gráfico funcione luego
                        k = k.replace(",", ".") # Cambia comas por puntos
                        data.append([fecha, dia, ej, k, r])
                if data:
                    sheet.append_rows(data)
                    st.success("¡Guardado exitosamente!")
                else:
                    st.warning("Anota al menos un ejercicio.")

# --- PESTAÑA 2: GRÁFICOS ---
with tab2:
    st.header("Tu Evolución")
    
    if sheet:
        # Descargar datos
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Limpieza de datos para el gráfico
            df["Peso"] = pd.to_numeric(df["Peso"], errors='coerce')
            df["Fecha"] = pd.to_datetime(df["Fecha"])
            
            # Selector de ejercicio
            lista_ejercicios = df["Ejercicio"].unique()
            ejercicio_sel = st.selectbox("Selecciona un ejercicio para ver el gráfico:", lista_ejercicios)
            
            # Filtrar datos
            df_chart = df[df["Ejercicio"] == ejercicio_sel]
            
            # Dibujar gráfico
            st.line_chart(df_chart, x="Fecha", y="Peso")
            
            # Mostrar tabla de récords
            max_peso = df_chart["Peso"].max()
            st.metric(label=f"Récord Histórico en {ejercicio_sel}", value=f"{max_peso} Kg")
            
            st.dataframe(df_chart[["Fecha", "Peso", "Reps"]].sort_values("Fecha", ascending=False))
            
        else:
            st.info("Aún no hay datos suficientes para graficar.")
