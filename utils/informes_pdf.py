from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io
import pandas as pd

def generar_informe_pdf_miembros(miembros_completo):
    # Crear un buffer para el PDF
    buffer = io.BytesIO()
    # Configurar la página en orientación horizontal (landscape) con márgenes pequeños
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),  # Página horizontal
        rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20  # Márgenes pequeños
    )

    # Estilos
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    subtitle_style = styles["Heading2"]
    normal_style = styles["BodyText"]

    # Contenido del PDF
    elements = []

    # Título
    elements.append(Paragraph("Informe de Miembros", title_style))
    elements.append(Spacer(1, 12))

    # Tabla de datos
    data = [["ID", "Razón Social", "Representante", "RIF", "Mensualidad", "Saldo", "Estado"]] + [
        [
            row["ID_MIEMBRO"],
            row["RAZON_SOCIAL"],
            row["REPRESENTANTE"],
            row["RIF"],
            row["ULTIMO_MES"],
            f"$ {row['SALDO']:.2f}",
            row["ESTADO"]
        ]
        for _, row in miembros_completo.iterrows()
    ]

    table = Table(data, colWidths=[50, 150, 150, 100, 100, 100, 100])  # Ajustar el ancho de las columnas
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),  # Fondo verde oscuro para encabezados
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),  # Texto blanco en encabezados
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),  # Centrar texto
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),  # Fuente en negrita para encabezados
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),  # Espaciado inferior en encabezados
        ("GRID", (0, 0), (-1, -1), 1, colors.black),  # Bordes negros
    ]))
    elements.append(table)

    # Construir el PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def model_member_add_csv():
    output = io.StringIO()
    df_modelo = pd.DataFrame({
        "ID_MIEMBRO": pd.Series(dtype='int'),
        "RAZON_SOCIAL": pd.Series(dtype='str'),
        "RIF": pd.Series(dtype='str'),
        "ULTIMO_MES": pd.Series(dtype='str'),
        "SALDO": pd.Series(dtype='float'),
        "NUM_TELEFONO": pd.Series(dtype='str'),
        "REPRESENTANTE": pd.Series(dtype='str'),
        "CI_REPRESENTANTE": pd.Series(dtype='str'),
        "CORREO": pd.Series(dtype='str'),
        "DIRECCION": pd.Series(dtype='str'),
        "HACIENDA": pd.Series(dtype='str')
    })
    df_modelo.to_csv(output, index=False)
    return output.getvalue()