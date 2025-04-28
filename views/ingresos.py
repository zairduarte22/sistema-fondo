import streamlit as st
import pandas as pd
from db.conexion import session, Ingreso, obtener_df_join, Miembro
from datetime import date, datetime
from sqlalchemy.orm import aliased
from sqlalchemy import select
from sqlalchemy.exc import PendingRollbackError
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io

if PendingRollbackError:
    session.rollback()

if 'edit' not in st.session_state:
    st.session_state.edit = True

if 'notificacion' in st.session_state:
    st.toast(st.session_state.notificacion)
    del st.session_state.notificacion

if 'selected_movimiento' not in st.session_state:
    st.session_state.selected_movimiento = None

# Crear un alias para la tabla Miembro
miembro_alias = aliased(Miembro)

# Realizar el join manualmente y seleccionar las columnas necesarias
query = (
    select(
        Ingreso.ID_INGRESO,
        Ingreso.FECHA,
        Ingreso.CUENTA_CONTABLE,
        Ingreso.TIPO_INGRESO,
        miembro_alias.RAZON_SOCIAL.label("TITULAR"),  # Mostrar la razón social
        Ingreso.METODO_PAGO,
        Ingreso.DETALLE,
        Ingreso.MONTO,
        Ingreso.MONTO_DIVISAS,
        Ingreso.REFERENCIA,
        Ingreso.NUMERO_FACTURA,
        Ingreso.NUMERO_CONTROL,
        Ingreso.BENEFICIARIO
    )
    .join(miembro_alias, Ingreso.TITULAR == miembro_alias.ID_MIEMBRO)
)

# Ejecutar la consulta y obtener los resultados como una lista de tuplas
resultados = session.execute(query).fetchall()

# Convertir los resultados en un DataFrame de pandas
movimientos = pd.DataFrame(resultados, columns=[
    "ID_INGRESO", "FECHA", "CUENTA_CONTABLE", "TIPO_INGRESO", "TITULAR",
    "METODO_PAGO", "DETALLE", "MONTO", "MONTO_DIVISAS", "REFERENCIA",
    "NUMERO_FACTURA", "NUMERO_CONTROL", "BENEFICIARIO"
])

@st.dialog("Registro de Ingreso", width="large")
def agregar_movimiento():
    st.header('Registrar Nuevo Ingreso')
    col13, col14 = st.columns(2)

    with col13:
        fecha = st.date_input('Fecha', value=date.today())
        tipo_ingreso = st.text_input('Tipo de Ingreso')
        beneficiario = st.text_input('Beneficiario')
        metodo_pago = st.text_input('Método de Pago')
        detalle = st.text_input('Detalle')
    with col14:
        monto = st.number_input('Monto', min_value=0.0, step=0.01, format="%.2f")
        monto_divisas = st.number_input('Monto Divisas', min_value=0.0, step=0.01, format="%.2f")
        referencia = st.text_input('Referencia')
        numero_factura = st.text_input('Número Factura')
        numero_control = st.text_input('Número Control')

    col10, col11, col12 = st.columns([1, 1, 4], gap='small')
    with col10:
        save_changes = st.button(':material/save: Guardar')
        if save_changes:
            # Diccionario para almacenar los campos a insertar en Ingreso
            campos_valores_movimiento = {
                "FECHA": fecha,
                "TIPO_INGRESO": tipo_ingreso,
                "BENEFICIARIO": beneficiario,
                "METODO_PAGO": metodo_pago,
                "DETALLE": detalle,
                "MONTO": monto,
                "MONTO_DIVISAS": monto_divisas,
                "REFERENCIA": referencia,
                "NUMERO_FACTURA": numero_factura,
                "NUMERO_CONTROL": numero_control
            }

            # Insertar nuevo ingreso
            nuevo_movimiento = Ingreso(**campos_valores_movimiento)
            try:
                session.add(nuevo_movimiento)
                session.commit()
                st.session_state.notificacion = 'Ingreso registrado exitosamente'
                st.rerun()
            except Exception as e:
                session.rollback()
                st.session_state.notificacion = f'Error al insertar el ingreso: {e}'
                st.rerun()

@st.dialog("Eliminar Ingreso", width="large")
def eliminar_movimiento():
    st.warning('¿Estás seguro de que quieres eliminar los siguientes ingresos?')
    for index in st.session_state.selected_movimiento:
        st.write(f'ID Ingreso: {movimientos.loc[index, "ID_INGRESO"]}')

    col0, col1, col2, col3 = st.columns([2, 1.3, 1.3, 2], gap='medium')
    with col0:
        if st.button('Confirmar', use_container_width=True):
            for index in st.session_state.selected_movimiento:
                try:
                    session.query(Ingreso).filter(Ingreso.ID_INGRESO == movimientos.loc[index, "ID_INGRESO"]).delete()
                    session.commit()
                except Exception as e:
                    session.rollback()
                    st.session_state.notificacion = f'Error al eliminar el ingreso: {e}'
                    st.rerun()
                    return
            st.session_state.notificacion = 'Ingreso(s) eliminado(s) exitosamente'
            st.rerun()

