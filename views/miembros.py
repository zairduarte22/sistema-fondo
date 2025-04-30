import streamlit as st
import pandas as pd
from db.conexion import session, Miembro, InformacionMiembro, Saldo, obtener_df_join, obtener_df
from sqlalchemy import update, delete, text
import io
from utils.cobranzas_whatsapp import enviar_mensaje_api
from utils.bcv_tasa import tasa_bs
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import numpy as np

tasa = tasa_bs()

if 'edit' not in st.session_state:
    st.session_state.edit = True

# Comprobación de session state
if st.session_state.get('notificacion'):
    st.toast(st.session_state.notificacion)
    del st.session_state.notificacion


if 'ids_a_eliminar' not in st.session_state:
    st.session_state.ids_a_eliminar = []


@st.dialog('Confirmar Eliminación', width="large")
def confirmar_eliminacion():
    st.warning('¿Estás seguro de que quieres eliminar los siguientes registros?')
    st.write(f'Miembro(s) a eliminar: {[int(id_miembro) for id_miembro in st.session_state.ids_a_eliminar]}')
    
    col0, col2, col3 = st.columns([2,1.3,2], gap='medium')
    with col2:
        if st.button('Confirmar', use_container_width=True):
            for id_miembro in st.session_state.ids_a_eliminar:
                eliminar_miembro(id_miembro)
            mensaje = 'Miembro(s) eliminado(s).'
            st.session_state.notificacion = mensaje
            st.rerun()
            

