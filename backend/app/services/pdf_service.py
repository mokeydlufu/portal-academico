import os
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

class AcademicPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(26, 35, 126) # Azul universitario
        self.cell(0, 8, "PORTAL ACADÉMICO UNIVERSITARIO", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "SISTEMA DE GESTIÓN ACADÉMICA Y REGISTRO CENTRAL", new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(3)
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        fecha_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.cell(0, 10, f"Documento oficial emitido por el Portal Académico el {fecha_str} - Página {self.page_no()}/{{nb}}", align="C")


def generar_boleta_simple_pdf(estudiante_data: dict, periodo_codigo: str, cursos: list[dict], promedio_ponderado: float, total_creditos: int) -> bytes:
    pdf = AcademicPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.add_page()

    # Título del reporte
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 8, "BOLETA DE NOTAS OFICIAL", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(139, 30, 47) # Color guinda
    pdf.cell(0, 6, f"PERIODO ACADÉMICO: {periodo_codigo}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)

    # Cuadro con datos del estudiante
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(10, pdf.get_y(), 190, 26, style="FD")
    start_y = pdf.get_y() + 2

    pdf.set_xy(14, start_y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(32, 5, "Estudiante:")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(80, 5, estudiante_data.get("nombre_completo", "").upper())

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(20, 5, "Código:")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, estudiante_data.get("codigo", ""), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(14)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(32, 5, "Carrera:")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(80, 5, estudiante_data.get("carrera", "").upper())

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(20, 5, "DNI:")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, estudiante_data.get("dni", ""), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(14)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(32, 5, "Ciclo Académico:")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(80, 5, str(estudiante_data.get("ciclo", "")))

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(20, 5, "Fecha:")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, datetime.now().strftime("%d/%m/%Y"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(start_y + 26)
    pdf.ln(3)

    # Tabla de cursos
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(30, 41, 59) # Azul pizarra oscuro
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(200, 200, 200)

    pdf.cell(10, 7, "N°", border=1, align="C", fill=True)
    pdf.cell(24, 7, "CÓDIGO", border=1, align="C", fill=True)
    pdf.cell(88, 7, "ASIGNATURA", border=1, align="L", fill=True)
    pdf.cell(22, 7, "SECCIÓN", border=1, align="C", fill=True)
    pdf.cell(14, 7, "CRÉD.", border=1, align="C", fill=True)
    pdf.cell(16, 7, "PROMEDIO", border=1, align="C", fill=True)
    pdf.cell(16, 7, "ESTADO", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 8)
    fill_row = False
    for idx, c in enumerate(cursos, start=1):
        if fill_row:
            pdf.set_fill_color(248, 250, 252)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.set_text_color(40, 40, 40)
        pdf.cell(10, 6.5, str(idx), border=1, align="C", fill=True)
        pdf.cell(24, 6.5, c.get("codigo", ""), border=1, align="C", fill=True)
        pdf.cell(88, 6.5, c.get("curso", "")[:48], border=1, align="L", fill=True)
        pdf.cell(22, 6.5, c.get("seccion", ""), border=1, align="C", fill=True)
        pdf.cell(14, 6.5, str(c.get("creditos", "")), border=1, align="C", fill=True)

        prom = c.get("promedio")
        prom_str = f"{prom:.2f}" if prom is not None else "--"
        pdf.set_font("Helvetica", "B", 8)
        if prom is not None and prom >= 10.5:
            pdf.set_text_color(13, 110, 253) # Azul aprobado
        elif prom is not None:
            pdf.set_text_color(220, 53, 69) # Rojo reprobado
        else:
            pdf.set_text_color(100, 100, 100)
        pdf.cell(16, 6.5, prom_str, border=1, align="C", fill=True)

        estado = c.get("estado_curso", "EN CURSO")
        if estado == "APROBADO":
            pdf.set_text_color(25, 135, 84) # Verde
        elif estado == "DESAPROBADO":
            pdf.set_text_color(220, 53, 69)
        else:
            pdf.set_text_color(100, 116, 139)
        pdf.cell(16, 6.5, estado[:3], border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        fill_row = not fill_row

    # Resumen de créditos y promedio ponderado
    pdf.ln(3)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(10, pdf.get_y(), 190, 14, style="FD")
    curr_y = pdf.get_y() + 3

    pdf.set_xy(15, curr_y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(50, 7, f"Total de Créditos Matriculados: {total_creditos}")

    pdf.set_xy(120, curr_y)
    prom_pond_str = f"{promedio_ponderado:.2f}" if promedio_ponderado > 0 else "--"
    pdf.cell(70, 7, f"Promedio Ponderado del Periodo: {prom_pond_str}", align="R")

    pdf.ln(18)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, "Nota: Esta boleta informativa refleja las calificaciones registradas en el sistema oficial a la fecha de emisión.", align="C", new_x="LMARGIN", new_y="NEXT")

    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


def generar_boleta_detallada_pdf(estudiante_data: dict, periodo_codigo: str, cursos_detallados: list[dict], promedio_ponderado: float, total_creditos: int) -> bytes:
    pdf = AcademicPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.add_page()

    # Encabezado
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 8, "BOLETA DE NOTAS DETALLADA", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(139, 30, 47)
    pdf.cell(0, 6, f"EVALUACIONES Y RENDIMIENTO - PERIODO {periodo_codigo}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)

    # Datos estudiante
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(10, pdf.get_y(), 190, 20, style="FD")
    start_y = pdf.get_y() + 2

    pdf.set_xy(14, start_y)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(28, 5, "Estudiante:")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(85, 5, estudiante_data.get("nombre_completo", "").upper())

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(18, 5, "Código:")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, estudiante_data.get("codigo", ""), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(14)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(28, 5, "Carrera:")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(85, 5, estudiante_data.get("carrera", "").upper())

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(18, 5, "Ciclo:")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, str(estudiante_data.get("ciclo", "")), new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(start_y + 20)
    pdf.ln(3)

    # Detalle por cada curso
    for c in cursos_detallados:
        if pdf.get_y() > 245:
            pdf.add_page()

        # Cabecera del curso
        pdf.set_fill_color(241, 245, 249)
        pdf.set_draw_color(203, 213, 225)
        pdf.rect(10, pdf.get_y(), 190, 7, style="FD")
        
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(15, 23, 42)
        curso_titulo = f"{c.get('codigo')} - {c.get('curso')} | Sec: {c.get('seccion')} | Docente: {c.get('docente')}"
        pdf.cell(150, 7, curso_titulo[:75], align="L")
        
        prom = c.get("promedio_actual")
        prom_str = f"Promedio: {prom:.2f}" if prom is not None else "Promedio: --"
        pdf.set_text_color(139, 30, 47)
        pdf.cell(40, 7, prom_str, align="R", new_x="LMARGIN", new_y="NEXT")

        # Sub-tabla de evaluaciones
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_fill_color(226, 232, 240)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(75, 5, "Evaluación", border=1, fill=True)
        pdf.cell(35, 5, "Tipo", border=1, align="C", fill=True)
        pdf.cell(30, 5, "Peso (%)", border=1, align="C", fill=True)
        pdf.cell(25, 5, "Nota", border=1, align="C", fill=True)
        pdf.cell(25, 5, "Estado", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(30, 41, 59)
        for ev in c.get("evaluaciones", []):
            pdf.cell(75, 4.8, ev.get("evaluacion", ""), border=1)
            pdf.cell(35, 4.8, ev.get("tipo", ""), border=1, align="C")
            pdf.cell(30, 4.8, f"{ev.get('peso', 0):.0f}%", border=1, align="C")

            nota_val = ev.get("nota")
            nota_str = f"{nota_val:.2f}" if nota_val is not None else "--"
            if nota_val is not None and nota_val >= 10.5:
                pdf.set_text_color(13, 110, 253)
            elif nota_val is not None:
                pdf.set_text_color(220, 53, 69)
            else:
                pdf.set_text_color(100, 100, 100)
            pdf.cell(25, 4.8, nota_str, border=1, align="C")

            pdf.set_text_color(30, 41, 59)
            pdf.cell(25, 4.8, ev.get("estado", ""), border=1, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(3)

    # Resumen final
    if pdf.get_y() > 255:
        pdf.add_page()
        
    pdf.ln(2)
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(10, pdf.get_y(), 190, 12, style="FD")
    res_y = pdf.get_y() + 2.5

    pdf.set_xy(15, res_y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(60, 7, f"Total de Asignaturas: {len(cursos_detallados)} | Créditos: {total_creditos}")

    pdf.set_xy(120, res_y)
    prom_pond_str = f"{promedio_ponderado:.2f}" if promedio_ponderado > 0 else "--"
    pdf.cell(70, 7, f"Promedio Ponderado Final: {prom_pond_str}", align="R")

    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


def generar_record_academico_pdf(estudiante_data: dict, record_data: dict) -> bytes:
    pdf = AcademicPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 8, "CERTIFICADO DE RÉCORD ACADÉMICO HISTÓRICO", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(139, 30, 47)
    pdf.cell(0, 6, "REGISTRO CENTRAL Y RENDIMIENTO CONSOLIDADO", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)

    # Datos estudiante
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(10, pdf.get_y(), 190, 22, style="FD")
    start_y = pdf.get_y() + 2

    pdf.set_xy(14, start_y)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(30, 5, "Estudiante:")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(85, 5, estudiante_data.get("nombre_completo", "").upper())

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(20, 5, "Código:")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, estudiante_data.get("codigo", ""), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(14)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(30, 5, "Programa:")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(85, 5, estudiante_data.get("carrera", "").upper())

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(20, 5, "DNI:")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, estudiante_data.get("dni", ""), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(14)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(30, 5, "Condición:")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(85, 5, "ALUMNO REGULAR")

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(20, 5, "Ciclo:")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, str(estudiante_data.get("ciclo", "")), new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(start_y + 22)
    pdf.ln(3)

    # Tabla de cursos
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(200, 200, 200)

    pdf.cell(10, 7, "N°", border=1, align="C", fill=True)
    pdf.cell(24, 7, "PERIODO", border=1, align="C", fill=True)
    pdf.cell(24, 7, "CÓDIGO", border=1, align="C", fill=True)
    pdf.cell(90, 7, "ASIGNATURA", border=1, align="L", fill=True)
    pdf.cell(14, 7, "CRÉD.", border=1, align="C", fill=True)
    pdf.cell(14, 7, "NOTA", border=1, align="C", fill=True)
    pdf.cell(14, 7, "EST.", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 8)
    fill_row = False
    cursos = record_data.get("cursos", [])
    for idx, c in enumerate(cursos, start=1):
        if pdf.get_y() > 265:
            pdf.add_page()
            # Encabezado repetido
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(30, 41, 59)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(10, 7, "N°", border=1, align="C", fill=True)
            pdf.cell(24, 7, "PERIODO", border=1, align="C", fill=True)
            pdf.cell(24, 7, "CÓDIGO", border=1, align="C", fill=True)
            pdf.cell(90, 7, "ASIGNATURA", border=1, align="L", fill=True)
            pdf.cell(14, 7, "CRÉD.", border=1, align="C", fill=True)
            pdf.cell(14, 7, "NOTA", border=1, align="C", fill=True)
            pdf.cell(14, 7, "EST.", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 8)

        if fill_row:
            pdf.set_fill_color(248, 250, 252)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.set_text_color(40, 40, 40)
        pdf.cell(10, 6, str(idx), border=1, align="C", fill=True)
        pdf.cell(24, 6, c.get("periodo", ""), border=1, align="C", fill=True)
        pdf.cell(24, 6, c.get("codigo", ""), border=1, align="C", fill=True)
        pdf.cell(90, 6, c.get("curso", "")[:48], border=1, align="L", fill=True)
        pdf.cell(14, 6, str(c.get("creditos", "")), border=1, align="C", fill=True)

        prom = c.get("promedio")
        prom_str = f"{prom:.2f}" if prom is not None else "--"
        pdf.set_font("Helvetica", "B", 8)
        if prom is not None and prom >= 10.5:
            pdf.set_text_color(13, 110, 253)
        elif prom is not None:
            pdf.set_text_color(220, 53, 69)
        else:
            pdf.set_text_color(100, 100, 100)
        pdf.cell(14, 6, prom_str, border=1, align="C", fill=True)

        estado = c.get("estado", "APROBADO")
        pdf.set_text_color(25, 135, 84) if estado == "APROBADO" else pdf.set_text_color(100, 116, 139)
        pdf.cell(14, 6, estado[:3], border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        fill_row = not fill_row

    # Resumen acumulado
    pdf.ln(3)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(10, pdf.get_y(), 190, 14, style="FD")
    res_y = pdf.get_y() + 3

    pdf.set_xy(15, res_y)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(60, 7, f"Total Asignaturas: {record_data.get('total_cursos', 0)} | Créditos Aprobados: {record_data.get('creditos_aprobados', 0)}")

    pdf.set_xy(110, res_y)
    prom_acum = record_data.get("promedio_acumulado", 0.0)
    pdf.cell(85, 7, f"Promedio Ponderado Acumulado: {prom_acum:.2f}", align="R")

    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()