@st.dialog("Editar Ingreso", width="large")
def editar_movimiento():
    movimiento = st.session_state.selected_movimiento
    if movimiento is None:
        st.error('No se ha seleccionado ningún ingreso para editar.')
        return

    col13, col14 = st.columns([1, 1])
    with col13:
        fecha = st.date_input('Fecha', value=movimiento['FECHA'], disabled=st.session_state.edit)
        tipo_ingreso = st.text_input('Tipo de Ingreso', value=movimiento['TIPO_INGRESO'], disabled=st.session_state.edit)
        beneficiario = st.text_input('Beneficiario', value=movimiento['BENEFICIARIO'], disabled=st.session_state.edit)
        metodo_pago = st.text_input('Método de Pago', value=movimiento['METODO_PAGO'], disabled=st.session_state.edit)
        detalle = st.text_input('Detalle', value=movimiento['DETALLE'], disabled=st.session_state.edit)
    with col14:
        # Convertir Decimal a float para evitar errores
        monto = st.number_input(
            'Monto',
            min_value=0.0,
            step=0.01,
            value=float(movimiento['MONTO']),  # Conversión a float
            format="%.2f",
            disabled=st.session_state.edit
        )
        monto_divisas = st.number_input(
            'Monto Divisas',
            min_value=0.0,
            step=0.01,
            value=float(movimiento['MONTO_DIVISAS']),  # Conversión a float
            format="%.2f",
            disabled=st.session_state.edit
        )
        referencia = st.text_input('Referencia', value=movimiento['REFERENCIA'], disabled=st.session_state.edit)
        numero_factura = st.text_input('Número Factura', value=movimiento['NUMERO_FACTURA'], disabled=st.session_state.edit)
        numero_control = st.text_input('Número Control', value=movimiento['NUMERO_CONTROL'], disabled=st.session_state.edit)

    col10, col11, col12 = st.columns([1, 1, 4], gap='small')
    with col10:
        def toggle_edit():
            st.session_state.edit = not st.session_state.edit
        st.button(':material/edit: Editar', on_click=toggle_edit, use_container_width=True)

    with col11:
        save_changes = st.button(':material/save: Guardar', use_container_width=True)
        if save_changes:
            # Diccionario para almacenar los campos a actualizar en Ingreso
            campos_valores_movimiento = {
                "FECHA": fecha,
                "TIPO_INGRESO": tipo_ingreso,
                "BENEFICIARIO": beneficiario,
                "METODO_PAGO": metodo_pago,
                "DETALLE": detalle,
                "MONTO": monto,
                "MONTO_DIVISAS": monto_divisas,
                "REFERENCIA": referencia,
                "NUMERO_FACTURA": numero_factura,
                "NUMERO_CONTROL": numero_control
            }

            # Actualizar ingreso
            try:
                session.query(Ingreso).filter(Ingreso.ID_INGRESO == movimiento['ID_INGRESO']).update(campos_valores_movimiento)
                session.commit()
                st.session_state.notificacion = 'Ingreso actualizado exitosamente'
                st.rerun()
            except Exception as e:
                session.rollback()
                st.session_state.notificacion = f'Error al actualizar el ingreso: {e}'
                st.rerun()

@st.dialog("Seleccionar Rango de Fechas para el Informe", width="large")
def seleccionar_rango_fechas():
    st.session_state.fecha_inicio = st.date_input("Fecha Inicio", value=datetime.now().replace(day=1).date())
    st.session_state.fecha_fin = st.date_input("Fecha Fin", value=datetime.now().date())
    confirmar_reporte = st.button("Confirmar")
    if confirmar_reporte:
        st.session_state.generar_reporte = True
        st.toast("Rango de fechas seleccionado. Ahora puedes generar el informe.")
        st.rerun()

def generar_informe_pdf(movimientos_filtrados):
    # Crear un buffer para el PDF
    buffer = io.BytesIO()
    # Configurar la página en orientación horizontal (landscape) con márgenes amplios
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    # Estilos
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    subtitle_style = styles["Heading2"]
    normal_style = styles["BodyText"]

    # Contenido del PDF
    elements = []

    # Título
    elements.append(Paragraph("Informe de Ingresos", title_style))
    elements.append(Spacer(1, 12))

    # Subtítulo con rango de fechas
    fecha_inicio, fecha_fin = filtro  # Usar el rango de fechas de la variable filtro
    elements.append(Paragraph(f"Rango de Fechas: {fecha_inicio} - {fecha_fin}", subtitle_style))
    elements.append(Spacer(1, 12))

    # Tabla de datos
    data = [["ID", "Fecha", "Tipo", "Titular", "Beneficiario", "Método", "Monto (Bs.)", "Monto ($)", "Factura", "Control"]] + [
        [
            row["ID_INGRESO"],
            row["FECHA"].strftime("%d/%m/%Y"),
            row["TIPO_INGRESO"],
            row["TITULAR"],
            row["BENEFICIARIO"],
            row["METODO_PAGO"],
            f"Bs. {row['MONTO']:.2f}",
            f"$ {row['MONTO_DIVISAS']:.2f}",
            row["NUMERO_FACTURA"],
            row["NUMERO_CONTROL"]
        ]
        for _, row in movimientos_filtrados.iterrows()
    ]

    # Ajustar el ancho de las columnas para que quepan en la hoja
    col_widths = [30, 60, 60, 80, 80, 60, 60, 60, 60, 60]

    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),  # Reducir el tamaño de la fuente
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),  # Reducir el padding inferior
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),  # Reducir el padding izquierdo
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),  # Reducir el padding derecho
    ]))

    # Agregar la tabla a los elementos
    elements.append(table)

    # Construir el PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Secciones de la página
