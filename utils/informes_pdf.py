from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import io
import pandas as pd


def generar_informe_pdf_miembros(miembros_completo, grupo: str):
    miembros_completo.groupby(grupo)
    pdfmetrics.registerFont(TTFont("Lato Bold", "assets/fonts/Lato/Lato-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Lato Regular", "assets/fonts/Lato/Lato-Regular.ttf"))
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
    elements.append(Paragraph("Reporte de Miembros", title_style))
    elements.append(Spacer(1, 12))

    # Tabla de datos
    data = [["ID", "Razón Social", "Representante", "Estado"]] + [
        [
            row["ID_MIEMBRO"],
            row["RAZON_SOCIAL"],
            row["REPRESENTANTE"],
            row["ESTADO"]
        ]
        for _, row in miembros_completo.iterrows()
    ]

    table = Table(data, emptyTableAction='indicate')  # Ajustar el ancho de las columnas
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),  # Fondo verde oscuro para encabezados
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),  # Texto blanco en encabezados
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),  # Centrar texto
        ("FONTNAME", (0, 0), (-1, 0), "Lato Bold"),  # Fuente en negrita para encabezados
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),  # Espaciado inferior en encabezados
        ("GRID", (0, 0), (-1, -1), 1, colors.black), # Bordes negros
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

def generar_factura_pdf(factura, miembros_completo):
    """
    Genera un archivo PDF de la factura seleccionada.

    Args:
        factura (dict): Diccionario con los datos de la factura seleccionada.

    Returns:
        io.BytesIO: Archivo PDF generado en memoria.
    """
    pdf_output = io.BytesIO()
    doc = SimpleDocTemplate(pdf_output, pagesize=letter)

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        alignment=1,  # Centrado
        spaceAfter=20
    )
    normal_style = styles["Normal"]
    bold_style = ParagraphStyle(
        "Bold",
        parent=normal_style,
        fontName="Helvetica-Bold"
    )

    # Contenido de la factura
    elements = []

    # Logo y datos de la empresa
    try:
        logo = Image("assets/images/LOGO.png", width=1.5 * inch, height=1.5 * inch)
    except:
        logo = None

    business_data = [
        ["FONDO DE UGAVI PARA DESARROLLO AGROPECUARIO"],
        ["RIF: J-30646602-9"],
        ["Dirección Fiscal: Av. 23 Sector Aurora, Edificio UGAVI"],
        ["Teléfono: 0412 786 6851"]
    ]
    business_table = Table(business_data, colWidths=[4.5 * inch])
    business_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))

    header_table = Table([[business_table, logo]], colWidths=[4.5 * inch, 1.5 * inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Fecha de emisión y número de factura
    invoice_data = [
        ["Fecha de Emisión:", factura.get("FECHA", "").strftime("%d/%m/%Y"), "", "N° de Factura:", factura.get("FACT_FONDO", "")],
        ["", "", "", "Estado:", factura.get("ESTADO", "")]
    ]
    invoice_table = Table(invoice_data, colWidths=[1.5 * inch, 2 * inch, 0.5 * inch, 1.5 * inch, 2 * inch])
    invoice_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Validar si existe un cliente correspondiente al ID_MIEMBRO
    cliente_data = miembros_completo.loc[miembros_completo['RAZON_SOCIAL'] == factura.get("ID_MIEMBRO")]
    if cliente_data.empty:
        cliente = {"RAZON_SOCIAL": "N/A", "RIF": "N/A", "DIRECCION": "N/A"}
    else:
        cliente = cliente_data.iloc[0]

    # Datos del cliente
    client_data = [
        ["DATOS DEL CLIENTE"],
        ["Razón Social:", cliente["RAZON_SOCIAL"]],
        ["RIF:", cliente["RIF"]],
        ["Dirección:", cliente["DIRECCION"]]
    ]
    client_table = Table(client_data, colWidths=[2.5 * inch, 4.5 * inch])
    client_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Detalles de la factura
    item_data = [
        ["DESCRIPCIÓN", "MONTO (Bs)"],
        [factura.get('MENSUALIDADES'), f"Bs. {factura.get('MONTO_BS', 0):.2f}"]
    ]
    item_table = Table(item_data, colWidths=[4.5 * inch, 2 * inch])
    item_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 0.5 * inch))

    # Total general
    total_data = [
        ["Total General (Bs):", f"Bs. {factura.get('MONTO_BS', 0):.2f}"]
    ]
    total_table = Table(total_data, colWidths=[4.5 * inch, 2 * inch])
    total_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 0.5 * inch))

    # Pie de página: Método de Pago
    footer_data = [
        ["Método de Pago:", factura.get("METODO_PAGO", "")]
    ]
    footer_table = Table(footer_data, colWidths=[2.5 * inch, 4.5 * inch])
    footer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(footer_table)

    # Generar el PDF
    doc.build(elements)
    pdf_output.seek(0)
    return pdf_output