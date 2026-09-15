import os
import sys
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime
from fpdf import FPDF
from passlib.context import CryptContext
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database import engine
from app.auth import pwd_context

STORAGE_DIR = BACKEND_DIR / "storage" / "silabos"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def create_sample_syllabus_pdf(file_path: Path, curso_codigo: str, curso_nombre: str, docente_nombre: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "PORTAL ACADÉMICO UNIVERSITARIO", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "SÍLABO OFICIAL DEL CURSO", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(45, 8, "Código de Curso:", border=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, curso_codigo, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(45, 8, "Nombre de Curso:", border=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, curso_nombre, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(45, 8, "Docente a cargo:", border=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, docente_nombre, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(45, 8, "Periodo Académico:", border=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "2026 II-B", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "1. SUMILLA", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, f"El presente curso de {curso_nombre} ({curso_codigo}) es de naturaleza teórico-práctica y tiene como propósito fundamental desarrollar en los estudiantes las competencias profesionales para el diseño, desarrollo, pruebas e implementación de soluciones modernas de software e infraestructura, aplicando estándares internacionales de calidad y mejores prácticas de la industria.")

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "2. COMPETENCIAS Y LOGROS DE APRENDIZAJE", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, "Al finalizar la asignatura, el estudiante demuestra dominio en la formulación, arquitectura y ejecución de proyectos de software, garantizando rendimiento, seguridad y escalabilidad.")

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "3. SISTEMA DE EVALUACIÓN", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "- Práctica Calificada 1 (PC1): 20%", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "- Examen Parcial (EP): 25%", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "- Práctica Calificada 2 (PC2): 25%", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "- Examen Final (EF): 30%", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 8, f"Documento oficial emitido el {date.today().strftime('%d/%m/%Y')}. Válido para el periodo 2026 II-B.", align="C")

    pdf.output(str(file_path))

def run_migration_and_seed():
    print("Iniciando migración y seed...")
    with engine.begin() as conn:
        # Ejecutar migration_v2.sql
        sql_file = BASE_DIR / "database" / "migration_v2.sql"
        sql_content = sql_file.read_text(encoding="utf-8")
        conn.execute(text(sql_content))
        print("Migración SQL ejecutada correctamente.")

        # 1. Carrera
        conn.execute(text("""
            INSERT INTO carreras (codigo, nombre)
            VALUES ('ISI', 'INGENIERÍA DE SISTEMAS DE INFORMACIÓN')
            ON CONFLICT (codigo) DO UPDATE SET nombre = EXCLUDED.nombre;
        """))
        carrera_id = conn.execute(text("SELECT id FROM carreras WHERE codigo = 'ISI'")).scalar()

        # 2. Periodos
        conn.execute(text("""
            INSERT INTO periodos (codigo, nombre, activo) VALUES
            ('2026 II-B', 'Periodo Académico 2026 Semestre II-B', TRUE),
            ('2026 II-A', 'Periodo Académico 2026 Semestre II-A', FALSE)
            ON CONFLICT (codigo) DO UPDATE SET activo = EXCLUDED.activo;
        """))
        periodo_actual_id = conn.execute(text("SELECT id FROM periodos WHERE codigo = '2026 II-B'")).scalar()
        periodo_ant_id = conn.execute(text("SELECT id FROM periodos WHERE codigo = '2026 II-A'")).scalar()

        # 3. Docentes
        docentes_data = [
            ("DOC-001", "Roberto Carlos", "Mendoza Castro", "rmendoza@portal.edu.pe"),
            ("DOC-002", "Elena Patricia", "Torres Valdivia", "etorres@portal.edu.pe"),
            ("DOC-003", "Erick Walter", "Palomino Silva", "epalomino@portal.edu.pe"),
            ("DOC-004", "Hugo César", "Paredes Rivas", "hparedes@portal.edu.pe")
        ]
        for cod, nom, ape, mail in docentes_data:
            conn.execute(text("""
                INSERT INTO docentes (codigo, nombres, apellidos, email)
                VALUES (:c, :n, :a, :m)
                ON CONFLICT (codigo) DO UPDATE SET nombres = EXCLUDED.nombres, apellidos = EXCLUDED.apellidos;
            """), {"c": cod, "n": nom, "a": ape, "m": mail})

        doc_mendoza = conn.execute(text("SELECT id FROM docentes WHERE codigo = 'DOC-001'")).scalar()
        doc_torres = conn.execute(text("SELECT id FROM docentes WHERE codigo = 'DOC-002'")).scalar()
        doc_palomino = conn.execute(text("SELECT id FROM docentes WHERE codigo = 'DOC-003'")).scalar()
        doc_paredes = conn.execute(text("SELECT id FROM docentes WHERE codigo = 'DOC-004'")).scalar()

        # 4. Cursos (los 7 del portal de la captura)
        cursos_data = [
            ("ETN24-002", "EXPERIENCIA FORMATIVA EN SITUACIÓN REAL DE TRABAJO", 3, "Ing. Roberto Carlos Mendoza", 7, "ETNC262M1-2", doc_mendoza),
            ("EIS-038", "SOLUCIONES MÓVILES Y CLOUD", 4, "Mg. Elena Torres Valdivia", 7, "EIS7A262N", doc_torres),
            ("EIS-037", "MODELAMIENTO DE BASE DE DATOS", 4, "Ing. Erick Palomino Silva", 7, "EIS7A262N", doc_palomino),
            ("EIS-039", "VALIDACIÓN Y PRUEBAS DE SOFTWARE", 4, "Dr. Hugo Paredes Rivas", 7, "EIS7A262N", doc_paredes),
            ("EIS-040", "ARQUITECTURA DE SOFTWARE", 4, "Mg. Elena Torres Valdivia", 8, "EIS8B262N", doc_torres),
            ("EIS-042", "GESTIÓN DE BASES DE DATOS", 4, "Ing. Erick Palomino Silva", 8, "EIS8B262N", doc_palomino),
            ("ETR-010", "EXPERIENCIA FORMATIVA EN SITUACIÓN REAL DE TRABAJO IV", 3, "Ing. Roberto Carlos Mendoza", 8, "EIS8B262N", doc_mendoza),
        ]

        curso_ids = {}
        seccion_ids = {}
        for cod, nom, cred, doc_nombre, ciclo, secc_cod, doc_id in cursos_data:
            conn.execute(text("""
                INSERT INTO cursos (codigo, nombre, creditos, docente, ciclo)
                VALUES (:c, :n, :cr, :d, :ci)
                ON CONFLICT (codigo) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    creditos = EXCLUDED.creditos,
                    docente = EXCLUDED.docente,
                    ciclo = EXCLUDED.ciclo;
            """), {"c": cod, "n": nom, "cr": cred, "d": doc_nombre, "ci": ciclo})
            c_id = conn.execute(text("SELECT id FROM cursos WHERE codigo = :c"), {"c": cod}).scalar()
            curso_ids[cod] = c_id

            # Crear sección para 2026 II-B
            res = conn.execute(text("""
                SELECT id FROM secciones
                WHERE curso_id = :cid AND periodo_id = :pid AND codigo = :scod
            """), {"cid": c_id, "pid": periodo_actual_id, "scod": secc_cod}).scalar()
            if not res:
                conn.execute(text("""
                    INSERT INTO secciones (codigo, curso_id, docente_id, periodo_id)
                    VALUES (:scod, :cid, :did, :pid)
                """), {"scod": secc_cod, "cid": c_id, "did": doc_id, "pid": periodo_actual_id})
                sec_id = conn.execute(text("""
                    SELECT id FROM secciones
                    WHERE curso_id = :cid AND periodo_id = :pid AND codigo = :scod
                """), {"cid": c_id, "pid": periodo_actual_id, "scod": secc_cod}).scalar()
            else:
                sec_id = res
            seccion_ids[cod] = sec_id

            # Generar Sílabo real en PDF
            pdf_name = f"silabo_{cod}.pdf"
            pdf_path = STORAGE_DIR / pdf_name
            create_sample_syllabus_pdf(pdf_path, cod, nom, doc_nombre)

            # Insertar en tabla silabos
            conn.execute(text("DELETE FROM silabos WHERE curso_id = :cid"), {"cid": c_id})
            conn.execute(text("""
                INSERT INTO silabos (curso_id, nombre_archivo, ruta_archivo, fecha_subida)
                VALUES (:cid, :na, :ra, CURRENT_TIMESTAMP)
            """), {"cid": c_id, "na": pdf_name, "ra": str(pdf_path)})

        # 5. Tipos de Evaluación
        tipos_eval = [
            ("PC", "Práctica Calificada"),
            ("EP", "Examen Parcial"),
            ("EF", "Examen Final"),
            ("TB", "Trabajo Aplicativo")
        ]
        for tcod, tnom in tipos_eval:
            conn.execute(text("""
                INSERT INTO tipos_evaluacion (codigo, nombre)
                VALUES (:c, :n)
                ON CONFLICT (codigo) DO UPDATE SET nombre = EXCLUDED.nombre;
            """), {"c": tcod, "n": tnom})

        tipo_pc = conn.execute(text("SELECT id FROM tipos_evaluacion WHERE codigo = 'PC'")).scalar()
        tipo_ep = conn.execute(text("SELECT id FROM tipos_evaluacion WHERE codigo = 'EP'")).scalar()
        tipo_ef = conn.execute(text("SELECT id FROM tipos_evaluacion WHERE codigo = 'EF'")).scalar()

        # 6. Evaluaciones para cada sección
        # PC1 (20%), EP (25%), PC2 (25%), EF (30%)
        eval_weights = [
            ("Práctica 1", tipo_pc, Decimal("20.00"), 1),
            ("Examen Parcial", tipo_ep, Decimal("25.00"), 2),
            ("Práctica 2", tipo_pc, Decimal("25.00"), 3),
            ("Examen Final", tipo_ef, Decimal("30.00"), 4)
        ]
        
        eval_ids = {} # (seccion_id, orden) -> eval_id
        for cod, s_id in seccion_ids.items():
            for enom, tid, peso, orden in eval_weights:
                eid = conn.execute(text("""
                    SELECT id FROM evaluaciones
                    WHERE seccion_id = :sid AND orden = :ord
                """), {"sid": s_id, "ord": orden}).scalar()
                if not eid:
                    conn.execute(text("""
                        INSERT INTO evaluaciones (seccion_id, tipo_id, nombre, peso, orden)
                        VALUES (:sid, :tid, :n, :p, :ord)
                    """), {"sid": s_id, "tid": tid, "n": enom, "p": peso, "ord": orden})
                    eid = conn.execute(text("""
                        SELECT id FROM evaluaciones
                        WHERE seccion_id = :sid AND orden = :ord
                    """), {"sid": s_id, "ord": orden}).scalar()
                eval_ids[(s_id, orden)] = eid

        # 7. Usuario Estudiante (Carlos Quispe)
        carlos_pass_hash = pwd_context.hash("Estudiante123*")
        user_carlos = conn.execute(text("SELECT id FROM usuarios WHERE correo = 'carlos@portal.edu.pe'")).scalar()
        if not user_carlos:
            conn.execute(text("""
                INSERT INTO usuarios (nombre, correo, password_hash, rol, activo)
                VALUES ('Carlos Alexander Quispe Espino', 'carlos@portal.edu.pe', :ph, 'ESTUDIANTE', TRUE)
            """), {"ph": carlos_pass_hash})
            user_carlos = conn.execute(text("SELECT id FROM usuarios WHERE correo = 'carlos@portal.edu.pe'")).scalar()
        else:
            conn.execute(text("""
                UPDATE usuarios SET password_hash = :ph, rol = 'ESTUDIANTE', nombre = 'Carlos Alexander Quispe Espino'
                WHERE id = :uid
            """), {"ph": carlos_pass_hash, "uid": user_carlos})

        # 8. Estudiante Carlos
        est_carlos = conn.execute(text("SELECT id FROM estudiantes WHERE codigo = '2026001'")).scalar()
        if not est_carlos:
            conn.execute(text("""
                INSERT INTO estudiantes (codigo, nombres, apellidos, dni, correo, carrera, ciclo, fecha_ingreso, estado, usuario_id, carrera_id)
                VALUES ('2026001', 'CARLOS ALEXANDER', 'QUISPE ESPINO', '76543210', 'carlos@portal.edu.pe', 'INGENIERÍA DE SISTEMAS DE INFORMACIÓN', 7, '2023-03-15', 'ACTIVO', :uid, :cid)
            """), {"uid": user_carlos, "cid": carrera_id})
            est_carlos = conn.execute(text("SELECT id FROM estudiantes WHERE codigo = '2026001'")).scalar()
        else:
            conn.execute(text("""
                UPDATE estudiantes
                SET nombres = 'CARLOS ALEXANDER',
                    apellidos = 'QUISPE ESPINO',
                    correo = 'carlos@portal.edu.pe',
                    carrera = 'INGENIERÍA DE SISTEMAS DE INFORMACIÓN',
                    ciclo = 7,
                    usuario_id = :uid,
                    carrera_id = :cid
                WHERE id = :eid
            """), {"uid": user_carlos, "cid": carrera_id, "eid": est_carlos})

        # 9. Matrículas para Carlos en 2026 II-B
        # Limpiamos matrículas previas de Carlos para 2026 II-B y reinsertamos limpiamente
        matricula_ids = {}
        notas_sample = {
            "ETN24-002": [Decimal("16.00"), Decimal("15.00"), Decimal("17.00"), Decimal("16.00")],
            "EIS-038":   [Decimal("15.00"), Decimal("14.00"), Decimal("16.00"), Decimal("15.00")],
            "EIS-037":   [Decimal("18.00"), Decimal("17.00"), Decimal("19.00"), Decimal("18.00")],
            "EIS-039":   [Decimal("14.00"), Decimal("13.00"), Decimal("15.00"), Decimal("14.00")],
            "EIS-040":   [Decimal("17.00"), Decimal("16.00"), Decimal("18.00"), Decimal("17.00")],
            "EIS-042":   [Decimal("15.00"), Decimal("16.00"), Decimal("15.00"), Decimal("16.00")],
            "ETR-010":   [Decimal("19.00"), Decimal("18.00"), Decimal("19.00"), Decimal("20.00")],
        }

        for cod in cursos_data:
            course_cod = cod[0]
            c_id = curso_ids[course_cod]
            s_id = seccion_ids[course_cod]
            
            m_id = conn.execute(text("""
                SELECT id FROM matriculas
                WHERE estudiante_id = :eid AND curso_id = :cid AND periodo = '2026 II-B'
            """), {"eid": est_carlos, "cid": c_id}).scalar()
            
            if not m_id:
                conn.execute(text("""
                    INSERT INTO matriculas (estudiante_id, curso_id, periodo, estado, seccion_id, periodo_id)
                    VALUES (:eid, :cid, '2026 II-B', 'M', :sid, :pid)
                """), {"eid": est_carlos, "cid": c_id, "sid": s_id, "pid": periodo_actual_id})
                m_id = conn.execute(text("""
                    SELECT id FROM matriculas
                    WHERE estudiante_id = :eid AND curso_id = :cid AND periodo = '2026 II-B'
                """), {"eid": est_carlos, "cid": c_id}).scalar()
            else:
                conn.execute(text("""
                    UPDATE matriculas
                    SET seccion_id = :sid, periodo_id = :pid, estado = 'M'
                    WHERE id = :mid
                """), {"sid": s_id, "pid": periodo_actual_id, "mid": m_id})

            matricula_ids[course_cod] = m_id

            # Insertar notas
            c_grades = notas_sample[course_cod]
            # PC1, EP, PC2, EF
            for ord_idx, grade_val in enumerate(c_grades, start=1):
                ev_id = eval_ids[(s_id, ord_idx)]
                conn.execute(text("""
                    INSERT INTO notas (evaluacion_id, matricula_id, valor)
                    VALUES (:evid, :mid, :val)
                    ON CONFLICT (matricula_id, evaluacion_id) DO UPDATE SET valor = EXCLUDED.valor;
                """), {"evid": ev_id, "mid": m_id, "val": grade_val})

        print("¡Seed completado con éxito!")

if __name__ == "__main__":
    run_migration_and_seed()
