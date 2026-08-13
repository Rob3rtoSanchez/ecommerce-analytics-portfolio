import streamlit as st
import pandas as pd
import joblib
import plotly.express as px

st.set_page_config(page_title="Olist E-Commerce Analytics", layout="wide")

# --- Carga de datos pre-procesados ---
@st.cache_data
def cargar_datos():
    ventas_mensuales = pd.read_csv('reports/ventas_mensuales.csv')
    analisis_regional = pd.read_csv('reports/analisis_regional.csv')
    entrega_satisfaccion = pd.read_csv('reports/entrega_vs_satisfaccion.csv')
    return ventas_mensuales, analisis_regional, entrega_satisfaccion

@st.cache_resource
def cargar_modelo():
    modelo = joblib.load('models/modelo_riesgo_insatisfaccion.pkl')
    columnas = joblib.load('models/columnas_modelo.pkl')
    return modelo, columnas

ventas_mensuales, analisis_regional, entrega_satisfaccion = cargar_datos()
modelo, columnas_modelo = cargar_modelo()

st.title("📊 Análisis E-Commerce Brasileño (Olist)")
st.markdown("Proyecto de ciencia de datos — 99,441 pedidos analizados (2016-2018)")

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Estacionalidad", "🚚 Entrega vs Satisfacción", "🗺️ Análisis Regional", "🎯 Demo: Modelo de Riesgo"
])

# --- TAB 1: Estacionalidad ---
with tab1:
    st.header("¿Hay estacionalidad que Olist debería anticipar?")
    fig = px.line(ventas_mensuales, x='year_month', y='num_pedidos',
                  title='Pedidos por mes', markers=True)
    st.plotly_chart(fig, use_container_width=True)
    st.info("**Hallazgo**: el pico más alto (nov 2017) coincide con Black Friday — "
            "el 24 de noviembre concentró 1,147 pedidos, 5.7x el promedio diario del mes.")

# --- TAB 2: Entrega vs Satisfacción ---
with tab2:
    st.header("¿El tiempo de entrega predice insatisfacción?")
    fig2 = px.bar(entrega_satisfaccion, x='review_score', y='dias_entrega',
                  title='Días promedio de entrega según calificación',
                  labels={'dias_entrega': 'Días promedio', 'review_score': 'Calificación'})
    st.plotly_chart(fig2, use_container_width=True)
    st.info("**Hallazgo**: correlación negativa moderada (Pearson r = -0.341, p < 0.001). "
            "Pedidos con 1 estrella tardaron en promedio 20.7 días vs 10.2 días para 5 estrellas.")

# --- TAB 3: Análisis Regional ---
with tab3:
    st.header("¿Qué regiones están sub-atendidas?")
    fig3 = px.bar(analisis_regional.sort_values('pedidos_por_100k_hab', ascending=True),
                  x='pedidos_por_100k_hab', y='customer_state', orientation='h',
                  title='Pedidos por cada 100,000 habitantes, por estado')
    st.plotly_chart(fig3, use_container_width=True)
    st.info("**Hallazgo**: Norte/Nordeste muestra baja penetración, correlacionado con que "
            "59.7% de los vendedores están concentrados en São Paulo. "
            "Fuente de población: IBGE/SIDRA, tabla 6579.")

# --- TAB 4: Demo del modelo ---
with tab4:
    st.header("Simula el riesgo de insatisfacción de un pedido")
    st.caption("Modelo Random Forest, AUC-ROC = 0.620, evaluado en el checkpoint de envío al transportista")

    col1, col2 = st.columns(2)
    with col1:
        price = st.number_input("Precio del producto (R$)", min_value=0.0, value=100.0)
        freight_value = st.number_input("Costo de envío (R$)", min_value=0.0, value=20.0)
        dias_estimados = st.slider("Días estimados de entrega", 1, 60, 20)
        dias_hasta_envio = st.slider("Días hasta despacho al transportista", 0, 30, 3)
    with col2:
        installments = st.slider("Número de cuotas de pago", 1, 24, 1)
        mismo_estado = st.selectbox("¿Cliente y vendedor en el mismo estado?", ["No", "Sí"])

    if st.button("Calcular riesgo"):
        margen_al_envio = dias_estimados - dias_hasta_envio
        ratio_flete_precio = freight_value / price if price > 0 else 0

        entrada = pd.DataFrame([{
            'price': price, 'freight_value': freight_value,
            'payment_installments_max': installments, 'dias_estimados': dias_estimados,
            'mismo_estado': 1 if mismo_estado == "Sí" else 0,
            'ratio_flete_precio': ratio_flete_precio,
            'dias_hasta_envio': dias_hasta_envio, 'margen_al_envio': margen_al_envio
        }])

        entrada_encoded = pd.get_dummies(entrada)
        entrada_final = entrada_encoded.reindex(columns=columnas_modelo, fill_value=0)

        riesgo = modelo.predict_proba(entrada_final)[0, 1]

        st.metric("Probabilidad de insatisfacción", f"{riesgo:.1%}")
        if riesgo > 0.479:
            st.error("⚠️ Riesgo elevado — considerar seguimiento proactivo")
        else:
            st.success("✅ Riesgo bajo")

st.markdown("---")
st.caption("Autor: Roberto Sánchez | [LinkedIn](https://www.linkedin.com/in/roberto-sánchez-ai-ml-developer) | "
            "[GitHub](https://github.com/Rob3rtoSanchez/ecommerce-analytics-portfolio)")