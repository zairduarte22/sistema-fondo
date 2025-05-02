# app.py - Interfaz Streamlit
import streamlit as st
from datetime import datetime
from .invoice_model import FacturaGenerator
import base64

# Configuración de la página
st.set_page_config(
    page_title="Generador de Facturas Físicas",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Clase para manejar el estado de la UI
class FacturaUI:
    @staticmethod
    def show_header():
        st.title("🧾 Generador de Facturas")
        st.markdown("""
        **Precisión milimétrica para talonarios físicos**  
        Tamaño configurado: {}mm × {}mm
        """.format(FacturaGenerator.TALONARIO_WIDTH, FacturaGenerator.TALONARIO_HEIGHT))

    @staticmethod
    def input_form():
        with st.form("factura_form"):
            cols = st.columns(2)
            with cols[0]:
                fecha = st.date_input("Fecha", datetime.now())
                nombre = st.text_input("Nombre del Cliente")
            with cols[1]:
                cedula = st.text_input("Cédula/RUC")
                direccion = st.text_input("Dirección")
            
            st.subheader("Detalles de Factura")
            detalles = []
            for i in range(2):  # Dos líneas de detalle
                cols = st.columns([3, 1])
                detalles.append({
                    "concepto": cols[0].text_input(f"Concepto {i+1}", key=f"concepto_{i}"),
                    "monto": cols[1].text_input(f"Monto {i+1}", key=f"monto_{i}")
                })
            
            total = st.text_input("Total")
            
            submit = st.form_submit_button("Generar Factura")
            
            if submit:
                return {
                    "fecha": fecha.strftime("%d/%m/%Y"),
                    "nombre": nombre,
                    "direccion": direccion,
                    "cedula": cedula,
                    "detalles": [d for d in detalles if d["concepto"]],
                    "total": total
                }
        return None

    @staticmethod
    def preview_section(pdf_bytes):
        st.subheader("Vista Previa")
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500px" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        st.download_button(
            label="Descargar PDF",
            data=pdf_bytes,
            file_name="factura.pdf",
            mime="application/pdf"
        )

    @staticmethod
    def print_section(pdf_bytes):
        st.subheader("Impresión Directa")
        if st.button("🖨 Enviar a Impresora"):
            js = f"""
            <script>
            function printPDF() {{
                const blob = new Blob([{list(pdf_bytes)}], {{type: 'application/pdf'}});
                const url = URL.createObjectURL(blob);
                const iframe = document.createElement('iframe');
                iframe.style.display = 'none';
                iframe.src = url;
                document.body.appendChild(iframe);
                iframe.onload = () => {{
                    setTimeout(() => {{
                        iframe.contentWindow.print();
                        URL.revokeObjectURL(url);
                    }}, 1000);
                }};
            }}
            printPDF();
            </script>
            """
            st.components.v1.html(js, height=0, width=0)
            st.success("Enviando a impresora... Verifica la primera copia")

# Flujo principal
def main():
    FacturaUI.show_header()
    
    data = FacturaUI.input_form()
    
    if data:
        pdf_bytes = FacturaGenerator.generar_pdf(data)
        FacturaUI.preview_section(pdf_bytes)
        FacturaUI.print_section(pdf_bytes)