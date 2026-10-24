import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Escucha Digital - Alcaldía de Santa Marta",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo visual personalizado
st.markdown("""
    <style>
    .main-header { font-size:26px; font-weight:bold; color:#1B365D; }
    .sub-header { font-size:16px; color:#555555; }
    .card-metric { background-color:#F4F6F9; padding:15px; border-radius:10px; border-left:5px solid #1B365D; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📊 Sistema de Escucha Digital Política</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Monitoreo de Favorabilidad, Gestión y Focos Críticos | Distrito de Santa Marta</p>', unsafe_allow_html=True)
st.divider()

# -----------------------------------------------------------------------------
# BARRA LATERAL: CONFIGURACIÓN
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # API Key de Gemini
    api_key = st.text_input("Gemini API Key:", type="password", help="Ingresa tu clave de API de Google AI Studio")
    
    st.markdown("---")
    st.subheader("📌 Parámetros de Análisis")
    plataforma = st.selectbox("Plataforma de Origen:", ["Facebook", "X (Twitter)", "Instagram", "Portal de Noticias", "WhatsApp (Dark Social)"])
    territorio = st.selectbox("Colectivo / Zona Prioritaria:", ["Todo el Distrito", "Localidad 1 (Cultural-Tylona)", "Localidad 2 (Histórica-Rodrigo de Bastidas)", "Localidad 3 (Turística-Perla del Caribe)", "Zona Rural / Corregimientos"])

# -----------------------------------------------------------------------------
# SECCIÓN PRINCIPAL DE ENTRADA DE DATOS
# -----------------------------------------------------------------------------
col_input1, col_input2 = st.tabs(["🔗 Análisis por URL / Enlace", "📝 Análisis de Texto Directo (Dark Social)"])

with col_input1:
    url_input = st.text_input("Ingresa la URL de la publicación o noticia:", placeholder="https://www.facebook.com/...")
    text_from_url = st.text_area("Comentarios o cuerpo extraído de la URL (si no usas scraper automático):", height=150, placeholder="Pega aquí los comentarios o el texto capturado de la publicación...")

with col_input2:
    text_direct_input = st.text_area("Pega aquí el texto, reporte o conversación de WhatsApp/Telegram:", height=200, placeholder="Ejemplo: Cadena reportando falta de agua en Mamatoco o quejas de alumbrado público...")

# Consolidar entrada
contenido_a_analizar = text_from_url if text_from_url else text_direct_input

btn_analizar = st.button("🚀 Procesar y Analizar Escucha Digital", type="primary", use_container_width=True)

# -----------------------------------------------------------------------------
# FUNCIÓN DE ANÁLISIS CON GEMINI API
# -----------------------------------------------------------------------------
def analizar_escucha_digital(texto, key_api, canal, zona):
    client = genai.Client(api_key=key_api)
    
    prompt_sistema = f"""
    Actúas como un experto en Ciencia de Datos Política y Social Listening especializado en el contexto de Santa Marta, Magdalena, Colombia.
    Analiza el siguiente conjunto de texto/comentarios provenientes de {canal} enfocado en la zona {zona}.
    
    Debes tener en cuenta el lenguaje local samario/costeño, la ironía (ejemplo: "excelente servicio" cuando se van la luz o el agua) y las problemáticas principales del distrito:
    1. Servicios Públicos (ESSMAR, Agua potable, Basuras/Atesa, Alcantarillado, Energía/Air-e).
    2. Seguridad (Extorsión, robos, sicariato, orden público).
    3. Movilidad e Infraestructura (Malla vial/huecos, mototaxismo, obras públicas).
    4. Turismo y Economía (Rodadero, vendedores informales, precios).
    5. Gestión Institucional (Alcalde Carlos Pinedo, gobernanza, contratación).
    
    DEBES DEVOLVER UNICAMENTE UN OBJETO JSON VALIDO CON LA SIGUIENTE ESTRUCTURA (SIN MARKDOWN DE CODIGO ```json):
    {{
        "favorabilidad_neta": 0,  // Porcentaje entre -100 (muy negativo) y +100 (muy positivo)
        "distribucion_sentimiento": {{
            "Positivo": 0,  // Porcentaje (0 a 100)
            "Negativo": 0,  // Porcentaje (0 a 100)
            "Neutro": 0     // Porcentaje (0 a 100)
        }},
        "focos_criticos": [
            {{"categoria": "Nombre Categoria", "menciones_pct": 0}}
        ],
        "nivel_de_alerta_crisis": 1, // Escala de 1 (Bajo/Normal) a 5 (Crisis Crítica/Protestas)
        "resumen_ejecutivo": "Texto conciso explicando la posición dominante del público y el motivo de la insatisfacción o apoyo.",
        "recomendacion_estrategica": "Sugerencia concreta de respuesta comunicacional u operativa para la Alcaldía."
    }}
    
    TEXTO A ANALIZAR:
    "{texto}"
    """
    
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt_sistema,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    return json.loads(response.text)

# -----------------------------------------------------------------------------
# EJECUCIÓN Y DESPLEGABLE DE RESULTADOS
# -----------------------------------------------------------------------------
if btn_analizar:
    if not api_key:
        st.error("⚠️ Por favor ingresa tu API Key de Gemini en la barra lateral para continuar.")
    elif not contenido_a_analizar.strip():
        st.warning("⚠️ Por favor ingresa el texto de los comentarios o la captura para realizar el análisis.")
    else:
        with st.spinner("⏳ Procesando lenguaje natural, detectando sarcasmo costeño y calculando métricas..."):
            try:
                resultado = analizar_escucha_digital(contenido_a_analizar, api_key, plataforma, territorio)
                
                st.success("✅ Análisis finalizado exitosamente")
                st.divider()
                
                # --- FILA 1: MÉTRICAS CLAVE ---
                c1, c2, c3, c4 = st.columns(4)
                
                fav = resultado.get("favorabilidad_neta", 0)
                sent = resultado.get("distribucion_sentimiento", {})
                alerta = resultado.get("nivel_de_alerta_crisis", 1)
                
                with c1:
                    st.metric("Índice de Favorabilidad Neta", f"{fav}%", delta=f"{fav}%", delta_color="normal")
                with c2:
                    st.metric("Sentimiento Negativo", f"{sent.get('Negativo', 0)}%")
                with c3:
                    st.metric("Sentimiento Positivo", f"{sent.get('Positivo', 0)}%")
                with c4:
                    color_alerta = "🔴 High" if alerta >= 4 else ("🟡 Medium" if alerta >= 3 else "🟢 Low")
                    st.metric("Nivel de Alerta de Crisis", f"{alerta} / 5", delta=color_alerta, delta_color="inverse")
                
                st.divider()
                
                # --- FILA 2: GRÁFICOS INTERACTIVOS ---
                col_graf1, col_graf2 = st.columns(2)
                
                with col_graf1:
                    st.subheader("📊 Distribución de Sentimiento")
                    df_sent = pd.DataFrame({
                        "Sentimiento": list(sent.keys()),
                        "Porcentaje": list(sent.values())
                    })
                    fig_pie = px.pie(
                        df_sent, values="Porcentaje", names="Sentimiento",
                        color="Sentimiento",
                        color_discrete_map={"Positivo": "#5CB85C", "Negativo": "#D9534F", "Neutro": "#A6ACAF"},
                        hole=0.4
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col_graf2:
                    st.subheader("🔥 Focos Críticos / Problemáticas Detectadas")
                    focos = resultado.get("focos_criticos", [])
                    if focos:
                        df_focos = pd.DataFrame(focos)
                        fig_bar = px.bar(
                            df_focos, x="menciones_pct", y="categoria", orientation="h",
                            labels={"menciones_pct": "% Menciones", "categoria": "Problemática"},
                            color_discrete_sequence=["#1B365D"]
                        )
                        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_bar, use_container_width=True)
                
                st.divider()
                
                # --- FILA 3: DIAGNÓSTICO Y RECOMENDACIÓN ESTRATÉGICA ---
                col_diag1, col_diag2 = st.columns(2)
                
                with col_diag1:
                    st.subheader("📋 Resumen Ejecutivo de la Escucha")
                    st.info(resultado.get("resumen_ejecutivo", "Sin resumen disponible."))
                    
                with col_diag2:
                    st.subheader("💡 Recomendación Estratégica")
                    st.warning(resultado.get("recomendacion_estrategica", "Sin recomendación disponible."))
                    
            except Exception as e:
                st.error(f"❌ Ocurrió un error al procesar la solicitud: {str(e)}")
                
                
                
