import streamlit as st
import pandas as pd
from db.conexion import session, Egreso, obtener_df_join, Miembro
from datetime import date, datetime
from sqlalchemy.orm import aliased
from sqlalchemy import select

if 'edit' not in st.session_state:
    st.session_state.edit = True

if 'notificacion' in st.session_state:
    st.toast(st.session_state.notificacion)
    del st.session_state.notificacion

if 'selected_movimiento' not in st.session_state:
    st.session_state.selected_movimiento = None


# Realizar el join manualmente y seleccionar las columnas necesarias
query = (
    select(
        Egreso.ID_EGRESO,
        Egreso.FECHA,
        Egreso.CUENTA_CONTABLE,
        Egreso.TIPO_OPERACION,
        Egreso.TITULAR,
        Egreso.METODO_PAGO,
        Egreso.DETALLE,
        Egreso.MONTO,
        Egreso.MONTO_DIVISAS,
        Egreso.BASE_IMPONIBLE,
        Egreso.IVA,
        Egreso.REFERENCIA,
        Egreso.NUMERO_FACTURA,
        Egreso.NUMERO_CONTROL,
        Egreso.BENEFICIARIO
    )
)

# Ejecutar la consulta y obtener los resultados como una lista de tuplas
resultados = session.execute(query).fetchall()

# Convertir los resultados en un DataFrame de pandas
movimientos = pd.DataFrame(resultados, columns=[
    "ID_EGRESO", "FECHA", "CUENTA_CONTABLE", "TIPO_OPERACION", "TITULAR",
    "METODO_PAGO", "DETALLE", "MONTO", "MONTO_DIVISAS", "BASE_IMPONIBLE",
    "IVA", "REFERENCIA", "NUMERO_FACTURA", "NUMERO_CONTROL", "BENEFICIARIO"
])

# Convertir la columna FECHA a datetime, manejando errores
movimientos['FECHA'] = pd.to_datetime(movimientos['FECHA'], errors='coerce').dt.date

# Verificar si hay valores nulos en la columna FECHA
if movimientos['FECHA'].isna().any():
    st.error("Se encontraron valores no válidos en la columna FECHA. Verifica los datos.")
    st.write(movimientos[movimientos['FECHA'].isna()])

@st.dialog("Registro de Egreso", width="large")
def agregar_movimiento():
    st.header('Registrar Nuevo Egreso')
    col13, col14 = st.columns(2)

    with col13:
        fecha = st.date_input('Fecha', value=date.today())
        cuenta_contable = st.text_input('Cuenta Contable')
        beneficiario = st.text_input('Beneficiario')
        metodo_pago = st.selectbox('Método de Pago', ['Pago Movil/Transferencia', 'Zelle', 'Efectivo Divisas'])
        detalle = st.text_input('Detalle')
        numero_control = st.text_input('Número Control')
    with col14:
        monto = st.number_input('Monto', min_value=0.0, step=0.01, format="%.2f")
        monto_divisas = st.number_input('Monto Divisas', min_value=0.0, step=0.01, format="%.2f")
        base_imponible = st.number_input('Base Imponible', min_value=0.0, step=0.01, format="%.2f")
        iva = st.number_input('IVA', min_value=0.0, step=0.01, format="%.2f")
        referencia = st.text_input('Referencia')
        numero_factura = st.text_input('Número Factura')

    col10, col11, col12 = st.columns([1, 1, 4], gap='small')
    with col10:
        save_changes = st.button(':material/save: Guardar')
        if save_changes:
            # Diccionario para almacenar los campos a insertar en Egreso
            campos_valores_movimiento = {
                "FECHA": fecha,
                "TIPO_OPERACION" : 'Gastos',
                "CUENTA_CONTABLE": cuenta_contable,
                "BENEFICIARIO": beneficiario,
                "METODO_PAGO": metodo_pago,
                "DETALLE": detalle,
                "MONTO": monto,
                "MONTO_DIVISAS": monto_divisas,
                "BASE_IMPONIBLE": base_imponible,
                "IVA": iva,
                "REFERENCIA": referencia,
                "NUMERO_FACTURA": numero_factura,
                "NUMERO_CONTROL": numero_control
            }

            # Insertar nuevo egreso
            nuevo_movimiento = Egreso(**campos_valores_movimiento)
            try:
                session.add(nuevo_movimiento)
                session.commit()
                st.session_state.notificacion = 'Egreso registrado exitosamente'
                st.rerun()
            except Exception as e:
                session.rollback()
                st.session_state.notificacion = f'Error al insertar el egreso: {e}'
                st.rerun()

@st.dialog("Eliminar Egreso", width="large")
def eliminar_movimiento():
    st.warning('¿Estás seguro de que quieres eliminar los siguientes egresos?')
    ids_egreso = [int(id_egreso) for id_egreso in st.session_state.selected_movimiento]
    for id in ids_egreso:
        st.write(f'ID Egreso: {id}')

    col0, col1, col2, col3 = st.columns([2, 1.3, 1.3, 2], gap='medium')
    with col0:
        if st.button('Confirmar', use_container_width=True):
            for id in ids_egreso:
                try:
                    session.query(Egreso).filter(Egreso.ID_EGRESO == id).delete()
                    session.commit()
                except Exception as e:
                    session.rollback()
                    st.session_state.notificacion = f'Error al eliminar el egreso: {e}'
                    st.rerun()
                    return
            st.session_state.notificacion = 'Egreso(s) eliminado(s) exitosamente'
            st.rerun()

