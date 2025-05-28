import streamlit as st
from db.conexion import session, FactCuota, Miembro, InformacionMiembro, obtener_df, obtener_df_join, Saldo
from datetime import date, datetime
from utils.bcv_tasa import tasa_bs
import pandas as pd
from utils.print_invoice import invoice_model, setup_printing
from utils.informes_pdf import generar_factura_pdf, generar_reporte_con_formato_imagen



if 'edit' not in st.session_state:
    st.session_state.edit = True

if 'notificacion' in st.session_state:
    st.toast(st.session_state.notificacion)
    del st.session_state.notificacion

if 'active_number' not in st.session_state:
    st.session_state.active_number = False

if 'selected_factura' not in st.session_state:
    st.session_state.selected_factura = None

# Obtener los datos de la tabla FACT_CUOTAS
facturas = obtener_df(FactCuota)
miembros = obtener_df(Miembro)
miembros_completo = obtener_df_join(Miembro, InformacionMiembro)


@st.dialog("Agregar Nueva Factura", width="large")
def agregar_factura():
    col13, col14 = st.columns([5,3])

    with col13:
        if st.toggle('Modificar Numeración de Facturas', value=False):
            st.session_state.active_number = False
        else:
            st.session_state.active_number = True      

    with col14:
        st.write(f'Tasa: Bs. {tasa_bs()}')   

    col6, col7 = st.columns([2.5, 1], vertical_alignment='center')
    with col6:
        # Crear un selectbox con las razones sociales de los miembros
        fecha = st.date_input('Fecha', value=date.today(), format="DD-MM-YYYY")
        razon_social = st.selectbox('Razón Social', miembros['RAZON_SOCIAL'], index=None, placeholder='Seleccione una opción')
    with col7:
        z = lambda x: float(miembros[miembros['RAZON_SOCIAL'] == razon_social]['SALDO']) if x is not None else 0.00
        saldo = z(razon_social)
        y = lambda x: x*-1 if x < 0.00 else 0.00
        monto_divisas = st.number_input('Monto ($)', value=y(saldo))
        x = lambda x: 0.00 if x == 0.00 else x*tasa_bs()
        monto_bs = st.number_input('Monto (Bs.)', format="%.2f", value=x(monto_divisas))

    col8, col9 = st.columns([1, 1])
    with col8:
        metodo_pago = st.selectbox('Método de Pago', ['Pago Movil/Transferencia', 'Zelle', 'Efectivo Divisas'])
        mensualidades = st.text_input('Mensualidades')
        referencia = st.text_input('Referencia')
    with col9:
        fact_ugavi = st.number_input('Factura UGAVI', format="%d", disabled=st.session_state.active_number, value=0)
        fact_fondo = st.number_input('Factura Fondo', format="%d", disabled=st.session_state.active_number, value=0)
        ultimo_mes = miembros[miembros['RAZON_SOCIAL'].isin([razon_social])]['ULTIMO_MES'].values
        if len(ultimo_mes) > 0:
            ultimo_mes = ultimo_mes[0]
        else:
            ultimo_mes = 'N/A'
        text = st.text(f'Ultimo Mes: {ultimo_mes}')
    colx, colz = st.columns(2)
    with colx:
        descuento = st.checkbox('Descuento por Pronto Pago', value=False, key='descuento_anticipado')
    with colz:
        with st.popover("Cant. Meses", disable = descuento):
            meses = st.number_input("Ingrese la cantidad de meses...",step = 1)

    col10, col11, col12 = st.columns([1, 1, 4], gap='small')
    with col10:
        save_changes = st.button(':material/save: Guardar')
        if save_changes:
            # Obtener el ID_MIEMBRO correspondiente a la razón social seleccionada
            id_miembro = miembros.loc[miembros['RAZON_SOCIAL'] == razon_social, 'ID_MIEMBRO'].values[0]
            
            # Diccionario para almacenar los campos a insertar en FactCuota
            if st.session_state.active_number:
                campos_valores_factura = {
                    "ID_MIEMBRO": id_miembro,
                    "FECHA": fecha,
                    "MONTO_BS": monto_bs,
                    "MONTO_DIVISAS": monto_divisas,
                    "METODO_PAGO": metodo_pago,
                    "MENSUALIDADES": mensualidades,
                    "REFERENCIA": referencia}
            else:
                campos_valores_factura = {
                                    "ID_MIEMBRO": id_miembro,
                                    "FECHA": fecha,
                                    "MONTO_BS": monto_bs,
                                    "MONTO_DIVISAS": monto_divisas,
                                    "METODO_PAGO": metodo_pago,
                                    "FACT_UGAVI": fact_ugavi,
                                    "FACT_FONDO": fact_fondo,
                                    "MENSUALIDADES": mensualidades,
                                    "REFERENCIA": referencia
                }
            
            saldo_descuento = {
                        "ID_MIEMBRO": id_miembro,
                        "DESCRIPCION": 'Descuento Por Pronto Pago',
                        "MONTO": 5}
            
            # Insertar nueva factura
            nueva_factura = FactCuota(**campos_valores_factura)
            nuevo_descuento = Saldo(**saldo_descuento)
            try:
                session.add(nueva_factura)
                if descuento:
                    session.add(nuevo_descuento)
                session.commit()
                st.session_state.notificacion = 'Factura registrada exitosamente'
                st.rerun()
            except Exception as e:
                session.rollback()
                mensaje = f'Error al insertar la nueva factura. Error: {e}'
                st.session_state.notificacion = mensaje
                st.rerun()
        with col11:
            if st.button(':material/print: Imprimir'):
                setup_printing(html_content=invoice_model(
                    date=fecha, 
                    name=razon_social, 
                    adress=miembros_completo.loc[miembros_completo['RAZON_SOCIAL'] == razon_social, 'DIRECCION'].values[0], 
                    id=miembros.loc[miembros['RAZON_SOCIAL'] == razon_social, 'RIF'].values[0], 
                    month=mensualidades, 
                    monto=monto_bs))
                

