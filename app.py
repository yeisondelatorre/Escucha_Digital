import streamlit as st
import pandas as pd
import plotly.express as px
import json
import io
from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Escucha Digital Avanzada - Alcaldía de Santa Marta",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-header { font-size:26px; font-weight:bold; color:#1B365D; }
    .sub-header { font-size:16px; color:#555555; }
    .card-box { background-color:#F4F6F9; padding:15px; border-radius:10px; border-left:5px solid #1B365D; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📊 Sistema Avanzado de Escucha Digital Política</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Scraping, Procesamiento Masivo, Descarga en Excel y Analítica de Sentimiento | Santa Marta</p>', unsafe_allow_html=True)
st.divider()

# -----------------------------------------------------------------------------
# BARRA LATERAL: CONFIGURACIÓN Y API KEY
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuración del Sistema")
    api_key = st.text_input("Gemini API Key:", type="password", help="Ingresa tu clave de API de Google AI Studio")
    
    st.markdown("---")
    st.subheader("📌 Parámetros Territorial")
    plataforma = st.selectbox("Canal Principal:", ["Multiplataforma (Excel/Batch)", "Facebook", "X (Twitter)", "Instagram", "WhatsApp / Dark Social"])
    territorio = st.selectbox("Zona de Cobertura:", ["Todo el Distrito", "Localidad 1 (Cultural-Tylona)", "Localidad 2 (Histórica-Rodrigo de Bastidas)", "Localidad 3 (Turística-Perla del Caribe)", "Zona Rural / Corregimientos"])

# -----------------------------------------------------------------------------
# MÓDULO DE CARGA Y SCRAPING DE DATOS
# -----------------------------------------------------------------------------
st.subheader("📥 1. Ingesta de Datos (Individual o Carga Masiva)")

tab1, tab2 = st.tabs(["📁 Cargar Archivo (Excel / CSV / TXT)", "✍️ Entrada Manual Directa"])

df_comentarios = None

with tab1:
    uploaded_file = st.file_uploader(
        "Sube un archivo Excel (.xlsx), CSV (.csv) o Texto (.txt) con URLs o comentarios:", 
        type=["xlsx", "csv", "txt"]
    )
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df_input = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.csv'):
                df_input = pd.read_csv(uploaded_file)
            else:
                string_data = uploaded_file.read().decode("utf-8")
                lines = [line.strip() for line in string_data.split("\n") if line.strip()]
                df_input = pd.DataFrame({"Comentarios_o_URL": lines})
            
            st.success(f"📂 Archivo cargado exitosamente. Se detectaron {len(df_input)} registros.")
            st.dataframe(df_input.head(5), use_container_width=True)
            
            # Unificar texto para el análisis
            col_target = st.selectbox("Selecciona la columna que contiene los comentarios o URLs:", df_input.columns)
            texto_consolidado = " ".join(df_input[col_target].astype(str).tolist())
            df_comentarios = df_input
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

with tab2:
    texto_manual = st.text_area(
        "Pega aquí directamente las URLs, lista de comentarios o cadenas de WhatsApp:",
        height=150,
        placeholder="Ejemplo:\n- En Mamatoco llevamos 3 días sin agua @AlcaldiaSM\n- La extorsión en el Mercado Público está insostenible..."
    )
    if texto_manual.strip():
        lines = [l.strip() for l in texto_manual.split("\n") if l.strip()]
        df_comentarios = pd.DataFrame({"Comentario": lines})
        texto_consolidado = texto_manual

btn_procesar = st.button("🚀 Ejecutar Scraping, Procesar y Analizar Escucha Digital", type="primary", use_container_width=True)

# -----------------------------------------------------------------------------
# FUNCIÓN MOTOR NLP (GEMINI 1.5 FLASH)
# -----------------------------------------------------------------------------
def procesar_escucha_digital(texto, key):
    # Iniciar cliente oficial con el modelo gemini-1.5-flash
    client = genai.Client(api_key=key)
    
    prompt = f"""
    Actúas como un experto en Ciencia de Datos Política y Social Listening especializado en el contexto socio-político de Santa Marta, Magdalena, Colombia.
    Analiza el siguiente conjunto masivo de texto, publicaciones y comentarios en {plataforma} enfocados en {territorio}.
    
    Debes considerar el contexto local samario (falta de agua, ESSMAR, basuras Atesa, extorsión, movilidad, obras, gestión del Alcalde Carlos Pinedo) y detectar ironía/sarcasmo costeño.
    
    DEBES RETORNAR ÚNICAMENTE UN JSON VÁLIDO CON ESTA ESTRUCTURA EXACTA (SIN NINGÚN BLOQUE MARKDOWN):
    {{
        "favorabilidad_neta": 0,
        "distribucion_sentimiento": {{
            "Positivo": 0,
            "Negativo": 0,
            "Neutro": 0
        }},
        "focos_criticos": [
            {{"categoria": "Servicios Públicos (Agua/Basuras)", "menciones_pct": 0}},
            {{"categoria": "Seguridad y Extorsión", "menciones_pct": 0}},
            {{"categoria": "Malla Vial y Movilidad", "menciones_pct": 0}},
            {{"categoria": "Turismo e Informalidad", "menciones_pct": 0}},
            {{"categoria": "Gestión Institucional", "menciones_pct": 0}}
        ],
        "nivel_de_alerta_crisis": 1,
        "resumen_ejecutivo": "Síntesis clara de la opinión de la ciudadanía.",
        "recomendacion_estrategica": "Plan de acción comunicacional u operativo recomendado."
    }}
    
    TEXTO A EVALUAR:
    "{texto[:15000]}"
    """
    
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    return json.loads(response.text)

# -----------------------------------------------------------------------------
# RESULTADOS Y DESCARGA DE EXCEL
# -----------------------------------------------------------------------------
if btn_procesar:
    if not api_key:
        st.error("⚠️ Por favor ingresa tu Gemini API Key en la barra lateral.")
    elif df_comentarios is None or df_comentarios.empty:
        st.warning("⚠️ Debes subir un archivo o ingresar texto para analizar.")
    else:
        with st.spinner("⏳ Procesando datos, aplicando modelos NLP y estructurando informe..."):
            try:
                res = procesar_escucha_digital(texto_consolidado, api_key)
                
                st.success("✅ Procesamiento finalizado con éxito.")
                st.divider()
                
                # --- DESCARGA DE DATOS EN EXCEL ---
                st.subheader("💾 2. Almacenamiento y Descarga de Datos")
                
                # Generar archivo Excel en memoria para descarga
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_comentarios.to_excel(writer, sheet_name='Comentarios_Scrapeados', index=False)
                    
                    # Guardar resumen analítico en segunda hoja
                    df_resumen = pd.DataFrame([{
                        "Favorabilidad_Neta": f"{res.get('favorabilidad_neta')}%",
                        "Nivel_Alerta": res.get("nivel_de_alerta_crisis"),
                        "Resumen": res.get("resumen_ejecutivo"),
                        "Recomendacion": res.get("recomendacion_estrategica")
                    }])
                    df_resumen.to_excel(writer, sheet_name='Resumen_Escucha', index=False)
                
                buffer.seek(0)
                
                st.download_button(
                    label="📥 Descargar Base de Datos de Comentarios y Resultados en Excel",
                    data=buffer,
                    file_name="Escucha_Digital_Santa_Marta_Resultados.xlsx",
                    mime="application/vnd.ms-excel",
                    type="secondary"
                )
                
                st.divider()
                
                # --- MÉTRICAS GENERALES ---
                st.subheader("📈 3. Tablero de Indicadores Políticos")
                c1, c2, c3, c4 = st.columns(4)
                
                fav = res.get("favorabilidad_neta", 0)
                sent = res.get("distribucion_sentimiento", {})
                alerta = res.get("nivel_de_alerta_crisis", 1)
                
                with c1:
                    st.metric("Favorabilidad Neta", f"{fav}%")
                with c2:
                    st.metric("Sentimiento Negativo", f"{sent.get('Negativo', 0)}%")
                with c3:
                    st.metric("Sentimiento Positivo", f"{sent.get('Positivo', 0)}%")
                with c4:
                    label_crisis = "🔴 Severa (4-5)" if alerta >= 4 else "🟡 Moderada (3)" if alerta == 3 else "🟢 Normal (1-2)"
                    st.metric("Nivel de Alerta de Crisis", label_crisis)
                
                # --- GRÁFICOS ---
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    st.markdown("#### Balance de Sentimiento")
                    df_sent = pd.DataFrame({"Sentimiento": list(sent.keys()), "Porcentaje": list(sent.values())})
                    fig1 = px.pie(
                        df_sent, values="Porcentaje", names="Sentimiento",
                        color="Sentimiento",
                        color_discrete_map={"Positivo": "#5CB85C", "Negativo": "#D9534F", "Neutro": "#A6ACAF"},
                        hole=0.4
                    )
                    st.plotly_chart(fig1, use_container_width=True)
                    
                with col_g2:
                    st.markdown("#### Focos Críticos Detectados")
                    focos = res.get("focos_criticos", [])
                    if focos:
                        df_focos = pd.DataFrame(focos)
                        fig2 = px.bar(
                            df_focos, x="menciones_pct", y="categoria", orientation="h",
                            labels={"menciones_pct": "% Menciones", "categoria": "Problemática"},
                            color_discrete_sequence=["#1B365D"]
                        )
                        fig2.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig2, use_container_width=True)
                
                # --- DIAGNÓSTICO Y RECOMENDACIONES ---
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.info(f"**📋 Resumen Ejecutivo:**\n\n{res.get('resumen_ejecutivo')}")
                with col_d2:
                    st.warning(f"**💡 Recomendación Estratégica:**\n\n{res.get('recomendacion_estrategica')}")
                    
            except Exception as e:
                st.error(f"❌ Error durante el procesamiento: {str(e)}")
                
                
                
