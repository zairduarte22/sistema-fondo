import streamlit as st
import pandas as pd
from db.conexion import session, Miembro, InformacionMiembro, Saldo, obtener_df_join, obtener_df
from sqlalchemy import update, delete, text
import io
from utils.cobranzas_whatsapp import enviar_mensaje_api
from utils.bcv_tasa import tasa_bs
import numpy as np
from utils.informes_pdf import generar_informe_pdf_miembros, model_member_add_csv
import time
import datetime

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
    ids_miembros = [int(id_miembro) for id_miembro in st.session_state.ids_a_eliminar]
    st.write(f'Miembro(s) a eliminar: {ids_miembros}')
    if st.button('Confirmar'):
        status = st.status('Eliminando miembros...', expanded=True, state='running')
        for id_miembro in ids_miembros:
            if eliminar_miembro(id_miembro):
                with status:
                    st.write(f"Miembro {id_miembro} eliminado exitosamente.")
            else:
                with status:
                    st.error(f"Error al eliminar el miembro {id_miembro}.")
                    status.update(label='Hubo un error inesperado :(', state='error', expanded=False)
        status.update(label='Eliminación completada', state='complete', expanded=False)
        st.session_state.notificacion = 'Miembro(s) eliminado(s).'
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
        archivo_csv = st.file_uploader("Subir archivo CSV", type=["csv"])
        st.download_button(
            label="¿Aún no tienes un archivo CSV? **Descarga el modelo aquí**",
            data=model_member_add_csv(),
            file_name="modelo_miembros.csv",
            mime="text/csv",
            type='tertiary'
        )
        if archivo_csv is not None:
            try:
                # Leer y limpiar datos
                df = pd.read_csv(archivo_csv, keep_default_na=False, na_values=['', 'NA', 'N/A', 'NaN'])
                df = df.replace({np.nan: None, 'nan': None, 'NaN': None})
                
                st.write("Vista previa de los datos:")
                st.dataframe(df.head())

                if st.button('Cargar Datos', key='cargar_csv'):
                    # Obtener IDs existentes
                    ids_existentes = {id_[0] for id_ in session.query(Miembro.ID_MIEMBRO).all()}
                    
                    # Separar DataFrame
                    nuevos = df[~df['ID_MIEMBRO'].isin(ids_existentes)]
                    existentes = df[df['ID_MIEMBRO'].isin(ids_existentes)]
                    
                    st.info(f"Registros nuevos: {len(nuevos)} | Registros existentes: {len(existentes)}")
                    
                    # Procesar en lotes
                    batch_size = 50
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    total_ops = len(nuevos) + len(existentes)
                    
                    # 1. Procesar NUEVOS registros (INSERCIÓN)
                    if len(nuevos) > 0:
                        status_text.text("Procesando nuevos miembros...")
                        
                        for i in range(0, len(nuevos), batch_size):
                            batch = nuevos[i:i + batch_size]
                            miembros_batch = []
                            info_batch = []
                            saldos_batch = []
                            
                            for _, row in batch.iterrows():
                                # Validar campos obligatorios
                                if None in [row.get('ID_MIEMBRO'), row.get('RAZON_SOCIAL'), row.get('RIF')]:
                                    raise ValueError(f"Campos obligatorios faltantes en fila {i}")

                                # Datos para Miembro - Asegurando incluir ULTIMO_MES
                                miembro_data = {
                                    'ID_MIEMBRO': int(row.get('ID_MIEMBRO')),
                                    'RAZON_SOCIAL': row.get('RAZON_SOCIAL'),
                                    'RIF': row.get('RIF'),
                                    'ULTIMO_MES': row.get('ULTIMO_MES'),  # Ahora sí se incluye correctamente
                                    'SALDO': float(row.get('SALDO', 0))
                                }
                                
                                print(f"Miembro data: {miembro_data}")  # Debug adicional
                                miembros_batch.append(miembro_data)
                                
                                info_data = {
                                    'ID_MIEMBRO': int(row.get('ID_MIEMBRO')),
                                    'NUM_TELEFONO': row.get('NUM_TELEFONO'),
                                    'REPRESENTANTE': row.get('REPRESENTANTE'),
                                    'CI_REPRESENTANTE': row.get('CI_REPRESENTANTE'),
                                    'CORREO': row.get('CORREO'),
                                    'DIRECCION': row.get('DIRECCION'),
                                    'HACIENDA': row.get('HACIENDA')
                                }
                                info_batch.append(info_data)
                            
                            
                            # Insertar lote - VERIFICACIÓN ADICIONAL
                            try:
                                session.bulk_insert_mappings(Miembro, miembros_batch)
                                session.bulk_insert_mappings(InformacionMiembro, info_batch)
                                session.commit()
                            except Exception as e:
                                session.rollback()
                                st.error(f"Error en lote {i//batch_size + 1}: {str(e)}")
                                # Debug adicional
                                st.error(f"Datos problemáticos: {miembros_batch}")
                                return
                            
                            progress = (i + len(batch)) / total_ops
                            progress_bar.progress(progress)
                    
                    # 2. Procesar EXISTENTES registros (ACTUALIZACIÓN)
                    if len(existentes) > 0:
                        status_text.text("Actualizando miembros existentes...")
                        
                        for i in range(0, len(existentes), batch_size):
                            batch = existentes[i:i + batch_size]
                            
                            for _, row in batch.iterrows():
                                # Verificar solo campo obligatorio
                                if row.get('ID_MIEMBRO') is None:
                                    raise ValueError(f"ID_MIEMBRO faltante en fila {i}")
                                
                                try:
                                    id_miembro = int(row['ID_MIEMBRO'])
                                    actualizaciones_realizadas = False
                                    
                                    # Verificar si hay campos para actualizar en Miembro
                                    campos_miembro = ['RAZON_SOCIAL', 'RIF', 'ULTIMO_MES', 'SALDO']
                                    tiene_campos_miembro = any(row.get(campo) is not None for campo in campos_miembro if campo in row)
                                    
                                    # Actualizar tabla Miembro solo si hay campos relevantes
                                    if tiene_campos_miembro:
                                        miembro = session.query(Miembro).get(id_miembro)
                                        if miembro:
                                            if 'RAZON_SOCIAL' in row and row['RAZON_SOCIAL'] is not None:
                                                miembro.RAZON_SOCIAL = row['RAZON_SOCIAL']
                                            if 'RIF' in row and row['RIF'] is not None:
                                                miembro.RIF = row['RIF']
                                            if 'ULTIMO_MES' in row and row['ULTIMO_MES'] is not None:
                                                miembro.ULTIMO_MES = row['ULTIMO_MES']
                                            if 'SALDO' in row and row['SALDO'] is not None:
                                                miembro.SALDO = float(row['SALDO'])
                                            actualizaciones_realizadas = True
                                    
                                    # Verificar si hay campos para actualizar en InformacionMiembro
                                    campos_info = ['NUM_TELEFONO', 'REPRESENTANTE', 'CI_REPRESENTANTE', 'CORREO', 'DIRECCION', 'HACIENDA']
                                    tiene_campos_info = any(row.get(campo) is not None for campo in campos_info if campo in row)
                                    
                                    # Actualizar tabla InformacionMiembro solo si hay campos relevantes
                                    if tiene_campos_info:
                                        info = session.query(InformacionMiembro).filter_by(ID_MIEMBRO=id_miembro).first()
                                        if info:
                                            if 'NUM_TELEFONO' in row and row['NUM_TELEFONO'] is not None:
                                                info.NUM_TELEFONO = row['NUM_TELEFONO']
                                            if 'REPRESENTANTE' in row and row['REPRESENTANTE'] is not None:
                                                info.REPRESENTANTE = row['REPRESENTANTE']
                                            if 'CI_REPRESENTANTE' in row and row['CI_REPRESENTANTE'] is not None:
                                                info.CI_REPRESENTANTE = row['CI_REPRESENTANTE']
                                            if 'CORREO' in row and row['CORREO'] is not None:
                                                info.CORREO = row['CORREO']
                                            if 'DIRECCION' in row and row['DIRECCION'] is not None:
                                                info.DIRECCION = row['DIRECCION']
                                            if 'HACIENDA' in row and row['HACIENDA'] is not None:
                                                info.HACIENDA = row['HACIENDA']
                                            actualizaciones_realizadas = True
                                    
                                    # Solo hacer commit si hubo actualizaciones reales
                                    if actualizaciones_realizadas:
                                        session.commit()
                                    
                                except Exception as e:
                                    session.rollback()
                                    st.warning(f"Advertencia: No se pudo actualizar ID {row.get('ID_MIEMBRO')}. Error: {str(e)}")
                                    continue  # Continuar con el siguiente registro
                            
                            progress = (len(nuevos) + i + len(batch)) / total_ops
                            progress_bar.progress(progress)
                    
                    st.success("¡Proceso completado con éxito!")
                    progress_bar.empty()
                    status_text.empty()
                    time.sleep(5)
                    st.rerun()
                    
            except Exception as e:
                session.rollback()
                st.error(f"Error durante el procesamiento: {str(e)}")
                time.sleep(5)
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
        st.error(f'Se ha producido un error al tratar de eliminar el registro. Error: {e}')
        return False
    finally:
        session.close()

