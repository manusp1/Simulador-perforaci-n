import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configuración de página
st.set_page_config(page_title="Advanced AI Geosteering - Colombia VMM", layout="wide")

st.title("🚀 Simulador Pro: Perforación Direccional e IA")
st.markdown("### Contexto: Cuenca Valle Medio del Magdalena (Colombia)")

# --- LÓGICA DE GEOLOGÍA ---
# [Nombre, Profundidad Tope (TVD), Color, Trama, Tipo Roca]
FORMACIONES = [
    ["Fm. Real", 0, "#8B4513", "///", "Lutita"],
    ["Fm. Colorado", 2000, "#F4D03F", "..", "Areniscas"],
    ["Fm. Mugrosa", 4500, "#58D68D", "--", "Lutita/Arena"],
    ["Target: Fm. Esmeraldas", 7000, "#D35400", "oo", "Arenisca Porosa"]
]
BUZAMIENTO = 3.0 

# --- INICIALIZACIÓN ---
if 'md' not in st.session_state:
    st.session_state.md = [6500]           # Empezamos más arriba para ver la caída
    st.session_state.tvd = [6600]          
    st.session_state.inc = [45.0]          # Empezamos con inclinación de construcción
    st.session_state.vs = [0]              
    st.session_state.dls = [0]             
    # Generar un obstáculo aleatorio adelante
    st.session_state.obs_x = 800           # Vertical Section donde está el obstáculo
    st.session_state.obs_y = 7050          # Profundidad del obstáculo
    st.session_state.finalizado = False

def calcular_dls(inc1, inc2, dist):
    return abs(inc2 - inc1) * (100 / dist)

# --- SIDEBAR ---
st.sidebar.header("⚙️ Parámetros de Perforación")
inc_objetivo = st.sidebar.slider("Ajustar Inclinación (Survey @100ft)", 0.0, 110.0, float(st.session_state.inc[-1]), 1.0)

if st.sidebar.button("🛠️ Perforar Survey (100 ft)") and not st.session_state.finalizado:
    dist = 100
    nueva_inc = inc_objetivo
    inc_promedio = (st.session_state.inc[-1] + nueva_inc) / 2
    
    nuevo_md = st.session_state.md[-1] + dist
    # En perforación, TVD baja (aumenta número) según el coseno del ángulo con la vertical
    # Para simplificar: delta_tvd = cos(inc) * dist
    nuevo_tvd = st.session_state.tvd[-1] + (dist * np.cos(np.radians(inc_promedio)))
    nuevo_vs = st.session_state.vs[-1] + (dist * np.sin(np.radians(inc_promedio)))
    
    dls_actual = calcular_dls(st.session_state.inc[-1], nueva_inc, dist)
    
    # Check Colisión con Obstáculo
    dist_al_obs = np.sqrt((nuevo_vs - st.session_state.obs_x)**2 + (nuevo_tvd - st.session_state.obs_y)**2)
    if dist_al_obs < 40:
        st.session_state.finalizado = True
        st.error("💥 ¡COLISIÓN! Has chocado con un pozo abandonado u obstáculo geológico.")
    
    st.session_state.md.append(nuevo_md)
    st.session_state.tvd.append(nuevo_tvd)
    st.session_state.inc.append(nueva_inc)
    st.session_state.vs.append(nuevo_vs)
    st.session_state.dls.append(dls_actual)

if st.sidebar.button("🚨 Realizar Sidetrack"):
    # El sidetrack "borra" el último tramo y cambia la trayectoria
    if len(st.session_state.md) > 1:
        st.session_state.md.pop()
        st.session_state.tvd.pop()
        st.session_state.vs.pop()
        st.session_state.inc.pop()
        st.warning("Sidetrack iniciado: Regresando al punto de desvío anterior.")
        st.session_state.finalizado = False

if st.sidebar.button("🔄 Reiniciar Todo"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- ALERTAS DE IA ---
st.subheader("🤖 Diagnóstico de IA en Tiempo Real")
col_a, col_b, col_c = st.columns(3)
with col_a:
    if st.session_state.dls[-1] > 4.5:
        st.error(f"DLS Crítico: {st.session_state.dls[-1]:.2f}. Peligro de Ojo de Llave.")
    else: st.success("DLS dentro de límites.")
with col_b:
    dist_obs = st.session_state.obs_x - st.session_state.vs[-1]
    if 0 < dist_obs < 300:
        st.warning(f"Obstáculo detectado a {dist_obs:.0f} ft adelante. ¡Evalúe Sidetrack!")
with col_c:
    st.metric("Inclinación Actual", f"{st.session_state.inc[-1]}°")

# --- GRÁFICA CORREGIDA ---
fig, ax = plt.subplots(figsize=(12, 7))

# Rango de visualización amplio
dist_max = 2000
x_plot = np.linspace(0, dist_max, 100)

for i in range(len(FORMACIONES)):
    nombre, tope, color, trama, roca = FORMACIONES[i]
    y_tope = tope + (x_plot * np.tan(np.radians(BUZAMIENTO)))
    y_base = 10000 if i == len(FORMACIONES)-1 else FORMACIONES[i+1][1] + (x_plot * np.tan(np.radians(BUZAMIENTO)))
    ax.fill_between(x_plot, y_tope, y_base, color=color, alpha=0.4, hatch=trama, label=f"{nombre}")

# Dibujar Obstáculo (Pozo abandonado)
circulo = plt.Circle((st.session_state.obs_x, st.session_state.obs_y), 30, color='red', label='Obstáculo (Colisión)')
ax.add_patch(circulo)

# Dibujar Trayectoria
ax.plot(st.session_state.vs, st.session_state.tvd, color='black', linewidth=4, marker='o', markersize=4, label="Pozo Activo")

# AJUSTE DE EJES PARA VER TODO EL PANORAMA
ax.set_ylim(8500, 4000) # Ver desde 4000 ft hasta 8500 ft (Ajusta esto según prefieras)
ax.set_xlim(0, dist_max)
ax.invert_yaxis() # Profundidad hacia abajo
ax.set_xlabel("Desplazamiento Horizontal (Vertical Section) [ft]")
ax.set_ylabel("Profundidad Vertical (TVD) [ft]")
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1))
ax.grid(True, which='both', linestyle='--', alpha=0.5)

st.pyplot(fig)

# Tabla de Survey
st.subheader("📋 Datos del Pozo")
st.write(f"**MD:** {st.session_state.md[-1]} ft | **TVD:** {st.session_state.tvd[-1]:.2f} ft | **DLS:** {st.session_state.dls[-1]:.2f} °/100ft")
