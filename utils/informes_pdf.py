from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import io
import pandas as pd
import streamlit as st

pdfmetrics.registerFont(TTFont("Lato Bold", "assets/fonts/Lato/Lato-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Lato Regular", "assets/fonts/Lato/Lato-Regular.ttf"))


def generar_informe_pdf_miembros(miembros_completo, grupos: list, campos: list):
    miembros = miembros_completo.sort_values(by=grupos, ascending=False)
    # Crear un buffer para el PDF
    buffer = io.BytesIO()
    # Configurar la página en orientación horizontal (landscape) con márgenes pequeños
    if len(campos) > 4:
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),  # Página horizontal
            rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20  # Márgenes pequeños
        )
    else:
        # Si hay menos de 4 campos, usar orientación vertical  
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,  # Página horizontal
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
    
    encabezados = []
    contenido = []
    medidas = []
    
    for campo in campos:
        contenido.append(str(campo))
        if campo == "ID_MIEMBRO":
            encabezados.append("ID")
            medidas.append(0.50 * inch)
        elif campo == "RAZON_SOCIAL":
            encabezados.append("Razón Social")
            medidas.append(4.25 * inch)
        elif campo == "RIF":
            encabezados.append("RIF")
            medidas.append(1.25 * inch)
        elif campo == "ULTIMO_MES":
            encabezados.append("Último Mes")
            medidas.append(1.25 * inch)
        elif campo == "SALDO":
            encabezados.append("Saldo")
            medidas.append(1.25 * inch)
        elif campo == "NUM_TELEFONO":
            encabezados.append("Teléfono")
            medidas.append(1.25 * inch)
        elif campo == "REPRESENTANTE":
            encabezados.append("Representante")
            medidas.append(1.25 * inch)
        elif campo == "CI_REPRESENTANTE":
            encabezados.append("CI Representante")
            medidas.append(1.25 * inch)
        elif campo == "CORREO":
            encabezados.append("Correo")
            medidas.append(1.25 * inch)
        elif campo == "DIRECCION":
            encabezados.append("Dirección")
            medidas.append(1.25 * inch)
        elif campo == "HACIENDA":
            encabezados.append("Hacienda")
            medidas.append(1.25 * inch)
        elif campo == "ESTADO":
            encabezados.append("Estado")
            medidas.append(1.25 * inch)
        else:
            st.toast(f"Campo desconocido: {campo}", "error")
            return None

    # Tabla de datos
    data = [encabezados] + [
        [
            row[x] for x in contenido
        ]
        for _, row in miembros.iterrows()
    ]
    st.toast(medidas)

    table = Table(data, colWidths=medidas)  # Ajustar el ancho de las columnas
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