@st.dialog("Editar Egreso", width="large")
def editar_movimiento():
    movimiento = st.session_state.selected_movimiento
    if movimiento is None:
        st.error('No se ha seleccionado ningún egreso para editar.')
        return

    col13, col14 = st.columns(2)
    with col13:
        fecha = st.date_input('Fecha', value=movimiento['FECHA'], disabled=st.session_state.edit)
        cuenta_contable = st.text_input('Cuenta Contable', value=movimiento['CUENTA_CONTABLE'], disabled=st.session_state.edit)
        beneficiario = st.text_input('Beneficiario', value=movimiento['BENEFICIARIO'], disabled=st.session_state.edit)
        metodo_pago = st.text_input('Método de Pago', value=movimiento['METODO_PAGO'], disabled=st.session_state.edit)
        detalle = st.text_input('Detalle', value=movimiento['DETALLE'], disabled=st.session_state.edit)
    with col14:
        monto = st.number_input(
            'Monto',
            min_value=0.0,
            step=0.01,
            value=float(movimiento['MONTO']),
            format="%.2f",
            disabled=st.session_state.edit
        )
        monto_divisas = st.number_input(
            'Monto Divisas',
            min_value=0.0,
            step=0.01,
            value=float(movimiento['MONTO_DIVISAS']),
            format="%.2f",
            disabled=st.session_state.edit
        )
        base_imponible = st.number_input(
            'Base Imponible',
            min_value=0.0,
            step=0.01,
            value=float(movimiento['BASE_IMPONIBLE']),
            format="%.2f",
            disabled=st.session_state.edit
        )
        iva = st.number_input(
            'IVA',
            min_value=0.0,
            step=0.01,
            value=float(movimiento['IVA']),
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
            campos_valores_movimiento = {
                "FECHA": fecha,
                "CUENTA_CONTABLE": cuenta_contable,
                "BENEFICIARIO": beneficiario,
                "METODO_PAGO": metodo_pago,
                "DETALLE": detalle,
                "MONTO": monto,
                "MONTO_DIVISAS": monto_divisas,
                "BASE_IMPONIBLE": base_imponible,
                "IVA": iva,
                "REFERENCIA": referencia,
                "NUMERO_FACTURA": numero_factura,
                "NUMERO_CONTROL": numero_control
            }

            try:
                session.query(Egreso).filter(Egreso.ID_EGRESO == movimiento['ID_EGRESO']).update(campos_valores_movimiento)
                session.commit()
                st.session_state.notificacion = 'Egreso actualizado exitosamente'
                st.rerun()
            except Exception as e:
                session.rollback()
                st.session_state.notificacion = f'Error al actualizar el egreso: {e}'
                st.rerun()

# Secciones de la página
header = st.container()
tabla = st.container()
botones = st.container()

with header:
    col1, col0, col2 = st.columns([4, 1, 1], vertical_alignment='center')
    with col1:
        st.title('Gestión de Egresos')
    with col2:
        add_mov = st.button(':material/add: Nuevo', type='primary')
        if add_mov:
            agregar_movimiento()
    col7, col8 = st.columns([1,5])
    with col7:
        filtro = st.date_input(
            'Filtrar por fecha:',
            value=(datetime.now().replace(day=1).date(), datetime.now().date()),
            format='DD/MM/YYYY')

with tabla:
    if movimientos.empty:
        st.divider()
        col4, col5, col6 = st.columns([2.4,1.2,2.4])
        with col5:
            st.warning('No hay gastos registrados')
            seleccion = []
    else:
        if isinstance(filtro, tuple) and len(filtro) == 2:
            fecha_inicio, fecha_fin = filtro
            movimientos = movimientos[
                (movimientos['FECHA'] >= fecha_inicio) & (movimientos['FECHA'] <= fecha_fin)
            ]

        movimientos_filtrado = movimientos[[
            "ID_EGRESO", "FECHA", "TIPO_OPERACION", "TITULAR", "BENEFICIARIO",
            "METODO_PAGO", "DETALLE", "MONTO", "MONTO_DIVISAS", "BASE_IMPONIBLE",
            "IVA", "REFERENCIA", "NUMERO_FACTURA", "NUMERO_CONTROL"
        ]]
        conf_col = {
            'ID_EGRESO': st.column_config.NumberColumn('ID'),
            "FECHA": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "TIPO_OPERACION": st.column_config.TextColumn("Tipo de Operación"),
            "TITULAR": st.column_config.TextColumn("Titular"),
            "BENEFICIARIO": st.column_config.TextColumn("Beneficiario"),
            "METODO_PAGO": st.column_config.TextColumn("Método de Pago"),
            "DETALLE": st.column_config.TextColumn("Detalle"),
            "MONTO": st.column_config.NumberColumn("Bs. ", format="Bs. %.2f"),
            "MONTO_DIVISAS": st.column_config.NumberColumn("$", format="$ %.2f"),
            "BASE_IMPONIBLE": st.column_config.NumberColumn("Base Imponible", format="Bs. %.2f"),
            "IVA": st.column_config.NumberColumn("IVA", format="Bs. %.2f"),
            "REFERENCIA": st.column_config.TextColumn("Referencia"),
            "NUMERO_FACTURA": st.column_config.TextColumn("N° Factura"),
            "NUMERO_CONTROL": st.column_config.TextColumn("N° Control"),
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
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if len(seleccion) >= 1:
            delete_movimiento = st.button(':material/delete: Eliminar Movimiento', type='primary')
            if delete_movimiento and seleccion:
                st.session_state.selected_movimiento = [movimientos_filtrado.iloc[(seleccion)]].to_dict()
                eliminar_movimiento()
    with col2:
        if len(seleccion) == 1:
            edit_movimiento = st.button(':material/edit: Ver/Editar', type='primary')
            if edit_movimiento and seleccion:
                st.session_state.selected_movimiento = movimientos.iloc[seleccion[0]].to_dict()
                editar_movimiento()