@st.dialog('Editar Factura', width="large")
def editar_factura():
    factura = st.session_state.selected_factura
    if factura is None:
        st.error('No se ha seleccionado ninguna factura para editar.')
        return

    col6, col7 = st.columns([2.5, 1], vertical_alignment='center')
    with col6:
        # Crear un selectbox con las razones sociales de los miembros
        fecha = st.date_input('Fecha', value=factura['FECHA'], format='DD/MM/YYYY', disabled=st.session_state.edit)
        razon_social = st.selectbox('Razón Social', miembros['RAZON_SOCIAL'], placeholder='Seleccione una opción', index=miembros['RAZON_SOCIAL'].tolist().index(factura['ID_MIEMBRO']), disabled=st.session_state.edit)
    with col7:
        monto_bs = st.number_input('Monto en Bolívares', format="%.2f", value=factura['MONTO_BS'], disabled=st.session_state.edit)
        monto_divisas = st.number_input('Monto en Divisas', format="%.2f", value=factura['MONTO_DIVISAS'], disabled=st.session_state.edit)

    col8, col9 = st.columns([1, 1])
    with col8:
        metodo_pago = st.selectbox('Método de Pago', ['Pago Movil/Transferencia', 'Zelle', 'Efectivo Divisas'], index=['Pago Movil/Transferencia', 'Zelle', 'Efectivo Divisas'].index(factura['METODO_PAGO']), disabled=st.session_state.edit)
        mensualidades = st.text_input('Mensualidades', value=factura['MENSUALIDADES'], disabled=st.session_state.edit)
        referencia = st.text_input('Referencia', value=factura['REFERENCIA'], disabled=st.session_state.edit)
    with col9:
        fact_ugavi = st.number_input('Factura UGAVI', format="%d", value=factura['FACT_UGAVI'], disabled=st.session_state.edit)
        fact_fondo = st.number_input('Factura Fondo', format="%d", value=factura['FACT_FONDO'], disabled=st.session_state.edit)
        estado = st.radio('Estado', ['VIGENTE', 'ANULADA'], index=['VIGENTE', 'ANULADA'].index(factura['ESTADO']), disabled=st.session_state.edit)

    col10, col11, col12 = st.columns([1.3, 1.3, 4], gap='small')
    with col10:
        def editar_factura():
            if st.session_state.edit == False:
                st.session_state.edit = True
            else:
                st.session_state.edit = False
        st.button(':material/edit: Editar', on_click=editar_factura, use_container_width=True)
            
    with col11:
        save_changes = st.button(':material/save: Guardar', use_container_width=True)
        if save_changes:
            # Obtener el ID_MIEMBRO correspondiente a la razón social seleccionada
            id_miembro = miembros.loc[miembros['RAZON_SOCIAL'] == razon_social, 'ID_MIEMBRO'].values[0]
            
            # Diccionario para almacenar los campos a actualizar en FactCuota
            campos_valores_factura = {
                "ID_MIEMBRO": id_miembro,
                "FECHA": fecha,
                "MONTO_BS": monto_bs,
                "MONTO_DIVISAS": monto_divisas,
                "METODO_PAGO": metodo_pago,
                "FACT_UGAVI": fact_ugavi,
                "FACT_FONDO": fact_fondo,
                "MENSUALIDADES": mensualidades,
                "REFERENCIA": referencia,
                "ESTADO" : estado
            }
            
            # Actualizar factura
            try:
                session.query(FactCuota).filter(FactCuota.ID_FACTURA == factura['ID_FACTURA']).update(campos_valores_factura)
                session.commit()
                mensaje = 'Factura actualizada exitosamente'
                st.session_state.notificacion = mensaje
                st.rerun()
            except Exception as e:
                session.rollback()
                mensaje = f'Error al actualizar la factura. Error: {e}'
                st.session_state.notificacion = mensaje
                st.rerun()
            

