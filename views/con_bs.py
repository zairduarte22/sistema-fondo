import streamlit as st
from db.conexion import session, Miembro, obtener_df, ConciliacionBS
from datetime import date, datetime
import pandas as pd

if 'edit' not in st.session_state:
    st.session_state.edit = True

if 'notificacion' in st.session_state:
    st.toast(st.session_state.notificacion)
    del st.session_state.notificacion

if 'active_number' not in st.session_state:
    st.session_state.active_number = False

if 'selected_factura' not in st.session_state:
    st.session_state.selected_factura = None

if 'selected_movimiento' not in st.session_state:
    st.session_state.selected_movimiento = None


# Obtener los datos de la tabla CONCILIACION_BS
movimientos_df = obtener_df(ConciliacionBS)
movimientos = movimientos_df.sort_values(by='FECHA', ascending=False)
# Obtener los datos de la tabla Miembro
miembros = obtener_df(Miembro)


@st.dialog("Registro de Movimiento", width="large")
def agregar_movimiento():
    st.header('Registrar Nuevo Movimiento')
    col13, col14 = st.columns(2)

    with col13:
        fecha = st.date_input('Fecha', value=date.today(), format='DD/MM/YYYY')
        cuenta_contable = st.text_input('Cuenta Contable')
        tipo_operacion = st.selectbox('Tipo de Operación', ['TRANSF', 'COM'])
        referencia = st.text_input('Referencia')
    with col14:
        beneficiario = st.text_input('Beneficiario')
        descripcion = st.text_input('Descripción')
        ingreso = st.number_input('Ingreso', min_value=0.0, step=0.01, format="%.2f")
        egreso = st.number_input('Egreso', min_value=0.0, step=0.01, format="%.2f")

    col10, col11, col12 = st.columns([1, 1, 4], gap='small')
    with col10:
        save_changes = st.button(':material/save: Guardar')
        if save_changes:
            # Diccionario para almacenar los campos a insertar en ConciliacionBS
            campos_valores_movimiento = {
                "FECHA": fecha,
                "CUENTA_CONTABLE": cuenta_contable,
                "TIPO_OPERACION": tipo_operacion,
                "REFERENCIA": referencia,
                "BENEFICIARIO": beneficiario,
                "DESCRIPCION": descripcion,
                "INGRESO": ingreso,
                "EGRESO": egreso
            }

            # Insertar nuevo movimiento
            nuevo_movimiento = ConciliacionBS(**campos_valores_movimiento)
            try:
                session.add(nuevo_movimiento)
                session.commit()
                st.session_state.notificacion = 'Movimiento registrado exitosamente'
                st.rerun()
            except Exception as e:
                session.rollback()
                st.session_state.notificacion = f'Error al insertar el movimiento: {e}'
                st.rerun()

