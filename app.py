import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Gym Tracker Pro", page_icon="💪", layout="wide")

# --- 1. DICCIONARIO DE IMÁGENES Y GIFS ---
IMAGENES = {
    "Fondos": "https://www.lyfta.app/_next/image?url=https%3A%2F%2Flyfta.app%2Fimages%2Fexercises%2F00091101.png&w=3840&q=75",
    "Press Inclinado": "https://www.lyfta.app/thumbnails/12991201.jpg",
    "Pec Deck": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Pec-Deck-Fly.gif",
    "Elevaciones Laterales": "https://fitcron.com/wp-content/uploads/2021/04/03111301-Dumbbell-Full-Can-Lateral-Raise_Shoulders_720.gif",
    "Press Militar": "https://i.pinimg.com/originals/67/b8/5a/67b85add1691a2620c3101b49a021899.gif",
    "Tríceps Polea": "https://treinototal.com.br/wp-content/uploads/2023/06/triceps-corda.gif",
    "Remo Barra": "https://fitcron.com/wp-content/uploads/2021/04/01181301-Barbell-Reverse-Grip-Bent-over-Row_Back-FIX_720.gif",
    "Jalón Pecho": "https://vitruve.fit/wp-content/uploads/2021/11/vitruvs.gif",
    "Face Pull": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Face-Pull.gif",
    "Curl Bayesiano": "https://cdn.shopify.com/s/files/1/0052/7043/7978/articles/squat-muscles-worked_1024x1024.jpg",
    "Curl Martillo": "https://media.giphy.com/media/eFxpNpVp4b55iWfgAS/giphy.gif",
    "Hip Thrust": "https://cdn.shopify.com/s/files/1/0052/7043/7978/articles/squat-muscles-worked_1024x1024.jpg",
    "Peso Muerto Rumano": "https://media.giphy.com/media/eFxpNpVp4b55iWfgAS/giphy.gif",
    "Elevacion de Pantorrillas": "https://cdn.shopify.com/s/files/1/0052/7043/7978/articles/squat-muscles-worked_1024x1024.jpg",
    "Curl femoral sentado": "https://media.giphy.com/media/eFxpNpVp4b55iWfgAS/giphy.gif",
    "Abductores en maquina": "https://cdn.shopify.com/s/files/1/0052/7043/7978/articles/squat-muscles-worked_1024x1024.jpg",
    "Remo Barra": "https://media.giphy.com/media/eFxpNpVp4b55iWfgAS/giphy.gif",
    "Jalón Pecho": "https://cdn.shopify.com/s/files/1/0052/7043/7978/articles/squat-muscles-worked_1024x1024.jpg",
    "Fondos Lastre": "https://media.giphy.com/media/eFxpNpVp4b55iWfgAS/giphy.gif",
    "Press Militar": "https://cdn.shopify.com/s/files/1/0052/7043/7978/articles/squat-muscles-worked_1024x1024.jpg",
    "Press Francés": "https://media.giphy.com/media/eFxpNpVp4b55iWfgAS/giphy.gif",
    "Tríceps Polea": "https://cdn.shopify.com/s/files/1/0052/7043/7978/articles/squat-muscles-worked_1024x1024.jpg",
    "Curl Araña": "https://media.giphy.com/media/eFxpNpVp4b55iWfgAS/giphy.gif",
    "Curl Martillo": "https://cdn.shopify.com/s/files/1/0052/7043/7978/articles/squat-muscles-worked_1024x1024.jpg",
    
    
}