@st.dialog('Añadir Miembro', width="large")
def añadir_miembro():
    registro = st.segmented_control('**Tipo de Registro**', ['Individual', 'Multiple'], selection_mode='single', default='Individual')
    
    if registro == 'Individual':
        col6, col7 = st.columns([2.5, 1], vertical_alignment='center')
        with col6:
            razon_social = st.text_input('**Razon Social**', placeholder="Nombre del miembro natural o juridico")
        with col7:
            saldo = st.number_input('**Saldo Pendiente**', format="%.2f", value=0.00)

        col8, col9 = st.columns([1, 1])
        with col8:
            rif = st.text_input('**Documento de Identidad**', placeholder='RIF/Cedula del Miembro')
            correo = st.text_input('**Correo**', placeholder='Dirección de correo electronico')
            direccion = st.text_input('**Dirección Fiscal**', placeholder='Dirección fiscal del Miembro')
            mes = st.text_input('**Ultimo Mes (Si aplica)**', placeholder='Ultimo mes cancelado por el miembro')
        with col9:
            representante = st.text_input('**Representante**', placeholder='Representante del Miembro')
            cedula_r = st.text_input('**Cedula**', placeholder='Cedula de Identidad del Representante')
            num_phone = st.text_input('**Número de Telefono**', placeholder='Numero en formato internacional')
            hacienda = st.text_input('**Hacienda**', placeholder='Nombre de la hacienda')

        col10, col11, col12 = st.columns([3, 1, 3], gap='small')
        with col10:
            saldo = saldo * -1
            save_changes = st.button(':material/save: Guardar')
            if save_changes:
                # Diccionarios para almacenar los campos a insertar
                campos_valores_miembro = {
                    "RAZON_SOCIAL": razon_social,
                    "RIF": rif,
                    "ULTIMO_MES": mes,
                    "SALDO": saldo
                }

                campos_valores_info_miembro = {
                    "NUM_TELEFONO": num_phone,
                    "REPRESENTANTE": representante,
                    "CI_REPRESENTANTE": cedula_r,
                    "CORREO": correo,
                    "DIRECCION": direccion,
                    "HACIENDA": hacienda
                }

                campos_valores_saldo = {
                    "DESCRIPCION": "Saldo Inicial",
                    "MONTO": saldo
                }
                
                # Insertar nuevo miembro
                nuevo_miembro = Miembro(**campos_valores_miembro)
                try:
                    session.add(nuevo_miembro)
                    session.commit()
                    nuevo_id = nuevo_miembro.ID_MIEMBRO
                except Exception as e:
                    session.rollback()
                    st.error(f'Error al insertar el nuevo miembro. Error: {e}')
                    return
                
                # Insertar saldo inicial
                campos_valores_saldo["ID_MIEMBRO"] = nuevo_id
                nuevo_saldo = Saldo(**campos_valores_saldo)
                try:
                    session.add(nuevo_saldo)
                    session.commit()
                except Exception as e:
                    session.rollback()
                    mensaje = f'Error al insertar el saldo inicial del nuevo miembro. Error: {e}'
                    st.session_state.notificacion = mensaje
                    st.rerun()

                # Insertar información del miembro
                campos_valores_info_miembro["ID_MIEMBRO"] = nuevo_id
                nueva_info_miembro = InformacionMiembro(**campos_valores_info_miembro)
                try:
                    session.add(nueva_info_miembro)
                    session.commit()
                    mensaje = 'Miembro añadido exitosamente.'
                    st.session_state.notificacion = mensaje
                    st.rerun()
                except Exception as e:
                    session.rollback()
                    mensaje = f'Error al insertar la información del nuevo miembro. Error: {e}'
                    st.session_state.notificacion = mensaje
                    st.rerun()
    else:
        # Botón para descargar el archivo modelo
        st.download_button(
            label="Descargar Archivo Modelo",
            data=generar_archivo_modelo(),
            file_name="modelo_miembros.csv",
            mime="text/csv"
        )
        
        # Subir archivo CSV
        archivo_csv = st.file_uploader("Subir archivo CSV", type=["csv"])
        if archivo_csv is not None:
            # Leer CSV reemplazando valores vacíos con None
            df = pd.read_csv(archivo_csv).replace({np.nan: None})
            st.write(df)
            
            if st.button('Cargar Datos'):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                batch_size = 50
                batches = [df[i:i + batch_size] for i in range(0, len(df), batch_size)]
                total_batches = len(batches)
                success_count = 0
                error_count = 0
                error_messages = []
                
                for i, batch in enumerate(batches):
                    try:
                        miembros_data = []
                        info_miembros_data = []
                        saldos_data = []
                        
                        for _, row in batch.iterrows():
                            # Limpiar datos y establecer valores por defecto
                            miembro_data = {
                                "ID_MIEMBRO": row.get('ID_MIEMBRO'),
                                "RAZON_SOCIAL": row.get('RAZON_SOCIAL'),
                                "RIF": row.get('RIF'),
                                "ULTIMO_MES": row.get('ULTIMO_MES'),
                                "SALDO": float(row.get('SALDO', 0)),  # Convertir a float y valor por defecto 0
                                "ESTADO": row.get('ESTADO') or 'Activo'  # Valor por defecto 'Activo'
                            }
                            # Eliminar campos con valor None
                            miembro_data = {k: v for k, v in miembro_data.items() if v is not None}
                            miembros_data.append(miembro_data)
                            
                            info_data = {
                                "ID_MIEMBRO": row.get('ID_MIEMBRO'),
                                "NUM_TELEFONO": row.get('NUM_TELEFONO'),
                                "REPRESENTANTE": row.get('REPRESENTANTE'),
                                "CI_REPRESENTANTE": row.get('CI_REPRESENTANTE'),
                                "CORREO": row.get('CORREO'),
                                "DIRECCION": row.get('DIRECCION'),
                                "HACIENDA": row.get('HACIENDA')
                            }
                            # Eliminar campos con valor None
                            info_data = {k: v for k, v in info_data.items() if v is not None}
                            info_miembros_data.append(info_data)
                            
                            saldo_data = {
                                "ID_MIEMBRO": row.get('ID_MIEMBRO'),
                                "DESCRIPCION": "Saldo Inicial",
                                "MONTO": float(row.get('SALDO', 0))  # Convertir a float y valor por defecto 0
                            }
                            saldos_data.append(saldo_data)
                        
                        # Validar datos obligatorios antes de insertar
                        for data in miembros_data:
                            if not all(k in data for k in ["ID_MIEMBRO", "RAZON_SOCIAL", "RIF"]):
                                raise ValueError(f"Faltan campos obligatorios para el miembro con ID {data.get('ID_MIEMBRO')}")
                        
                        # Insertar en lotes
                        session.bulk_insert_mappings(Miembro, miembros_data)
                        session.bulk_insert_mappings(InformacionMiembro, info_miembros_data)
                        session.bulk_insert_mappings(Saldo, saldos_data)
                        
                        session.commit()
                        success_count += len(batch)
                        
                    except Exception as e:
                        session.rollback()
                        error_count += len(batch)
                        error_messages.append(f"Error en lote {i+1}: {str(e)}")
                    
                    progress_bar.progress((i + 1) / total_batches)
                    status_text.text(f"Procesando... {i+1}/{total_batches} lotes completados")
                
                if error_count == 0:
                    st.success(f"¡Todos los {success_count} miembros fueron cargados exitosamente!")
                else:
                    st.warning(f"Se cargaron {success_count} miembros con éxito, pero hubo {error_count} errores.")
                    for msg in error_messages:
                        st.error(msg)
                
                progress_bar.empty()
                status_text.empty()
                st.rerun()

