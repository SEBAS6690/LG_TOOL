import streamlit as st
import pandas as pd
import datetime
import cv2
import numpy as np
import requests

# 1. CONFIGURACIÓN DE LA PÁGINA (Estilo Industrial / Corporativo)
st.set_page_config(
    page_title="Smart Tool Check-In | Lundin Gold",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para la interfaz del Tótem
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #002F6C; color: white; font-weight: bold; border-radius: 6px; height: 45px; }
    .stButton>button:hover { background-color: #001F4D; color: white; border: 1px solid #FFC72C; }
    .title-banner { padding: 20px; background-color: #002F6C; color: white; border-radius: 8px; margin-bottom: 25px; border-bottom: 5px solid #FFC72C; }
    .danger-box { padding: 20px; background-color: #FADBD8; border-left: 6px solid #CD6155; border-radius: 5px; margin-bottom: 15px; color: #78281F; }
    .success-box { padding: 20px; background-color: #D4EFDF; border-left: 6px solid #27AE60; border-radius: 5px; margin-bottom: 15px; color: #145A32; }
    .metric-card { background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #E5E7E9; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# 2. HISTORIAL LOCAL TEMPORAL (Para mostrar en pantalla mientras carga)
if 'registro_inspecciones' not in st.session_state:
    st.session_state.registro_inspecciones = []

# 3. DICCIONARIO MAESTRO DE ACTIVOS# 3. DICCIONARIO MAESTRO DE ACTIVOS (Corregido y Verificado)
HERRAMIENTAS_DB = {
    "HERR-AMO-045": {
        "nombre": "Amoladora Angular de 4.5\"",
        "categoria": "Corte y Desbaste",
        "marca": "DeWalt",
        "serial": "DW-2026-9941X",
        "imagen": "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?q=80&w=600&auto=format&fit=crop",
        "puntos": [
            "⚠️ **Punto 1 (Empuñadura):** ¿La empuñadura auxiliar está instalada, limpia y firme?",
            "⚠️ **Punto 2 (Guarda):** ¿La carcasa metálica está fija y orientada entre el disco y su mano?",
            "⚠️ **Punto 3 (Gatillo):** ¿El interruptor 'hombre muerto' se desactiva automáticamente al soltarlo?"
        ]
    },
    "HERR-NEU-075": {
        "nombre": "Pistola de Impacto Neumática 3/4\"",
        "categoria": "Ajuste Mecánico / Torque",
        "marca": "Chicago Pneumatic",
        "serial": "CP-772H-00542",
        "imagen": "https://images.unsplash.com/photo-1620917260582-8494b281b376?q=80&w=600&auto=format&fit=crop",
        "puntos": [
            "⚠️ **Punto 1 (Retención):** ¿El dado tiene su O-ring y pasador de seguridad colocados?",
            "⚠️ **Punto 2 (Carcasa/Goma):** ¿El recubrimiento absorbente de vibración en el mango está intacto?",
            "⚠️ **Punto 3 (Gatillo):** ¿El gatillo se mueve libremente sin atascos mecánicos?"
        ]
    },
    "ELE-TL-001": {
        "nombre": "Taladro Percutor Industrial",
        "categoria": "Perforación / Construcción",
        "marca": "Bosch Heavy Duty",
        "serial": "BSH-GSB20-8831",
        "imagen": "https://images.unsplash.com/photo-1504148455328-c376907d081c?q=80&w=600&auto=format&fit=crop",
        "puntos": [
            "⚠️ **Punto 1 (Mandril):** ¿El broquero ajusta de forma simétrica y se retiró la llave de apriete?",
            "⚠️ **Punto 2 (Tope):** ¿La varilla de tope de profundidad está fija para evitar atrapamientos directos?",
            "⚠️ **Punto 3 (Sentido):** ¿El inversor de marcha cambia con firmeza para evitar contragolpes?"
        ]
    }
}