@st.dialog("Editar Movimiento", width="large")
def editar_movimiento():
    movimiento = st.session_state.selected_movimiento
    if movimiento is None:
        st.error('No se ha seleccionado ningún movimiento para editar.')
        return

    col13, col14 = st.columns(2)
    with col13:
        fecha = st.date_input('Fecha', value=movimiento['FECHA'], disabled=st.session_state.edit)
        cuenta_contable = st.text_input('Cuenta Contable', value=movimiento['CUENTA_CONTABLE'], disabled=st.session_state.edit)
        tipo_operacion = st.selectbox('Tipo de Operación',['TRANSF', 'COM'] , index=['TRANSF', 'COM'].index(movimiento['TIPO_OPERACION']), disabled=st.session_state.edit)
        referencia = st.text_input('Referencia', value=movimiento['REFERENCIA'], disabled=st.session_state.edit)
    with col14:
        beneficiario = st.text_input('Beneficiario', value=movimiento['BENEFICIARIO'], disabled=st.session_state.edit)
        descripcion = st.text_input('Descripción', value=movimiento['DESCRIPCION'], disabled=st.session_state.edit)
        ingreso = st.number_input('Ingreso', min_value=0.0, step=0.01, value=movimiento['INGRESO'], format="%.2f", disabled=st.session_state.edit)
        egreso = st.number_input('Egreso', min_value=0.0, step=0.01, value=movimiento['EGRESO'], format="%.2f", disabled=st.session_state.edit)

    col10, col11, col12 = st.columns([1, 1, 4], gap='small')
    with col10:
        def toggle_edit():
            st.session_state.edit = not st.session_state.edit
        st.button(':material/edit: Editar', on_click=toggle_edit, use_container_width=True)

    with col11:
        save_changes = st.button(':material/save: Guardar', use_container_width=True)
        if save_changes:
            # Diccionario para almacenar los campos a actualizar en ConciliacionBS
            campos_valores_movimiento = {
                "FECHA": fecha,
                "CUENTA_CONTABLE": cuenta_contable,
                "TIPO_OPERACION": tipo_operacion,
                "REFERENCIA": referencia,
                "BENEFICIARIO": beneficiario,
                "DESCRIPCION": descripcion,
                "INGRESO": ingreso,
                "EGRESO": egreso
            }
            

            # Actualizar movimiento
            try:
                session.query(ConciliacionBS).filter(ConciliacionBS.ID_MOVIMIENTO == movimiento['ID_MOVIMIENTO']).update(campos_valores_movimiento)
                session.commit()
                st.session_state.notificacion = 'Movimiento actualizado exitosamente'
                st.rerun()
            except Exception as e:
                session.rollback()
                st.session_state.notificacion = f'Error al actualizar el movimiento: {e}'
                st.rerun()

@st.dialog("Eliminar Movimiento", width="large")
def eliminar_movimiento():
    st.warning('¿Estás seguro de que quieres eliminar los siguientes movimientos?')
    for movimiento in st.session_state.selected_movimiento:
        st.write(f'ID Movimiento: {movimiento["ID_MOVIMIENTO"]}')

    col0, col1, col2, col3 = st.columns([2, 1.3, 1.3, 2], gap='medium')
    with col0:
        if st.button('Confirmar', use_container_width=True):
            for movimiento in st.session_state.selected_movimiento:
                try:
                    session.query(ConciliacionBS).filter(ConciliacionBS.ID_MOVIMIENTO == movimiento["ID_MOVIMIENTO"]).delete()
                    session.commit()
                except Exception as e:
                    session.rollback()
                    st.session_state.notificacion = f'Error al eliminar el movimiento: {e}'
                    st.rerun()
                    return
            st.session_state.notificacion = 'Movimiento(s) eliminado(s) exitosamente'
            st.rerun()

@st.dialog("Carga Masiva de Movimientos", width="large")
def cargar_movimientos_csv():
    st.header("Carga Masiva de Movimientos desde CSV")
    st.markdown(
        "Descarga el formato, complétalo y súbelo para registrar varios movimientos de una vez. "
        "**El campo FECHA debe estar en formato DD/MM/YYYY.**"
    )

    # Botón para descargar el formato CSV
    formato = pd.DataFrame(columns=[
        "FECHA", "CUENTA_CONTABLE", "TIPO_OPERACION", "REFERENCIA",
        "BENEFICIARIO", "DESCRIPCION", "INGRESO", "EGRESO"
    ])
    csv_formato = formato.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Descargar Formato CSV",
        data=csv_formato,
        file_name="formato_movimientos.csv",
        mime="text/csv"
    )

    # Subida de archivo CSV
    csv_file = st.file_uploader("Selecciona el archivo CSV", type=["csv"], key="csv_movimientos_dialog")
    if csv_file is not None:
        try:
            df = pd.read_csv(csv_file)
            required_cols = {"FECHA", "CUENTA_CONTABLE", "TIPO_OPERACION", "REFERENCIA", "BENEFICIARIO", "DESCRIPCION", "INGRESO", "EGRESO"}
            if not required_cols.issubset(df.columns):
                st.error(f"El CSV debe contener las columnas: {', '.join(required_cols)}")
            else:
                # Convertir FECHA al formato correcto
                try:
                    df["FECHA"] = pd.to_datetime(df["FECHA"], format="%d/%m/%Y").dt.date
                    df["INGRESO"] = df["INGRESO"].replace('.', '', regex=True)
                    df["INGRESO"] = df["INGRESO"].replace(',', '.', regex=True)
                    df["INGRESO"] = pd.to_numeric(df["INGRESO"], errors='coerce').fillna(0.0)
                    df["EGRESO"] = df["EGRESO"].replace('.', '', regex=True)
                    df["EGRESO"] = df["EGRESO"].replace(',', '.', regex=True)
                    df["EGRESO"] = pd.to_numeric(df["EGRESO"], errors='coerce').fillna(0.0)
                except Exception:
                    st.error("Error al procesar las fechas o los montos. Asegúrate de que el formato de fecha sea DD/MM/YYYY y los montos sean numéricos.")
                    return
                nuevos_movimientos = [
                    ConciliacionBS(
                        FECHA=row["FECHA"],
                        CUENTA_CONTABLE=row["CUENTA_CONTABLE"],
                        TIPO_OPERACION=row["TIPO_OPERACION"],
                        REFERENCIA=row["REFERENCIA"],
                        BENEFICIARIO=row["BENEFICIARIO"],
                        DESCRIPCION=row["DESCRIPCION"],
                        INGRESO=row["INGRESO"],
                        EGRESO=row["EGRESO"]
                    )
                    for _, row in df.iterrows()
                ]
                session.add_all(nuevos_movimientos)
                session.commit()
                st.success(f"Se han cargado {len(nuevos_movimientos)} movimientos desde el CSV.")
                st.rerun()
        except Exception as e:
            session.rollback()
            st.error(f"Error al cargar el archivo CSV: {e}")