@st.dialog('Información Adicional', width="large")
def informacion_miembro(num_indice: int, dataframe: pd.DataFrame):
    info = dataframe.loc[num_indice]
    info = info.iloc

    if st.toggle('**Habilitar Edición**', False):
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
        # Iniciar una transacción única para todas las operaciones
        with session.begin():
            # 1. Eliminar registros relacionados primero (por restricciones de clave foránea)
            session.query(Saldo).filter(Saldo.ID_MIEMBRO == id_miembro).delete()
            session.query(InformacionMiembro).filter(InformacionMiembro.ID_MIEMBRO == id_miembro).delete()
            
            # 2. Finalmente eliminar el miembro principal
            deleted_count = session.query(Miembro).filter(Miembro.ID_MIEMBRO == id_miembro).delete()
            
            # Verificar si realmente se eliminó algún registro
            if deleted_count == 0:
                st.toast(f'No se encontró el miembro con ID {id_miembro} para eliminar')
                return False
            
        st.toast(f'Miembro con ID {id_miembro} eliminado exitosamente.')
        return True
        
    except Exception as e:
        session.rollback()
        st.toast(f'Error al eliminar el miembro con ID {id_miembro}. Error: {e}')
        return False
    # No necesitamos finally con session.close() si usas @st.cache_resource para la sesión

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