def generar_reporte_con_formato_imagen(facturas_completo, filtro_reporte, descargar_pdf=True, logo_path=None):
    if isinstance(filtro_reporte, tuple) and len(filtro_reporte) == 2:
        fecha_inicio_str, fecha_fin_str = filtro_reporte

        # Asegurarse que las fechas en el DataFrame y las de filtro sean datetime
        # (Descomentar y ajustar si 'FECHA' no es datetime o las fechas de filtro no lo son)
        # facturas_completo['FECHA'] = pd.to_datetime(facturas_completo['FECHA'], errors='coerce')
        # fecha_inicio = pd.to_datetime(fecha_inicio_str)
        # fecha_fin = pd.to_datetime(fecha_fin_str)
        
        # Para este ejemplo, se asume que fecha_inicio_str y fecha_fin_str ya son objetos de fecha o strings parseables por pd.to_datetime
        fecha_inicio = pd.to_datetime(fecha_inicio_str)
        fecha_fin = pd.to_datetime(fecha_fin_str)


        facturas_filtradas = facturas_completo[
            (pd.to_datetime(facturas_completo['FECHA']) >= fecha_inicio) & (pd.to_datetime(facturas_completo['FECHA']) <= fecha_fin)
        ]

        # --- Tabla 1: Cuotas recibidas en Bs. (Pago Movil/Transferencia) ---
        pago_movil = facturas_filtradas[facturas_filtradas['METODO_PAGO'] == 'Pago Movil/Transferencia'].copy()
        if not pago_movil.empty:
            pago_movil.loc[:, 'Monto Original Bs'] = pago_movil['MONTO_BS']
            pago_movil.loc[:, 'UGAVI 60% Bs'] = pago_movil['MONTO_BS'] * 0.6
            pago_movil.loc[:, 'Club 20% Bs'] = pago_movil['MONTO_BS'] * 0.2
            pago_movil.loc[:, 'Total Bs (80%)'] = pago_movil['MONTO_BS'] * 0.8
            total_monto_bs_tabla1 = pago_movil['Monto Original Bs'].sum()
            total_ugavi_bs_tabla1 = pago_movil['UGAVI 60% Bs'].sum()
            total_club_bs_tabla1 = pago_movil['Club 20% Bs'].sum()
            total_total_bs_tabla1 = pago_movil['Total Bs (80%)'].sum()
        else:
            pago_movil = pd.DataFrame(columns=['FECHA', 'FACT_UGAVI', 'Monto Original Bs', 'UGAVI 60% Bs', 'Club 20% Bs', 'Total Bs (80%)'])
            total_monto_bs_tabla1 = 0
            total_ugavi_bs_tabla1 = 0
            total_club_bs_tabla1 = 0
            total_total_bs_tabla1 = 0
        
        pago_movil.reset_index(drop=True, inplace=True)
        pago_movil.index += 1


        # --- Tabla 2: Cuotas Recibidas en Divisas (Zelle / Efectivo Divisas) ---
        otros_metodos = facturas_filtradas[facturas_filtradas['METODO_PAGO'].isin(['Zelle', 'Efectivo Divisas'])].copy()
        if not otros_metodos.empty:
            # Asegurarse que MONTO_DIVISAS sea numérico
            otros_metodos.loc[:, 'MONTO_DIVISAS'] = pd.to_numeric(otros_metodos['MONTO_DIVISAS'], errors='coerce').fillna(0)
            otros_metodos.loc[:, 'Monto $'] = otros_metodos['MONTO_DIVISAS']
            otros_metodos.loc[:, '60% $'] = otros_metodos['MONTO_DIVISAS'] * 0.6
            otros_metodos.loc[:, '20% $'] = otros_metodos['MONTO_DIVISAS'] * 0.2
            otros_metodos.loc[:, '60% Bs.'] = otros_metodos['MONTO_BS'] * 0.6
            otros_metodos.loc[:, '20% Bs.'] = otros_metodos['MONTO_BS'] * 0.2
            total_monto_div_tabla2 = otros_metodos['Monto $'].sum()
            total_ugavi_div_tabla2 = otros_metodos['60% $'].sum()
            total_ugavi_bs_div_tabla2 = otros_metodos['60% Bs.'].sum()
            total_club_div_tabla2 = otros_metodos['20% $'].sum()
            total_club_bs_div_tabla2 = otros_metodos['20% Bs.'].sum()
        else:
            otros_metodos = pd.DataFrame(columns=['FECHA', 'FACT_UGAVI', 'Monto $','60% $', '20% $', '60 Bs.', '20% Bs.'])
            total_monto_div_tabla2 = 0
            total_ugavi_div_tabla2 = 0
            total_ugavi_bs_div_tabla2 = 0
            total_club_div_tabla2 = 0
            total_club_bs_div_tabla2 = 0

        otros_metodos.reset_index(drop=True, inplace=True)
        otros_metodos.index += 1

        # --- Overall Totals for Header Boxes and Repartimiento Table ---
        grand_total_recibido_bs = total_monto_bs_tabla1
        grand_total_recibido_divisas = total_monto_div_tabla2

        reparto_ugavi_bs = grand_total_recibido_bs * 0.6
        reparto_club_bs  = grand_total_recibido_bs * 0.2
        reparto_fondo_bs = grand_total_recibido_bs * 0.2 # El 20% restante para el fondo

        reparto_ugavi_divisas = grand_total_recibido_divisas * 0.6
        reparto_club_divisas  = grand_total_recibido_divisas * 0.2
        reparto_fondo_divisas = grand_total_recibido_divisas * 0.2 # El 20% restante para el fondo
        
        if descargar_pdf:
            pdf_output = io.BytesIO()
            doc = SimpleDocTemplate(pdf_output, pagesize=letter,
                                    rightMargin=30, leftMargin=30, # Margenes un poco más amplios
                                    topMargin=30, bottomMargin=30)

            styles = getSampleStyleSheet()
            
            # Estilo para el título principal del reporte
            report_main_title_style = styles["h1"]
            report_main_title_style.alignment = 1 # Centrado
            report_main_title_style.fontSize = 16
            report_main_title_style.fontName = 'Lato Bold'
            report_main_title_style.leading = 5 # Espacio entre líneas 

            # Estilo para el subtítulo (periodo)
            period_subtitle_style = styles["h2"]
            period_subtitle_style.alignment = 1 # Centrado
            period_subtitle_style.fontSize = 12
            period_subtitle_style.fontName = 'Lato Regular'
            
            # Estilo para información en el encabezado (Total Bs, Total $)
            header_info_style = styles["Normal"]
            header_info_style.fontSize = 30
            header_info_style.fontName = 'Lato Bold'
            header_info_style.alignment = 1 # Centrado

            # Estilo para los títulos de las tablas de cuotas
            table_section_title_style = styles["h3"]
            table_section_title_style.alignment = 1 # Izquierda
            table_section_title_style.fontSize = 11
            table_section_title_style.fontName = 'Lato Bold'

            elements = []
            page_width_available = letter[0] - doc.leftMargin - doc.rightMargin


            # --- Sección de Encabezado: Logo, Título, Periodo ---
            report_title_text = "Reporte de Ingresos por Cuotas de Miembros"
            period_text = f"Periodo: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"

            header_content_right = [
                Paragraph(report_title_text, report_main_title_style),
                Paragraph(period_text, period_subtitle_style)
            ]
            
            if logo_path:
                try:
                    logo_img = Image(logo_path, width=0.75*inch, height=0.75*inch)
                    logo_width = 0.85*inch
                    title_width = page_width_available - logo_width - 6 
                    header_table_data = [[logo_img, header_content_right]]
                    header_layout_table = Table(header_table_data, colWidths=[logo_width, title_width])
                    header_layout_table.setStyle(TableStyle([
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('ALIGN', (0,0), (0,0), 'LEFT'),      
                        ('ALIGN', (1,0), (1,-1), 'CENTER'), 
                        ('LEFTPADDING', (0,0), (0,0), 50),
                        ('RIGHTPADDING', (0,0), (0,0), 1), # Espacio entre logo y título
                    ]))
                    elements.append(header_layout_table)
                except Exception as e:
                    print(f"Error al cargar el logo: {e}. Omitiendo logo.")
                    elements.extend(header_content_right) # Añadir solo texto si el logo falla
            else: # Sin logo
                elements.extend(header_content_right)
            
            elements.append(Spacer(1, 0.1*inch))

            # --- Sección de Resumen: Total Bs/$, Tabla Repartimiento (lado a lado) ---
            elements.append(Paragraph("Total Recibido", report_main_title_style))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(f"<b>Bs.</b> {grand_total_recibido_bs:,.2f} | <b>$</b> {grand_total_recibido_divisas:,.2f}", header_info_style))

            data_repartimiento = [
                ["Departamento", "Bolívares (Bs.)", "Divisas ($)"],
                ["UGAVI 60%", f"Bs. {reparto_ugavi_bs:,.2f}", f"$ {reparto_ugavi_divisas:,.2f}"],
                ["Club 20%", f"Bs. {reparto_club_bs:,.2f}", f"$ {reparto_club_divisas:,.2f}"],
                ["Fondo 20%", f"Bs. {reparto_fondo_bs:,.2f}", f"$ {reparto_fondo_divisas:,.2f}"]
            ]
            repart_col_widths = [2*inch, 1.7*inch, 1.6*inch] # Total ~3.5 inch
            table_repartimiento = Table(data_repartimiento, colWidths=repart_col_widths)
            table_repartimiento.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen), # Gris claro para encabezado
                ('TEXTCOLOR', (0, 0), (-1,-1), colors.black),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Lato Regular'),
                ('FONTNAME', (0, 1), (-1, -1), 'Lato Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 15),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.transparent),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('TOPPADDING', (0,0), (-1,-1), 5),
            ]))
            
            elements.append(Spacer(1, 0.5*inch))
            elements.append(table_repartimiento)
            elements.append(Spacer(1, 0.15*inch))


            # --- Tabla 1: Cuotas recibidas en Bs. ---
            elements.append(Paragraph("Cuotas Recibidas en Bs. (Pago Móvil/Transferencia)", table_section_title_style))
            
            data_pago_movil = [["N°", "Fecha", "N° Factura", "Monto Bs", " 60% Bs.", "20% Bs.", "Total Bs (80%)"]]
            for index, row in pago_movil.iterrows():
                data_pago_movil.append([
                    index,
                    pd.to_datetime(row["FECHA"]).strftime('%d/%m/%Y') if pd.notnull(row["FECHA"]) else '',
                    row["FACT_UGAVI"],
                    f"Bs. {row['Monto Original Bs']:,.2f}", f"Bs. {row['UGAVI 60% Bs']:,.2f}",
                    f"Bs. {row['Club 20% Bs']:,.2f}", f"Bs. {row['Total Bs (80%)']:,.2f}"
                ])
            data_pago_movil.append([
                "TOTALES", "", "", f"Bs. {total_monto_bs_tabla1:,.2f}", f"Bs.{total_ugavi_bs_tabla1:,.2f}",
                f"Bs. {total_club_bs_tabla1:,.2f}", f"Bs. {total_total_bs_tabla1:,.2f}"
            ])
            
            table_pago_movil_cols = [0.4*inch, 0.8*inch, 0.9*inch, 1*inch, 1.1*inch, 1*inch, 1.1*inch] # Ajustar según necesidad
            table_pago_movil = Table(data_pago_movil, colWidths=table_pago_movil_cols, repeatRows=1)
            table_pago_movil.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (-1,-1), (-1,-1), 'LEFT'),
                ('ALIGN', (0,1), (0,-2), 'CENTER'), # Item
                ('ALIGN', (1,1), (1,-2), 'CENTER'), # Fecha
                ('ALIGN', (2,1), (2,-2), 'CENTER'),   # Factura
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('BOX', (0,0), (-1,-1), 1, colors.black),
                ('LINEBELOW', (0,0), (-1,-2), 1, colors.black), # Líneas horizontales internas
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#E0E0E0")),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                ('ALIGN', (0,-1), (0,-1), 'LEFT'), # "TOTALES"
            ]))
            elements.append(table_pago_movil)
            elements.append(Spacer(1, 0.25*inch))

            # --- Tabla 2: Cuotas Recibidas en Divisas ---
            elements.append(Paragraph("Cuotas Recibidas en Divisas (Zelle/Efectivo)", table_section_title_style))
            
            data_otros_metodos = [["N°", "Fecha", "N° Factura", "Monto $", "60% $", "20% $", "60% Bs.", "20% Bs."]]
            for index, row in otros_metodos.iterrows():
                data_otros_metodos.append([
                    index,
                    pd.to_datetime(row["FECHA"]).strftime('%d/%m/%Y') if pd.notnull(row["FECHA"]) else '',
                    row["FACT_UGAVI"],
                    f"$ {row['Monto $']:,.2f}", f"$ {row['60% $']:,.2f}", f"$ {row['20% $']:,.2f}",
                    f"Bs. {row['60% Bs.']:,.2f}", f"Bs. {row['20% Bs.']:,.2f}"
                ])
            data_otros_metodos.append([
                "TOTALES", "", "", f"$ {total_monto_div_tabla2:,.2f}", f"$ {total_ugavi_div_tabla2:,.2f}",
                f"$ {total_club_div_tabla2:,.2f}", f"Bs. {total_ugavi_bs_div_tabla2:,.2f}", f"Bs. {total_club_bs_div_tabla2:,.2f}"
            ])
            
            table_otros_metodos_cols = [0.4*inch, 0.7*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.1*inch, 1.1*inch] # Usar mismos anchos
            table_otros_metodos = Table(data_otros_metodos, colWidths=table_otros_metodos_cols, repeatRows=1)
            table_otros_metodos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0,0), (2,0), 'CENTER'), 
                ('ALIGN', (0,1), (0,-2), 'CENTER'), # Item
                ('ALIGN', (1,1), (1,-2), 'CENTER'), # Fecha
                ('ALIGN', (2,1), (2,-2), 'CENTER'),   # Factura
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('BOX', (0,0), (-1,-1), 1, colors.black),
                ('LINEBELOW', (0,0), (-1,-2), 1, colors.black), # Líneas horizontales internas
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#E0E0E0")),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                ('ALIGN', (0,-1), (0,-1), 'LEFT'), # "TOTALES"
            ]))
            elements.append(table_otros_metodos)
            
            doc.build(elements)
            pdf_output.seek(0)
            return pdf_output
    return None