header = st.container()
tabla = st.container()
botones = st.container()

with header:
    st.title('Gestión de Ingresos')
    col1, col0, col2 = st.columns([2, 4, 1], vertical_alignment='center')
    with col1:
        # Filtro de fecha: primer día del mes actual hasta hoy
        filtro = st.date_input(
            'Filtrar por fecha:',
            value=(datetime.now().replace(day=1).date(), datetime.now().date()),
            format='DD/MM/YYYY'
        )
    with col2:
        add_mov = st.button(':material/add: Nuevo', type='primary')
        if add_mov:
            agregar_movimiento()

# Configuración de la tabla
with tabla:
    if movimientos.empty:
        st.divider()
        col4, col5, col6 = st.columns([2.4,1.2,2.4])
        with col5:
            st.warning('No hay ingresos registrados')
            seleccion = []
    else:
        # Aplicar el filtro de fecha
        if isinstance(filtro, tuple) and len(filtro) == 2:
            fecha_inicio, fecha_fin = filtro
            movimientos = movimientos[
                (movimientos['FECHA'] >= fecha_inicio) & (movimientos['FECHA'] <= fecha_fin)
            ]

        # Configurar las columnas a mostrar (excluyendo TITULAR y CUENTA_CONTABLE)
        movimientos_filtrado = movimientos[[
            "ID_INGRESO", "FECHA", "TIPO_INGRESO", "TITULAR", "BENEFICIARIO",
            "METODO_PAGO", "DETALLE", "MONTO", "MONTO_DIVISAS", "REFERENCIA",
            "NUMERO_FACTURA", "NUMERO_CONTROL"
        ]]
        conf_col = {
            'ID_INGRESO': st.column_config.NumberColumn('ID'),
            "FECHA": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "TIPO_INGRESO": st.column_config.TextColumn("Tipo de Ingreso"),
            "TITULAR": st.column_config.TextColumn("Titular"),
            "BENEFICIARIO": st.column_config.TextColumn("Beneficiario"),  # Razón social
            "METODO_PAGO": st.column_config.TextColumn("Método de Pago"),
            "DETALLE": st.column_config.TextColumn("Detalle"),
            "MONTO": st.column_config.NumberColumn("Bs. ", format="Bs. %.2f"),
            "MONTO_DIVISAS": st.column_config.NumberColumn("$", format="$ %.2f"),
            "REFERENCIA": st.column_config.TextColumn("Referencia"),
            "NUMERO_FACTURA": st.column_config.TextColumn("N° Factura"),
            "NUMERO_CONTROL": st.column_config.TextColumn("N°Control"),
        }
        movimientos_df = st.dataframe(
            movimientos_filtrado,
            use_container_width=True,
            hide_index=True,
            column_config=conf_col,
            on_select='rerun',
            selection_mode="multi-row"
        )
        seleccion = movimientos_df.selection.rows

with botones:
    # Botones de acción
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if len(seleccion) >= 1:
            delete_movimiento = st.button(':material/delete: Eliminar Movimiento', type='primary')
            if delete_movimiento and seleccion:
                st.session_state.selected_movimiento = seleccion
                eliminar_movimiento()
    with col2:
        if len(seleccion) == 1:
            edit_movimiento = st.button(':material/edit: Ver/Editar', type='primary')
            if edit_movimiento and seleccion:
                st.session_state.selected_movimiento = movimientos.loc[seleccion[0]].to_dict()
                editar_movimiento()

    col1, col2 = st.columns([1, 4])
    with col1:
        generar_reporte = st.button(':material/download: Generar Informe PDF', type='primary')
        if generar_reporte:
            # Filtrar los movimientos por el rango de fechas de la variable filtro
            if isinstance(filtro, tuple) and len(filtro) == 2:
                fecha_inicio, fecha_fin = filtro
                movimientos_filtrados = movimientos[
                    (movimientos["FECHA"] >= fecha_inicio) & (movimientos["FECHA"] <= fecha_fin)
                ]

                # Generar el PDF
                pdf_buffer = generar_informe_pdf(movimientos_filtrados)

                # Descargar el PDF
                st.download_button(
                    label="Descargar Informe en PDF",
                    data=pdf_buffer,
                    file_name="informe_ingresos.pdf",
                    mime="application/pdf"
                )

