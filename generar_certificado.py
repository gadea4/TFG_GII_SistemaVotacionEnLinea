# -*- coding: utf-8 -*-
# generar_certificado.py
# Genera el certificado PDF de confirmación de voto

import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

def generar_pdf_certificado(codigo, nombre, apellidos, dni, distrito, seccion, mesa, local, fecha_hora):
    """
    Genera el PDF del certificado de voto y lo devuelve como bytes.
    """

    # ── Colores institucionales ────────────────────────────
    AZUL        = HexColor('#3a7abf')
    AZUL_OSCURO = HexColor('#2a5a9f')
    GRIS_OSC    = HexColor('#4a4a4a')
    GRIS_MED    = HexColor('#666666')
    VERDE       = HexColor('#2e8b57')
    GRIS_FONDO  = HexColor('#f7f9fc')
    GRIS_BORDE  = HexColor('#dddddd')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    # Estilos personalizados
    estilo_titulo = ParagraphStyle(
        'titulo',
        fontSize=18,
        fontName='Helvetica-Bold',
        textColor=AZUL_OSCURO,
        alignment=TA_CENTER,
        spaceAfter=4
    )
    estilo_subtitulo = ParagraphStyle(
        'subtitulo',
        fontSize=11,
        fontName='Helvetica',
        textColor=GRIS_MED,
        alignment=TA_CENTER,
        spaceAfter=2
    )
    estilo_seccion = ParagraphStyle(
        'seccion',
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=AZUL,
        spaceAfter=4,
        spaceBefore=8,
        borderPad=4
    )
    estilo_normal = ParagraphStyle(
        'normal',
        fontSize=10,
        fontName='Helvetica',
        textColor=GRIS_OSC,
        spaceAfter=3,
        leading=16
    )
    estilo_legal = ParagraphStyle(
        'legal',
        fontSize=8,
        fontName='Helvetica',
        textColor=GRIS_MED,
        alignment=TA_JUSTIFY,
        leading=12
    )
    estilo_codigo = ParagraphStyle(
        'codigo',
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=AZUL_OSCURO,
        alignment=TA_CENTER,
        spaceAfter=4
    )
    estilo_ok = ParagraphStyle(
        'ok',
        fontSize=13,
        fontName='Helvetica-Bold',
        textColor=VERDE,
        alignment=TA_CENTER,
        spaceAfter=4
    )

    # DNI parcialmente oculto
    dni_oculto = dni[:4] + '****' + dni[-1] if len(dni) >= 5 else dni

    # ── Construir el documento ────────────────────────────
    elementos = []

    # Cabecera institucional
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("SISTEMA DE VOTACIÓN ELECTRÓNICA", estilo_titulo))
    elementos.append(Paragraph("Universidad de Burgos · Grado en Ingeniería Informática", estilo_subtitulo))
    elementos.append(Spacer(1, 0.3*cm))

    # Línea separadora
    elementos.append(Table(
        [['']],
        colWidths=[17*cm],
        style=TableStyle([('LINEBELOW', (0,0), (-1,-1), 2, AZUL)])
    ))
    elementos.append(Spacer(1, 0.4*cm))

    # Título del certificado
    elementos.append(Paragraph("✔ CERTIFICADO DE EMISIÓN DE VOTO", estilo_ok))
    elementos.append(Spacer(1, 0.2*cm))

    # Número de justificante
    elementos.append(Paragraph(f"Justificante nº {codigo}", estilo_codigo))
    elementos.append(Spacer(1, 0.4*cm))

    # Tabla principal con datos del votante y QR
    tabla_principal = Table(
        [
            [Paragraph("DATOS DEL VOTANTE", estilo_seccion)],
            [Paragraph(f"Nombre:  <b>{nombre} {apellidos}</b>", estilo_normal)],
            [Paragraph(f"DNI:  <b>{dni_oculto}</b>", estilo_normal)],
            [Spacer(1, 0.3*cm)],
            [Paragraph("DATOS DE LA MESA ELECTORAL", estilo_seccion)],
            [Paragraph(f"Local:  <b>{local}</b>", estilo_normal)],
            [Paragraph(f"Distrito: <b>{distrito}</b>  ·  Sección: <b>{seccion}</b>  ·  Mesa: <b>{mesa}</b>", estilo_normal)],
            [Spacer(1, 0.3*cm)],
            [Paragraph("FECHA Y HORA DE EMISIÓN", estilo_seccion)],
            [Paragraph(f"<b>{fecha_hora}</b>", estilo_normal)],
        ],
        colWidths=[17*cm],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), GRIS_FONDO),
            ('BOX', (0,0), (-1,-1), 1, GRIS_BORDE),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 14),
        ])
    )
    elementos.append(tabla_principal)
    elementos.append(Spacer(1, 0.5*cm))

    # Texto legal
    elementos.append(Table(
        [['']],
        colWidths=[17*cm],
        style=TableStyle([('LINEBELOW', (0,0), (-1,-1), 0.5, GRIS_BORDE)])
    ))
    elementos.append(Spacer(1, 0.3*cm))

    texto_legal = (
        "El presente documento acredita que el titular identificado ha ejercido su derecho al voto "
        "de forma correcta a través del Sistema de Votación Electrónica de la Universidad de Burgos. "
        "El voto emitido es <b>secreto e irrevocable</b>, conforme a lo establecido en la Ley Orgánica "
        "5/1985, de 19 de junio, del Régimen Electoral General (LOREG). El contenido del voto no figura "
        "en este justificante ni en ningún registro asociado a la identidad del votante."
    )
    elementos.append(Paragraph(texto_legal, estilo_legal))
    elementos.append(Spacer(1, 0.4*cm))

    # Pie institucional
    elementos.append(Table(
        [['']],
        colWidths=[17*cm],
        style=TableStyle([('LINEABOVE', (0,0), (-1,-1), 1, AZUL)])
    ))
    elementos.append(Spacer(1, 0.2*cm))
    elementos.append(Paragraph(
        "Sistema de Votación Electrónica · Universidad de Burgos · Uso restringido",
        ParagraphStyle('pie', fontSize=8, fontName='Helvetica', textColor=GRIS_MED, alignment=TA_CENTER)
    ))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.read()

