import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gym Tracker", page_icon="💪")

# --- DEFINICIÓN DE LA RUTINA ---
rutina = {
    "Día 1: Pecho-Hombro-Tríceps": [
        "Fondos (Calentamiento)",
        "Press Banca Inclinado (Barra)",
        "Pec Deck (Mariposa)",
        "Máquina de Pecho",
        "Elevaciones Laterales",
        "Máquina Press Militar",
        "Tríceps Polea (Ejercicio 1)",
        "Tríceps Polea (Ejercicio 2)"
    ],
    "Día 2: Espalda-Bíceps": [
        "Dominadas (Calentamiento)",
        "Remo con Barra (Pesado)",
        "Jalón al Pecho",
        "Máquina de Remo (Agarre Abierto)",
        "Hombro Posterior (Polea/Facepull)",
        "Curl Bayesiano",
        "Curl Araña",
        "Curl Martillo"
    ],
    "Día 3: Pierna": [
        "Extensión Cuádriceps (Calentamiento)",
        "Sentadilla (Máquina o Libre)",
        "Hip Thrust",
        "Peso Muerto Rumano",
        "Pantorrillas con Mancuerna",
        "Máquina Femoral",
        "Abductores"
    ],
    "Día 5: Pecho-Espalda (Torso)": [
        "Press Banca Inclinado (Barra)",
        "Press Banca Normal (Barra)",
        "Remo con Barra",
        "Jalón al Pecho",
        "Pec Deck",
        "Fondos con Peso",
        "Remo en Máquina",
        "Jalón Dorsal Unilateral"
    ],
    "Día 6: Brazos": [
        "Elevaciones Laterales",
        "Press Militar",
        "Hombro Posterior (Coso de atrás)",
        "Press Rompecráneos",
        "Tríceps Polea 1",
        "Tríceps Polea 2",
        "Bíceps Araña",
        "Bíceps Bayesiano",
        "Bíceps Martillo"
    ]
}

# --- ARCHIVO DE GUARDADO ---
FILE_NAME = "mi_progreso_gym.csv"

# --- TÍTULO ---
st.title("🏋️‍♂️ Mi Gym Tracker")
st.write("Registra tus pesos y rompe tus límites.")

# --- SELECCIÓN DE DÍA ---
dia_seleccionado = st.selectbox("¿Qué toca entrenar hoy?", list(rutina.keys()))

# --- FORMULARIO DE ENTRADA ---
st.subheader(f"Rutina: {dia_seleccionado}")

datos_dia = []

# Creamos un formulario para que no se recargue la página con cada click
with st.form("entry_form"):
    col1, col2, col3 = st.columns([3, 1, 1])
    col1.write("**Ejercicio**")
    col2.write("**Peso (kg)**")
    col3.write("**Reps**")
    
    inputs = {} # Diccionario para guardar los inputs temporalmente

    for ejercicio in rutina[dia_seleccionado]:
        st.markdown(f"**{ejercicio}**")
        # Generamos 3 series por defecto para llenar
        for i in range(1, 4):
            c1, c2 = st.columns([3, 1])
            with c1:
                peso = st.text_input(f"Peso Serie {i}", key=f"{ejercicio}_w_{i}", placeholder="Ej: 20")
            with c2:
                reps = st.text_input(f"Reps Serie {i}", key=f"{ejercicio}_r_{i}", placeholder="Ej: 12")
            
            inputs[f"{ejercicio}_s{i}"] = (peso, reps)
        st.divider()

    # Botón de envío
    submitted = st.form_submit_button("💾 Guardar Entrenamiento")

    if submitted:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        nuevos_datos = []
        
        for ejercicio in rutina[dia_seleccionado]:
            for i in range(1, 4):
                peso, reps = inputs[f"{ejercicio}_s{i}"]
                if peso and reps: # Solo guardamos si escribiste algo
                    nuevos_datos.append({
                        "Fecha": fecha_hoy,
                        "Día": dia_seleccionado,
                        "Ejercicio": ejercicio,
                        "Serie": i,
                        "Peso": peso,
                        "Reps": reps
                    })
        
        if nuevos_datos:
            df_nuevo = pd.DataFrame(nuevos_datos)
            
            # Cargar archivo existente o crear uno nuevo
            if os.path.exists(FILE_NAME):
                df_antiguo = pd.read_csv(FILE_NAME)
                df_final = pd.concat([df_antiguo, df_nuevo], ignore_index=True)
            else:
                df_final = df_nuevo
            
            df_final.to_csv(FILE_NAME, index=False)
            st.success("✅ ¡Entrenamiento guardado con éxito!")
        else:
            st.warning("⚠️ No has anotado ningún dato.")

# --- VISUALIZAR PROGRESO ---
st.header("📈 Historial Reciente")
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
    # Mostramos los últimos registros primero
    st.dataframe(df.tail(10).sort_index(ascending=False), use_container_width=True)
    
    # Botón para descargar tu Excel
    with open(FILE_NAME, "rb") as file:
        st.download_button(
            label="📥 Descargar todo mi historial (CSV)",
            data=file,
            file_name="historial_gym.csv",
            mime="text/csv"
        )
else:
    st.info("Aún no hay registros. ¡A entrenar!")