@st.dialog('Eliminar Factura', width="large")
def eliminar_factura():
    st.warning('¿Estás seguro de que quieres eliminar la siguiente factura?')
    factura = st.session_state.selected_factura
    st.write(f'ID Factura: {list(factura["FACT_FONDO"].values())}')
    
    col0, col1, col2, col3 = st.columns([2, 1.3, 1.3, 2], gap='medium')
    with col0:
        if st.button('Confirmar', use_container_width=True):
            for valor in factura["ID_FACTURA"].values():
                try:
                    session.query(FactCuota).filter(FactCuota.ID_FACTURA == valor).delete()
                    session.commit()
                    mensaje = 'Factura eliminada exitosamente'
                    st.session_state.notificacion = mensaje
                except Exception as e:
                    session.rollback()
                    mensaje = f'Error al eliminar la factura con ID {factura["ID_FACTURA"]}. Error: {e}'
                    st.session_state.notificacion = mensaje
            st.rerun()

@st.dialog("Reporte de Ingresos por Cuotas",width="small")
def generar_reporte():
    col1, col2 = st.columns([2, 1], vertical_alignment='bottom')
    with col1:
        filtro_reporte = st.date_input(
            "Filtrar por fecha:",
            value=(datetime.now().replace(day=1).date(), datetime.now().date()),
            format="DD/MM/YYYY", key='filtro_reportes_factura'
        )
    with col2:
        reporte = generar_reporte_con_formato_imagen(facturas_completo, filtro_reporte, logo_path="assets/images/LOGO.png")
        # Descargar el PDF
        if len(filtro_reporte) > 1:
            st.download_button(
                label=":material/download: Descargar",
                data=reporte,
                file_name=f"Reporte_Facturacion_{filtro_reporte[0]}_a_{filtro_reporte[1]}.pdf",
                mime="application/pdf"
            )
    

facturas_completo = facturas.merge(miembros[['ID_MIEMBRO', 'RAZON_SOCIAL']], on='ID_MIEMBRO', how='left')
facturas_completo['ID_MIEMBRO'] = facturas_completo['RAZON_SOCIAL']
facturas_completo.drop(columns=['RAZON_SOCIAL'], inplace=True)

# Secciones de la página
header = st.container()
tabla = st.container()
botones = st.container()