# Secciones de la página
header = st.container()
tabla = st.container()
botones = st.container()

with header:
    st.title('Conciliacion Bancaria: BNC')
    col1, col0, col2, col3 = st.columns([2, 4, 1, 2], vertical_alignment='center')
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
    with col3:
        btn_carga_csv = st.button(':material/upload: Carga Masiva', type='primary')
        if btn_carga_csv:
            cargar_movimientos_csv()

with tabla:
    if isinstance(filtro, tuple) and len(filtro) == 2:
            fecha_inicio, fecha_fin = filtro
            movimientos = movimientos[
                (movimientos['FECHA'] >= fecha_inicio) & (movimientos['FECHA'] <= fecha_fin)
            ]

    if movimientos.empty:
        st.divider()
        col4, col5, col6 = st.columns([2.4,1.2,2.4])
        with col5:
            st.warning('No hay movimientos registrados')
            seleccion = []
    else:
        # Configurar las columnas a mostrar
        movimientos_filtrado = movimientos[[
            "FECHA", "CUENTA_CONTABLE", "TIPO_OPERACION", "REFERENCIA",
            "BENEFICIARIO", "DESCRIPCION", "INGRESO", "EGRESO"
        ]]
        conf_col = {
            "FECHA": st.column_config.DateColumn("Fecha", format="DD-MM-YYYY"),
            "CUENTA_CONTABLE": st.column_config.TextColumn("Cuenta Contable"),
            "TIPO_OPERACION": st.column_config.TextColumn("Tipo de Operación"),
            "REFERENCIA": st.column_config.TextColumn("Referencia"),
            "BENEFICIARIO": st.column_config.TextColumn("Beneficiario"),
            "DESCRIPCION": st.column_config.TextColumn("Descripción"),
            "INGRESO": st.column_config.NumberColumn("Ingreso", format="Bs. %.2f"),
            "EGRESO": st.column_config.NumberColumn("Egreso", format="Bs. %.2f"),
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
            delete_movimiento = st.button(':material/delete: Eliminar', type='primary')
            if delete_movimiento and seleccion:
                st.session_state.selected_movimiento = movimientos.iloc[seleccion].to_dict('records')
                eliminar_movimiento()
    with col2:
        if len(seleccion) == 1:
            edit_movimiento = st.button(':material/edit: Ver/Editar', type='primary')
            if edit_movimiento and seleccion:
                st.session_state.selected_movimiento = movimientos.iloc[seleccion[0]].to_dict()
                editar_movimiento()


