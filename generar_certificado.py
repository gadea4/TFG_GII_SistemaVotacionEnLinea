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

    