def deactivate_edit():
    st.session_state.edit = not st.session_state.edit

def actualizar_datos(tabla, id_miembro, campos_valores):
    try:
        # Construir manualmente la consulta SQL con los valores directos
        set_clause = ", ".join([f"{col} = '{val}'" for col, val in campos_valores.items()])
        query = text(f"UPDATE {tabla.name} SET {set_clause} WHERE {tabla.c.ID_MIEMBRO.name} = {id_miembro}")
        session.execute(query)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f'Se ha producido un error al tratar de realizar los cambios. Error: {e}')
        return False
    finally:
        session.close()

def eliminar_datos(tabla, id_miembro):
    try:
        query = text(f"DELETE FROM {tabla.name} WHERE {tabla.c.ID_MIEMBRO.name} = {id_miembro}")
        session.execute(query)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f'Se ha producido un error al tratar de eliminar el registro. Error: {e}')
        return False
    finally:
        session.close()

@st.dialog('Información Adicional', width="large")
def informacion_miembro(num_indice: int, dataframe: pd.DataFrame):
    info = dataframe.loc[num_indice]
    info = info.iloc

    if st.toggle('**HABILITAR EDICION**', False):
        st.session_state.edit = False
    else:
        st.session_state.edit = True

    edit = st.session_state.edit

    col6, col7 = st.columns([2.5, 1.3], vertical_alignment='center')
    with col6:
        cod = st.header(f"Cod. de miembro **N° {info[0]}**")
        razon_social = st.text_input('_Razon Social_', info[1], disabled=edit, placeholder="Razon Social")
    with col7:
        saldo = info[4]
        saldo_metrica = st.metric('Saldo Pendiente', f'$ {saldo:.2f}', f'Bs. {saldo * tasa:.2f}', "normal", help=f'Estado: {info[5]}')

    col8, col9 = st.columns([1, 1])
    with col8:
        rif = st.text_input('_Documento de Identidad_', info[2], disabled=edit)
        correo = st.text_input('_Correo_', info[10], disabled=edit)
        direccion = st.text_input('_Dirección Fiscal_', info[11], disabled=edit)
        mes = st.text_input('_Ultimo Mes_', info[3], disabled=edit)
    with col9:
        representante = st.text_input('_Representante_', info[8], disabled=edit)
        cedula_r = st.text_input('_Cedula del Representante_', info[9], disabled=edit)
        num_phone = st.text_input('Número de Telefono', info[7], disabled=edit)
        hacienda = st.text_input('_Hacienda_', info[12], disabled=edit)

    col10, col11, col12 = st.columns([1, 1, 4], gap='small')
    with col10:
        save_changes = st.button(':material/save: Guardar', disabled=edit)
        if save_changes:
            # Diccionarios para almacenar los campos a actualizar
            campos_valores_miembro = {
                "RAZON_SOCIAL": razon_social,
                "RIF": rif,
                "ULTIMO_MES": mes,
                "ESTADO": info[5]  # Asumiendo que el estado no se puede editar
            }
            campos_valores_info_miembro = {
                "NUM_TELEFONO": num_phone,
                "REPRESENTANTE": representante,
                "CI_REPRESENTANTE": cedula_r,
                "CORREO": correo,
                "DIRECCION": direccion,
                "HACIENDA": hacienda
            }
            
            # Actualizar datos en las tablas correspondientes
            exito_miembro = actualizar_datos(Miembro.__table__, info[0], campos_valores_miembro) if campos_valores_miembro else True
            exito_info_miembro = actualizar_datos(InformacionMiembro.__table__, info[0], campos_valores_info_miembro) if campos_valores_info_miembro else True
            
            # Manejar el estado de éxito o error
            if exito_miembro and exito_info_miembro:
                mensaje = 'Cambios guardados exitosamente.'
                st.session_state.notificacion = mensaje
                st.rerun()
            else:
                mensaje = 'Error al guardar los cambios.'
                st.session_state.notificacion = mensaje
                st.rerun()
            # Reiniciar la aplicación

