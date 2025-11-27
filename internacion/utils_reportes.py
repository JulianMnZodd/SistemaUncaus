"""
Módulo de utilidades para reportes PDF en BedWise.
Proporciona funciones comunes para generar reportes PDF con estilo consistente.
"""

import io
import qrcode
from datetime import datetime
from django.conf import settings
from django.contrib.staticfiles import finders
from reportlab.lib.utils import ImageReader

def agregar_encabezado_bedwise(canvas, titulo, width, height):
    """
    Agrega un encabezado estandarizado a los reportes PDF de BedWise.
    
    Args:
        canvas: Canvas de ReportLab donde dibujar
        titulo: Título del reporte
        width: Ancho de la página
        height: Alto de la página
    """
    # En entorno de prueba, podríamos no tener acceso a finders, así que lo manejamos con try/except
    logo_path = None
    try:
        logo_path = finders.find("logobedwise.png")
    except:
        # Si hay un error, simplemente no usamos el logo
        pass
    
    # Dibujar el logo si existe
    if logo_path:
        try:
            # Logo a la izquierda, más arriba para evitar superposición
            canvas.drawImage(logo_path, 40, height - 85, width=70, height=50, preserveAspectRatio=True, mask='auto')
        except:
            # Si hay error al dibujar la imagen, usar texto alternativo
            canvas.setFont("Helvetica-Bold", 14)
            canvas.drawString(40, height - 60, "BedWise")
    else:
        # Si no hay logo, dibujar un texto alternativo
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(40, height - 60, "BedWise")
    
    # Título del documento - movido a la derecha para evitar superposición con el logo
    canvas.setFont("Helvetica-Bold", 16)
    # Usando drawString en lugar de drawCentredString para tener más control
    # Calculamos el ancho del texto para centrarlo en el espacio disponible
    texto_ancho = canvas.stringWidth(titulo, "Helvetica-Bold", 16)
    posicion_x = (width / 2) + 35  # Desplazado a la derecha
    canvas.drawString(posicion_x - texto_ancho/2, height - 50, titulo)
    
    # Línea decorativa
    canvas.setStrokeColorRGB(0.2, 0.4, 0.7)  # Azul corporativo
    canvas.setLineWidth(2)
    canvas.line(40, height - 100, width - 40, height - 100)  # Espacio entre encabezado y contenido
    
    # Información del hospital
    canvas.setFont("Helvetica", 8)  # Cambiado de Helvetica-Italic a Helvetica
    canvas.drawRightString(width - 50, height - 80, "Hospital Universitario UNCAUS")
    canvas.drawRightString(width - 50, height - 90, "Comandante Fernández, Chaco")

def generar_codigo_qr(texto, tamano=150):
    """
    Genera un código QR como una imagen para insertar en el PDF.
    
    Args:
        texto: El texto a codificar en el QR
        tamano: Tamaño del código QR en píxeles
    
    Returns:
        ImageReader: Un objeto ImageReader listo para usar con ReportLab
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(texto)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a BytesIO para usar con ReportLab
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Convertir el BytesIO a ImageReader que ReportLab puede usar directamente
        img_reader = ImageReader(buffer)
        return img_reader
    except Exception as e:
        # En caso de error, mostrar detalles
        print(f"Error generando QR: {e}")
        import traceback
        traceback.print_exc()
        return None

def agregar_pie_pagina(canvas, width, num_pagina=None, total_paginas=None, doc_id=None):
    """
    Agrega un pie de página estandarizado a los reportes PDF de BedWise.
    
    Args:
        canvas: Canvas de ReportLab donde dibujar
        width: Ancho de la página
        num_pagina: Número de página actual (opcional)
        total_paginas: Total de páginas (opcional)
        doc_id: Identificador único del documento para el código QR
    """
    # Línea decorativa
    canvas.setStrokeColorRGB(0.2, 0.4, 0.7)
    canvas.setLineWidth(1)
    canvas.line(40, 48, width - 40, 48)  # Movido más arriba para dar espacio al QR
    
    # Fecha de generación
    canvas.setFont("Helvetica", 8)
    fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M')
    canvas.drawString(40, 35, f"Generado el {fecha_generacion}")
    
    # Página X de Y (si se proporciona)
    if num_pagina is not None and total_paginas is not None:
        canvas.drawRightString(width - 40, 35, f"Página {num_pagina} de {total_paginas}")
    
    # Copyright y versión
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(width/2, 35, "BedWise © 2025 - Sistema de Gestión Hospitalaria v1.0")
    
    # Código QR para verificación (si se proporciona un ID)
    if doc_id:
        try:
            # URL de verificación (ficticia, ajustar a la real)
            verification_url = f"https://bedwise.uncaus.edu.ar/verificar/{doc_id}"
            
            # Generar el código QR
            qr_img = generar_codigo_qr(verification_url)
            if qr_img:
                # Dibujar el código QR en una posición más visible
                canvas.drawImage(qr_img, width - 100, 55, width=45, height=45)
                
                # Texto de verificación más visible
                canvas.setFont("Helvetica", 7)
                canvas.drawString(width - 100, 52, f"Verificar: {doc_id[:8]}...")
                print(f"QR agregado para documento {doc_id}")
            else:
                print("Error: no se pudo generar la imagen QR")
        except Exception as e:
            # Si hay error, mostrar detalles para diagnóstico
            print(f"Error al agregar código QR: {e}")
            import traceback
            traceback.print_exc()