# Se obtienen valores de las tablas miembros e informacion_miembros mediante un join
miembros_completo = obtener_df_join(Miembro, InformacionMiembro)
miembros_base = obtener_df(Miembro)


# SECCIONES DE LA PAGINA
header = st.container()
datos = st.container()
tabla = st.container()
botones = st.container()

# HEADER DE LA PAGINA
with header:
    col0, col1, col3, col5 = st.columns([6, 1, 1, 1], vertical_alignment='center')
    with col0:
        st.title('Miembros')
        st.caption('Esta pagina contiene información reelevante con respecto a los miembros de la organización.')
    with col1:
        add = st.button(':material/add: Añadir', use_container_width=True, type='primary')
        if add:
            añadir_miembro()
    with col3:
        cobrar = st.button(':material/phone: Cobrar', use_container_width=True, type='secondary')
        if cobrar:
            cobranza(miembros_completo)
    with col5:
        pdf_buffer = generar_informe_pdf_miembros(miembros_completo, ["ESTADO", "SALDO"])
        st.download_button(
            label=":material/download: Informe",
            data=pdf_buffer,
            file_name=f"informe_miembros {datetime.date.today()}.pdf",
            mime="application/pdf"
        )

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
        col01, col02, col03 = st.columns([3, 2, 3])
        with col02:
            st.warning('No hay datos para mostrar')
        seleccion = []
    elif not miembros_base.empty:
        # Selección de las columnas a mostrar
        miembros = miembros_base[["ID_MIEMBRO", "RAZON_SOCIAL", "RIF", "ULTIMO_MES", "SALDO", "ESTADO"]].sort_values(by="SALDO", ascending=False)
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
                st.session_state.ids_a_eliminar = [miembros.loc[i, "ID_MIEMBRO"] for i in seleccion]
                confirmar_eliminacion()
    with col3:
        if len(seleccion) == 1:
            more = st.button(':material/post_add: Ver/Editar', use_container_width=True, type='secondary')
            if more:
                id_miembro = miembros.loc[seleccion[0], 'ID_MIEMBRO']
                informacion_miembro(id_miembro, miembros_completo)