def eliminar_miembro(id_miembro):
    try:
        # Eliminar información del miembro
        exito_info_miembro = eliminar_datos(InformacionMiembro.__table__, id_miembro)
        # Eliminar miembro
        exito_saldo_miembro = eliminar_datos(Saldo.__table__, id_miembro)
        exito_miembro = eliminar_datos(Miembro.__table__, id_miembro)
        
        if exito_info_miembro and exito_miembro:
            st.toast(f'Miembro con ID {id_miembro} eliminado exitosamente.')
    except Exception as e:
        st.toast(f'Error al eliminar el miembro con ID {id_miembro}. Error: {e}')

def style_dataframe(df):
    return df.style.set_properties(
        **{
            "border": "none",  # Quitar bordes
            "background-color": "transparent",  # Fondo transparente
        }
    )


def generar_archivo_modelo():
    output = io.StringIO()
    df_modelo = pd.DataFrame({
        "ID_MIEMBRO": pd.Series(dtype='int'),
        "RAZON_SOCIAL": pd.Series(dtype='str'),
        "RIF": pd.Series(dtype='str'),
        "ULTIMO_MES": pd.Series(dtype='str'),
        "SALDO": pd.Series(dtype='float'),
        "ESTADO": pd.Series(dtype='str'),
        "NUM_TELEFONO": pd.Series(dtype='str'),
        "REPRESENTANTE": pd.Series(dtype='str'),
        "CI_REPRESENTANTE": pd.Series(dtype='str'),
        "CORREO": pd.Series(dtype='str'),
        "DIRECCION": pd.Series(dtype='str'),
        "HACIENDA": pd.Series(dtype='str')
    })
    df_modelo.to_csv(output, index=False)
    return output.getvalue()

# Se obtienen valores de las tablas miembros e informacion_miembros mediante un join
miembros_completo = obtener_df_join(Miembro, InformacionMiembro)
miembros_base = obtener_df(Miembro)

