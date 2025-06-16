from streamlit.components.v1 import html
import uuid
import datetime

def setup_printing(html_content):
    iframe_id = f"print-frame-{uuid.uuid4()}"
    
    js = f"""
    <script>
    function prepareAndPrint() {{
        // Crear iframe oculto
        var iframe = document.createElement('iframe');
        iframe.id = '{iframe_id}';
        iframe.style.position = 'fixed';
        iframe.style.right = '0';
        iframe.style.bottom = '0';
        iframe.style.width = '0';
        iframe.style.height = '0';
        iframe.style.border = 'none';
        document.body.appendChild(iframe);
        
        // Insertar contenido
        var iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        iframeDoc.open();
        iframeDoc.write(`{html_content}`);
        iframeDoc.close();
        
        // Esperar a que el contenido se cargue y luego imprimir
        iframe.onload = function() {{
            setTimeout(function() {{
                iframe.contentWindow.focus();
                iframe.contentWindow.print();
            }}, 200); // Pequeño retraso para asegurar la carga
        }};
    }}
    
    // Ejecutar automáticamente al cargar la página
    window.addEventListener('load', prepareAndPrint);
    </script>
    """
    html(js)


def invoice_model(date: datetime, name: str, adress: str, id: str, month: str, monto: float):
    day = date.day
    month_date = date.month
    year = date.year
    monto_ugavi = monto * 0.6
    monto_fondo = monto * 0.2
    total1 = monto_ugavi + monto_fondo
    html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                @page {{
                    size: 205mm 148mm;
                    margin: 0;
                    padding: 0;
                }}
                body {{
                    width: 205mm;
                    margin: 0;
                    padding: 0;
                    padding: 4mm;
                    font-family: Arial;
                    font-size: 12.5pt;
                    position: relative;
                }}
                .pagina {{
                    width: 205mm;
                    height: 148mm;
                    padding-top: 2mm;
                    position: relative;
                    page-break-after: always;
                    overflow: hidden;
                }}
                .pagina:last-child {{
                    page-break-after: auto;
                }}
                .date {{
                    position: absolute;
                    top: 34mm;
                    right: 154mm;
                }}
                .name {{
                    position: absolute;
                    top: 41mm;
                    left: 66mm;
                    font-size: 13.5pt;
                }}
                .address {{
                    position: absolute;
                    top: 45mm;
                    left: 50mm;
                }}
                .id {{
                    position: absolute;
                    top: 51mm;
                    left: 150mm;
                    /* Prueba añadiendo !important para la impresión */
                    /* position: absolute !important;
                    top: 60mm !important;
                    left: 148mm !important; */
                }}
        
                .items-wrapper {{
                    position: absolute;
                    top: 63mm;
                    left: 18mm;
                    width: 180mm;
                    display: flex;
                    flex-direction: column;  /* Apila los elementos verticalmente */
                    gap: 1mm;  /* Espacio entre elementos */
                }}
                
                .item-container {{
                    display: flex;
                    justify-content: space-between;
                    width: 100%;
                }}
        
                .item-description {{
                    width: 104mm;
                    text-align: left;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    white-space: normal;
                    /* background-color: rgba(255,0,0,0.1); /* Solo para visualización */
                }}
        
                .item-amount {{
                    width: 32mm;
                    text-align: right;
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-end;
                    /* background-color: rgba(0,255,0,0.1); /* Solo para visualización */
                    /* Prueba añadiendo !important para la impresión */
                    /* display: flex !important;
                    flex-direction: column !important;
                    justify-content: flex-end !important; */
                }}
        
                .total1 {{
                    position: absolute;
                    top: 119mm;
                    right: 20mm;
                    text-align: right;
                }}
                .dash1 {{
                    position: absolute;
                    top: 124mm;
                    right: 20mm;
                    text-align: right;
                }}
                .dash2 {{
                    position: absolute;
                    top: 129mm;
                    right: 20mm;
                    text-align: right;
                }}
                .final-total {{
                    position: absolute;
                    top: 134mm;
                    right: 20mm;
                    text-align: right;
                }}
                
                .date2 {{
                    position: absolute;
                    top: 48mm;
                    right: 140mm;
                }}
                
                .name2 {{
                    position: absolute;
                    top: 54mm;
                    left: 58mm;
                    font-size: 13.5pt;
                }}
                
                .address2 {{
                    position: absolute;
                    top: 59mm;
                    left: 41mm;
                }}
                
                .id2 {{
                    position: absolute;
                    top: 65mm;
                    left: 160mm;
                    /* Prueba añadiendo !important para la impresión */
                    /* position: absolute !important;
                    top: 60mm !important;
                    left: 148mm !important; */
                }}
        
                .item-container2 {{
                    position: absolute;
                    top: 78mm;
                    left: 30mm;
                    width: 168mm;
                    display: flex;
                    justify-content: space-between;
                    font-size: 13.5pt;
                }}
        
                .item-description2 {{
                    width: 104mm;
                    text-align: left;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    white-space: normal;
                    /* background-color: rgba(255,0,0,0.1); /* Solo para visualización */
                }}
        
                .item-amount2 {{
                    width: 28mm;
                    text-align: center;
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-end;
                    /* background-color: rgba(0,255,0,0.1); /* Solo para visualización */
                    /* Prueba añadiendo !important para la impresión */
                    /* display: flex !important;
                    flex-direction: column !important;
                    justify-content: flex-end !important; */
                }}
        
                .total12 {{
                    position: absolute;
                    top: 120mm;
                    right: 18mm;
                    text-align: right;
                }}
                .dash12 {{
                    position: absolute;
                    top: 128mm;
                    right: 21mm;
                    text-align: right;
                }}
                .dash22 {{
                    position: absolute;
                    top: 135mm;
                    right: 21mm;
                    text-align: right;
                }}
                .final-total2 {{
                    position: absolute;
                    top: 141mm;
                    right: 18mm;
                    text-align: right;
                }}
        
        
                /* Estilos específicos para la impresión (prueba aquí) */
                @media print {{
                    /* Intenta forzar la visualización */
                    .id {{
                        /* position: absolute !important;
                        top: 60mm !important;
                        left: 148mm !important; */
                        color: black !important; /* Asegúrate de que el color no sea blanco o transparente */
                    }}
                    .item-amount {{
                        /* display: flex !important;
                        flex-direction: column !important;
                        justify-content: flex-end !important; */
                        color: black !important; /* Asegúrate de que el color no sea blanco o transparente */
                    }}
        
                    /* Prueba con un borde para ver si el elemento está ahí */
                    /* .id {{ border: 1px solid black !important; }}
                    .item-amount {{ border: 1px solid blue !important; }} */
                }}
            </style>
        </head>
        <body>
            <div class="pagina">
                <div class="date">{day} &emsp;{month_date} &emsp;{year}</div>
            
                <div class="name">{name}</div>
                <div class="address">{adress}</div>
                <div class="id">{id}</div>

                <div class="items-wrapper">
                    <div class="item-container">
                        <div class="item-description">
                            CANCELACIÓN DEL 60% POR CUOTA CORRESPONDIENTE A {month}
                        </div>
                        <div class="item-amount">
                            {monto_ugavi:.2f}
                        </div>
                    </div>
                    <div class="item-container">
                        <div class="item-description">
                            CANCELACIÓN DEL 20% POR CUOTA CORRESPONDIENTE A {month}
                        </div>
                        <div class="item-amount">
                            {monto_fondo:.2f}
                        </div>
                    </div>
                </div>
            
                <div class="total1">{total1:.2f}</div>
                <div class="dash1">-</div>
                <div class="dash2">-</div>
                <div class="final-total">{total1:.2f}</div>
            </div>
        
            <!-- SEGUNDA PÁGINA (MONTOS ACTUALIZADOS) -->
            <div class="pagina">
                <div class="date2">{day} &emsp;&emsp;{month_date} &emsp;{year}</div>
            
                <div class="name2">{name}</div>
                <div class="address2">{adress}</div>
                <div class="id2">{id}</div>
            
                <div class="item-container2">
                    <div class="item-description2">
                        CANCELACIÓN DEL 20% POR CUOTA CORRESPONDIENTE A {month}
                    </div>
                    <div class="item-amount2">
                        {monto_fondo:.2f}
                    </div>
                </div>
            
                <div class="total12">{monto_fondo:.2f}</div>
                <div class="dash12">-</div>
                <div class="dash22">-</div>
                <div class="final-total2">{monto_fondo:.2f}</div>
            </div>
        </body>
        </html>
        """
    return html_content