with header:
    col1, col2, col3 = st.columns([4, 1, 1], vertical_alignment='center')
    with col1:
        st.title('Facturación de Miembros')
        st.write('En esta sección se muestran las facturas de los miembros')
    with col2:
        add_factura = st.button(':material/add: Nueva Factura', type='primary')
        if add_factura:
            agregar_factura()
    with col3:
        generar_reporte_btn = st.button(":material/download: Reporte", type="primary")
        if generar_reporte_btn:
            generar_reporte()

    col7, col8 = st.columns([1,5])
    with col7:
        filtro = st.date_input(
            'Filtrar por fecha:',
            value=(datetime.now().replace(day=1).date(), datetime.now().date()),
            format='DD/MM/YYYY')

with tabla:
    if facturas_completo.empty:
        st.divider()
        col4, col5, col6 = st.columns([2.4,1.2,2.4])
        with col5:
            st.warning('No hay facturas registradas')
            seleccion = []
    else:
        # Aplicar el filtro de fecha
        if isinstance(filtro, tuple) and len(filtro) == 2:
            fecha_inicio, fecha_fin = filtro
            facturas_completo = facturas_completo[
                (facturas_completo['FECHA'] >= fecha_inicio) & (facturas_completo['FECHA'] <= fecha_fin)
            ]

        sorted_facturas = facturas_completo.sort_values(by='FECHA', ascending=False)
        # Filtrar las columnas a mostrar
        facturas_filtrado = sorted_facturas[[
            "FECHA", "ID_MIEMBRO", "MONTO_BS", "MONTO_DIVISAS", "METODO_PAGO", "MENSUALIDADES","FACT_UGAVI","FACT_FONDO", "ESTADO"
        ]]

        # Configuración de las columnas
        conf_col = {
            "FECHA": st.column_config.DateColumn("Fecha", format="DD-MM-YYYY"),
            "ID_MIEMBRO": st.column_config.TextColumn("Razón Social"),
            "MONTO_BS": st.column_config.NumberColumn("Monto Bs", format="Bs. %.2f"),
            "MONTO_DIVISAS": st.column_config.NumberColumn("Monto Divisas", format="$ %.2f"),
            "METODO_PAGO": st.column_config.TextColumn("Método de Pago"),
            "MENSUALIDADES": st.column_config.TextColumn("Mensualidades"),
            "FACT_UGAVI": st.column_config.NumberColumn("Fact. UGAVI", format="%d"),
            "FACT_FONDO": st.column_config.NumberColumn("Fact. Fondo", format="%d"),
            "ESTADO": st.column_config.TextColumn("Estado")
        }

        # Mostrar el DataFrame filtrado en la tabla
        facturas_df = st.dataframe(
            facturas_filtrado,
            use_container_width=True,
            hide_index=True,
            column_config=conf_col,
            on_select='rerun',
            selection_mode='multi-row'
        )

        # Obtener las filas seleccionadas
        seleccion = facturas_df.selection.rows

with botones:
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
            if len(seleccion) >= 1:
                delete_factura = st.button(':material/delete: Eliminar Factura', type='primary')
                if delete_factura and seleccion:
                    st.session_state.selected_factura = sorted_facturas.iloc[(seleccion)].to_dict()
                    eliminar_factura()
    with col2:
        if len(seleccion) == 1:
            edit_factura = st.button(':material/edit: Ver/Editar', type='primary')
            if edit_factura and seleccion:
                st.session_state.selected_factura = sorted_facturas.iloc[(seleccion[0])].to_dict()
                print(seleccion[0])
                print(facturas_completo.iloc[seleccion[0]])
                print(st.session_state.selected_factura)
                editar_factura()
    with col3:
        if len(seleccion) == 1:
            generar_factura = st.button(':material/receipt: Generar Factura', type='primary')
            if generar_factura and seleccion:
                factura_seleccionada = sorted_facturas.iloc[seleccion[0]].to_dict()
                pdf_file = generar_factura_pdf(factura_seleccionada, miembros_completo)
                st.download_button(
                    label="Descargar Factura",
                    data=pdf_file,
                    file_name=f"Factura_{factura_seleccionada['FACT_FONDO']}.pdf",
                    mime="application/pdf"
                )

# Configurar el sistema de impresió