@st.dialog('Cobranzas', width="large")
def cobranza(df):
    col0, col1 = st.columns([2, 2])
    with col0:
        seleccionar = st.selectbox('Seleccione el criterio para realizar la cobranza:', ['Por Monto', 'Por Miembro'])
    if seleccionar == 'Por Monto':
        st.write('El rango de cobranza se establece entre los siguientes valores:')
        col0, col1 = st.columns([1, 1])
        with col0:
            rango = st.number_input('Minimo:', format="%.2f", min_value=df['SALDO'].min(), max_value=df['SALDO'].max(), value=df['SALDO'].min())
        with col1:
            rango2 = st.number_input('Maximo:', format="%.2f", min_value=df['SALDO'].min(), max_value=df['SALDO'].max(), value=df['SALDO'].max())
        if st.button('Enviar Mensaje'):
            for index, row in df.iterrows():
                if row['NUM_TELEFONO'] is None:
                    continue
                else:
                    mensaje = f"*Estimado/a {row['RAZON_SOCIAL']}*, \n\nDe acuerdo con nuestros registros, su membresía presenta un adeudo de 2 meses de cuotas no cubiertas. Le informamos que, al cancelar el saldo pendiente, su situación quedará regularizada y podrá volver a disfrutar del descuento por pronto pago (reducción de $5 en la cuota mensual, quedando en $20), aplicable cuando realice la cancelacación del mes actual dentro de los primeros diez (10) días de cada mes.\n\nDetalles del adeudo:\n- Total a cancelar en divisas: $ {row['SALDO']:.2f}\n- Total a cancelar en bolivares: Bs. {row['SALDO']*tasa_bs():,.2f}\n\nBeneficios al llevar su membresía al día:\n✅ Reactivación del descuento por pronto pago:\n- Cuota mensual con descuento: $20 (válido pagando entre el día 1 y 10 de cada mes). \n\nMétodos de pago:\n🔹 Transferencia/Pago Móvil/Zelle: https://bit.ly/4hSoKVH \n\nNota importante:\nLa morosidad superior a tres meses puede afectar los beneficios de su membresía. Le invitamos a regularizar su situación para evitar inconvenientes.\n\nAtentamente,\nFondo de UGAVI para Desarrollo Agropecuario\n📞 +584246088302 | ✉ fondo@ugavired.com"
                    if row['SALDO'] >= rango and row['SALDO'] <= rango2:
                        try:
                            enviar_mensaje_api(mensaje, row['NUM_TELEFONO'])
                            st.toast(f'Mensaje enviado a {row["RAZON_SOCIAL"]}')
                        except Exception as e:
                            st.toast(f'Error al enviar el mensaje a {row["RAZON_SOCIAL"]}. Error: {e}')
            mensaje = 'Mensajes enviados exitosamente.'
            st.session_state.notificacion = mensaje
            st.rerun()
    else:
        st.write('Seleccione los miembros a los cuales desea enviar el mensaje:')
        select_miembros = st.multiselect('Miembros:', df['RAZON_SOCIAL'], placeholder='Seleccione los miembros', default=None)
        enviar_miembro = st.button('Enviar Mensaje')
        if enviar_miembro:
            for index, row in df.iterrows():
                if row['NUM_TELEFONO'] is None:
                    continue
                else:
                    if row['RAZON_SOCIAL'] in select_miembros:
                        mensaje = f"*Estimado/a {row['RAZON_SOCIAL']}*, \n\nDe acuerdo con nuestros registros, su membresía presenta un adeudo de 2 meses de cuotas no cubiertas. Le informamos que, al cancelar el saldo pendiente, su situación quedará regularizada y podrá volver a disfrutar del descuento por pronto pago (reducción de $5 en la cuota mensual, quedando en $20), aplicable cuando realice la cancelacación del mes actual dentro de los primeros diez (10) días de cada mes.\n\nDetalles del adeudo:\n- Total a cancelar en divisas: $ {row['SALDO']*-1:.2f}\n- Total a cancelar en bolivares: Bs. {row['SALDO']*(tasa_bs() * -1):,.2f}\n\nBeneficios al llevar su membresía al día:\n✅ Reactivación del descuento por pronto pago:\n- Cuota mensual con descuento: $20 (válido pagando entre el día 1 y 10 de cada mes). \n\nMétodos de pago:\n🔹 Transferencia/Pago Móvil/Zelle: https://bit.ly/4hSoKVH \n\nNota importante:\nLa morosidad superior a tres meses puede afectar los beneficios de su membresía. Le invitamos a regularizar su situación para evitar inconvenientes.\n\nAtentamente,\nFondo de UGAVI para Desarrollo Agropecuario\n📞 +584246088302 | ✉ fondo@ugavired.com"
                        try:
                            enviar_mensaje_api(row['NUM_TELEFONO'], mensaje)
                            st.toast(f'Mensaje enviado a {row["RAZON_SOCIAL"]}')
                        except Exception as e:
                            st.toast(f'Error al enviar el mensaje a {row["RAZON_SOCIAL"]}. Error: {e}')
            mensaje = 'Mensajes enviados exitosamente.'
            st.session_state.notificacion = mensaje
            st.rerun()