# --- 2. CONEXIÓN INTELIGENTE (PC O NUBE) ---
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
    "Día 1: Pecho-Hombro-Tríceps": ["Fondos", "Press Inclinado", "Pec Deck", "Elevaciones Laterales", "Press Militar", "Tríceps Polea"],
    "Día 2: Espalda-Bicep": ["Dominadas", "Remo Barra", "Jalón Pecho", "Face Pull", "Curl Bayesiano", "Curl Martillo"],
    "Día 3: Pierna": ["Sentadilla", "Hip Thrust", "Peso Muerto Rumano", "Elevacion de Pantorrillas", "Curl femoral sentado", "Abductores en maquina"],
    "Día 5: Torso": ["Press Inclinado", "Press Banca", "Remo Barra", "Jalón Pecho", "Fondos Lastre"],
    "Día 6: Brazos": ["Elevaciones Laterales", "Press Militar", "Press Francés", "Tríceps Polea", "Curl Araña", "Curl Martillo"]
}

# --- INTERFAZ PRINCIPAL ---
st.title("💪 Mi Gym Tracker")
sheet = conectar_google_sheet()

tab1, tab2 = st.tabs(["🏋️ Registrar Entrenamiento", "📈 Ver Mi Progreso"])

# --- PESTAÑA 1: REGISTRO (CON SERIES) ---
with tab1:
    if sheet:
        dia = st.selectbox("¿Qué toca hoy?", list(rutina.keys()))
        
        with st.form("gym_form"):
            st.subheader(f"Rutina: {dia}")
            inputs = [] # Lista para guardar los datos temporalmente
            
            for ej in rutina[dia]:
                st.markdown(f"### {ej}")
                if ej in IMAGENES:
                    st.image(IMAGENES[ej], width=200)
                
                # Encabezados pequeños
                c_lbl1, c_lbl2 = st.columns(2)
                c_lbl1.caption("Peso (Kg)")
                c_lbl2.caption("Repeticiones")

                # Generamos 4 espacios para series (Serie 1 a 4)
                for i in range(1, 5): 
                    c1, c2 = st.columns(2)
                    # Usamos label_visibility="collapsed" para que no repita el titulo "Peso" 4 veces
                    peso = c1.text_input(f"S{i}", key=f"{ej}_s{i}_k", placeholder=f"Serie {i}", label_visibility="collapsed")
                    reps = c2.text_input(f"S{i}", key=f"{ej}_s{i}_r", placeholder="Reps", label_visibility="collapsed")
                    
                    # Guardamos la referencia para procesarla después
                    inputs.append({"ejercicio": ej, "serie": i, "peso": peso, "reps": reps})
                
                st.divider()
            
            if st.form_submit_button("Guardar Entrenamiento 💾"):
                fecha = datetime.now().strftime("%Y-%m-%d")
                filas_a_subir = []
                
                for item in inputs:
                    # Solo guardamos si se escribieron datos (para ignorar las series vacías)
                    if item["peso"] and item["reps"]:
                        p = item["peso"].replace(",", ".")
                        # Estructura: Fecha, Día, Ejercicio, Serie, Peso, Reps
                        filas_a_subir.append([fecha, dia, item["ejercicio"], item["serie"], p, item["reps"]])
                
                if filas_a_subir:
                    sheet.append_rows(filas_a_subir)
                    st.success(f"¡Se han guardado {len(filas_a_subir)} series correctamente!")
                else:
                    st.warning("No has anotado ningún dato.")

# --- PESTAÑA 2: GRÁFICOS ---
with tab2:
    st.header("Tu Evolución")
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if not df.empty:
            df["Peso"] = pd.to_numeric(df["Peso"], errors='coerce')
            df["Fecha"] = pd.to_datetime(df["Fecha"])
            
            lista_ejercicios = df["Ejercicio"].unique()
            ejercicio_sel = st.selectbox("Selecciona ejercicio:", lista_ejercicios)
            
            df_chart = df[df["Ejercicio"] == ejercicio_sel]
            
            # Gráfico de Peso máximo movido por día
            st.line_chart(df_chart, x="Fecha", y="Peso")
            
            max_peso = df_chart["Peso"].max()
            st.metric(label=f"Récord Personal (PR)", value=f"{max_peso} Kg")
            st.dataframe(df_chart[["Fecha", "Serie", "Peso", "Reps"]].sort_values("Fecha", ascending=False))
        else:
            st.info("Aún no hay datos.")



