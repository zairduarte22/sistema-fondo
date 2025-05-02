import streamlit as st
from jinja2 import Template
import datetime

# Configuración exacta para tu talonario (15.72cm x 12.61cm)
TALONARIO = {
    "width": 157.2,
    "height": 126.1,
    "margins": {
        "top": 5,
        "left": 5
    }
}

# POSICIONES AJUSTABLES (valores iniciales basados en tu imagen)
POSICIONES = {
    "fecha": {"top": 10, "left": 10},
    "nombre": {"top": 22, "left": 10},
    "direccion": {"top": 30, "left": 10},
    "cedula": {"top": 38, "left": 10},
    "detalle1_concepto": {"top": 50, "left": 10},
    "detalle1_monto": {"top": 50, "left": 120},
    "detalle2_concepto": {"top": 60, "left": 10},
    "detalle2_monto": {"top": 60, "left": 120},
    "total": {"top": 100, "left": 120}
}

# Herramienta de calibración
with st.sidebar.expander("🔧 CALIBRACIÓN", expanded=True):
    st.caption("Ajusta mm por mm para alinear perfectamente")
    
    # Ajustes generales
    ajuste_x = st.slider("Ajuste Horizontal (mm)", -15, 15, 0)
    ajuste_y = st.slider("Ajuste Vertical (mm)", -15, 15, 0)
    
    # Ajustes individuales
    for campo in POSICIONES:
        POSICIONES[campo]["top"] += ajuste_y
        POSICIONES[campo]["left"] += ajuste_x

# Plantilla HTML/CSS optimizada
template = Template(f'''
<!DOCTYPE html>
<html>
<head>
<style>
@page {{
    size: {TALONARIO['width']}mm {TALONARIO['height']}mm;
    margin: 0;
}}

body {{
    width: {TALONARIO['width']}mm;
    height: {TALONARIO['height']}mm;
    margin: 0;
    padding: 0;
    font-family: "Courier New", monospace;
    font-size: 10pt;
    position: relative;
}}

/* ESTILOS BASE */
.campo {{
    position: absolute;
    white-space: nowrap;
}}

/* POSICIONES ESPECÍFICAS */
.fecha {{
    top: {POSICIONES['fecha']['top']}mm;
    left: {POSICIONES['fecha']['left']}mm;
    letter-spacing: 2px;
}}

.nombre {{
    top: {POSICIONES['nombre']['top']}mm;
    left: {POSICIONES['nombre']['left']}mm;
    font-weight: bold;
}}

.direccion {{
    top: {POSICIONES['direccion']['top']}mm;
    left: {POSICIONES['direccion']['left']}mm;
}}

.cedula {{
    top: {POSICIONES['cedula']['top']}mm;
    left: {POSICIONES['cedula']['left']}mm;
}}

.detalle1-concepto {{
    top: {POSICIONES['detalle1_concepto']['top']}mm;
    left: {POSICIONES['detalle1_concepto']['left']}mm;
    width: 100mm;
}}

.detalle1-monto {{
    top: {POSICIONES['detalle1_monto']['top']}mm;
    left: {POSICIONES['detalle1_monto']['left']}mm;
    text-align: right;
    width: 30mm;
}}

/* Repetir para detalle2... */

.total {{
    top: {POSICIONES['total']['top']}mm;
    left: {POSICIONES['total']['left']}mm;
    text-align: right;
    font-weight: bold;
    width: 30mm;
}}
</style>
</head>
<body>

<!-- ESTRUCTURA EXACTA -->
<div class="campo fecha">{{ fecha }}</div>
<div class="campo nombre">{{ nombre_cliente }}</div>
<div class="campo direccion">{{ direccion }}</div>
<div class="campo cedula">{{ cedula }}</div>

<div class="campo detalle1-concepto">{{ detalle1_concepto }}</div>
<div class="campo detalle1-monto">{{ detalle1_monto }}</div>

<div class="campo detalle2-concepto">{{ detalle2_concepto }}</div>
<div class="campo detalle2-monto">{{ detalle2_monto }}</div>

<div class="campo total">{{ total }}</div>

</body>
</html>
''')

# Datos de ejemplo (reemplaza con tus datos reales)
factura = {
    "fecha": "31    12    2023",
    "nombre_cliente": "MARIO ALFREDO SAAB",
    "direccion": "URB EL VALLE",
    "cedula": "V-127582390",
    "detalle1_concepto": "CANCELACIÓN DEL 60% POR CUOTA CORRESPONDIENTE A ENERO 2024",
    "detalle1_monto": "432.00",
    "detalle2_concepto": "CANCELACIÓN DEL 20% POR CUOTA CORRESPONDIENTE A ENERO 2024",
    "detalle2_monto": "144.00",
    "total": "576.00"
}

# Visualización en Streamlit
st.components.v1.html(template.render(**factura), height=400)

# Botón de impresión mejorado
if st.button("🖨 IMPRIMIR FACTURA"):
    js = """
    <script>
    setTimeout(() => {
        window.print();
    }, 200);
    </script>
    """
    st.components.v1.html(js)

# Guía de ayuda
with st.expander("ℹ️ INSTRUCCIONES DE USO"):
    st.markdown("""
    1. **Primera prueba**: Imprime en papel normal y compara con tu talonario físico
    2. **Ajusta los controles deslizantes** hasta que coincidan perfectamente
    3. **Configuración de impresión**:
       - Tamaño de papel: Personalizado (157.2mm × 126.1mm)
       - Márgenes: Ninguno
       - Escala: 100%
    4. **Coloca el talonario** en la bandeja de alimentación manual
    5. **Imprime** y verifica la alineación
    """)