def generar_informe_pdf(miembros_completo):
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

# SECCIONES DE LA PAGINA
header = st.container()
datos = st.container()
tabla = st.container()
botones = st.container()

# HEADER DE LA PAGINA
with header:
    col0, col1, col3 = st.columns([6, 1, 1], vertical_alignment='center')
    with col0:
        st.title('Miembros')
        st.caption('Esta pagina contiene información reelevante con respecto a los miembros de la organización.')
    with col1:
        add = st.button(':material/add: Añadir', use_container_width=True, type='primary')
        if add:
            añadir_miembro()
    with col3:
        cobrar = st.button(':material/phone: Cobrar', use_container_width=True, type='primary')
        if cobrar:
            cobranza(miembros_completo)

with datos:
    col11, col12, col13 = st.columns(3)
    with col11:
        st.metric('TOTAL MIEMBROS', len(miembros_base['RAZON_SOCIAL']))
    with col12:
        st.metric('MIEMBROS SOLVENTES', len(miembros_base[miembros_base['ESTADO'] == 'SOLVENTE']))
    with col13:
        st.metric('MIEMBROS INSOLVENTES', len(miembros_base[miembros_base['ESTADO'] == 'INSOLVENTE']))

# DATAFRAME CON LOS DATOS DE LOS MIEMBROS
with tabla:
    if miembros_base.empty:
        st.warning('No hay datos para mostrar')
        seleccion = []
    elif not miembros_base.empty:
        # Selección de las columnas a mostrar
        miembros = miembros_base[["ID_MIEMBRO", "RAZON_SOCIAL", "RIF", "ULTIMO_MES", "SALDO", "ESTADO"]]
        # Configuración de las columnas
        conf_col = {
            "ID_MIEMBRO": st.column_config.NumberColumn("Cod."),
            "RAZON_SOCIAL": st.column_config.TextColumn("Razón Social"),
            "RIF": st.column_config.TextColumn("Documento"),
            "ULTIMO_MES": st.column_config.TextColumn("Mensualidad"),
            "SALDO": st.column_config.NumberColumn("Saldo", format="$ %.2f"),
            "ESTADO": st.column_config.TextColumn("Estado")
        }
        
        # DataFrame final con todas las configuraciones
        miembros_df = st.dataframe(miembros,
            use_container_width=True, 
            hide_index=True, 
            column_config=conf_col,
            on_select='rerun',
            selection_mode='multi-row')
        

        # Lista con los índices de las columnas seleccionadas
        seleccion = miembros_df.selection.rows

    else:
        st.warning('No se han encontrado datos en esta tabla')

# BOTONES PARA INTERACTUAR CON LA TABLA
with botones:
    col2, col3, col4 = st.columns([1.3, 1.5, 7], gap='small', vertical_alignment='center')
    with col2:
        if len(seleccion) > 0:
            delete = st.button(':material/delete: Eliminar', use_container_width=True, type='primary')
            if delete:
                st.session_state.ids_a_eliminar = [miembros_base.loc[i, "ID_MIEMBRO"] for i in seleccion]
                print(st.session_state.ids_a_eliminar)
                confirmar_eliminacion()
    with col3:
        if len(seleccion) == 1:
            more = st.button(':material/post_add: Ver/Editar', use_container_width=True, type='secondary')
            if more:
                informacion_miembro(seleccion[0], miembros_completo)
    col5, col6 = st.columns([1.5, 8])
    with col5:
        if st.button(':material/download: Informe', use_container_width=True, type='primary'):
            pdf_buffer = generar_informe_pdf(miembros_completo)
            st.download_button(
                label="PDF",
                data=pdf_buffer,
                file_name="informe_miembros.pdf",
                mime="application/pdf"
            )
