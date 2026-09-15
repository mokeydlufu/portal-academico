import sys
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime, timedelta
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database import engine

def run():
    print("Iniciando migración v3 y seed de módulos estudiantiles...")
    with engine.begin() as conn:
        # 1. Ejecutar SQL de migración v3
        sql_file = BASE_DIR / "database" / "migration_v3.sql"
        conn.execute(text(sql_file.read_text(encoding="utf-8")))
        print("Tablas v3 creadas correctamente.")

        # Obtener estudiante Carlos
        est_id = conn.execute(text("SELECT id FROM estudiantes WHERE codigo = '2026001'")).scalar()
        if not est_id:
            raise Exception("No se encontró al estudiante Carlos (2026001). Ejecute run_migration_and_seed.py primero.")

        # Actualizar datos de contacto de Carlos
        conn.execute(text("""
            UPDATE estudiantes
            SET telefono = '987654321', direccion = 'Av. Universitaria 1450, Urb. Maranga, Lima'
            WHERE id = :eid
        """), {"eid": est_id})

        # Periodo actual
        p_act_id = conn.execute(text("SELECT id FROM periodos WHERE codigo = '2026 II-B'")).scalar()

        # Matrículas de Carlos
        matriculas = conn.execute(text("""
            SELECT m.id, m.seccion_id, m.curso_id, c.codigo, c.nombre
            FROM matriculas m
            JOIN cursos c ON m.curso_id = c.id
            WHERE m.estudiante_id = :eid
        """), {"eid": est_id}).fetchall()

        # 2. Horarios por sección
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
        horas = [
            ("07:30", "09:45", "Aula B-201"),
            ("10:00", "12:15", "Lab Sistemas 03"),
            ("13:00", "15:15", "Aula C-104"),
            ("15:30", "17:45", "Lab Software 02"),
            ("18:00", "20:15", "Lab Cloud Computing"),
            ("20:30", "22:45", "Aula Magna A")
        ]

        for idx, m in enumerate(matriculas):
            sec_id = m.seccion_id
            if sec_id:
                has_horario = conn.execute(text("SELECT id FROM horarios WHERE seccion_id = :sid"), {"sid": sec_id}).scalar()
                if not has_horario:
                    dia = dias[idx % len(dias)]
                    h_ini, h_fin, aula = horas[idx % len(horas)]
                    conn.execute(text("""
                        INSERT INTO horarios (seccion_id, dia, hora_inicio, hora_fin, aula, modalidad)
                        VALUES (:sid, :dia, :hi, :hf, :aula, 'PRESENCIAL')
                    """), {"sid": sec_id, "dia": dia, "hi": h_ini, "hf": h_fin, "aula": aula})

            # 3. Asistencias para cada matrícula
            has_asistencias = conn.execute(text("SELECT id FROM asistencias WHERE matricula_id = :mid"), {"mid": m.id}).scalar()
            if not has_asistencias:
                base_date = date.today() - timedelta(days=40)
                estados = ["PRESENTE", "PRESENTE", "PRESENTE", "PRESENTE", "PRESENTE", "TARDANZA", "PRESENTE", "PRESENTE", "FALTA", "PRESENTE"]
                for sess_idx, st in enumerate(estados):
                    fec = base_date + timedelta(days=sess_idx * 4)
                    obs = "Llegó 10 min tarde" if st == "TARDANZA" else ("Inasistencia injustificada" if st == "FALTA" else "Asistencia puntual")
                    conn.execute(text("""
                        INSERT INTO asistencias (matricula_id, fecha, hora, estado, observacion)
                        VALUES (:mid, :fec, '08:00', :st, :obs)
                    """), {"mid": m.id, "fec": fec, "st": st, "obs": obs})

        # 4. Trámites
        conn.execute(text("DELETE FROM tramites WHERE estudiante_id = :eid"), {"eid": est_id})
        conn.execute(text("""
            INSERT INTO tramites (estudiante_id, codigo, tipo, motivo, descripcion, estado, fecha_solicitud, fecha_respuesta, respuesta)
            VALUES
            (:eid, 'TRM-2026-001', 'Constancia de Matrícula Oficial', 'Trámite laboral', 'Solicito constancia de matrícula del semestre 2026-II para acreditar estudios en mi centro de prácticas.', 'APROBADO', NOW() - INTERVAL '15 days', NOW() - INTERVAL '12 days', 'Constancia emitida y firmada digitalmente.'),
            (:eid, 'TRM-2026-002', 'Carnet Universitario SUNEDU 2026', 'Renovación anual', 'Solicito duplicado y actualización de carnet universitario.', 'APROBADO', NOW() - INTERVAL '30 days', NOW() - INTERVAL '25 days', 'Entregado en mesa de partes.'),
            (:eid, 'TRM-2026-003', 'Carta de Presentación para Prácticas', 'Postulación laboral', 'Carta de presentación institucional dirigida al Banco de Crédito del Perú.', 'EN REVISION', NOW() - INTERVAL '2 days', NULL, NULL);
        """), {"eid": est_id})

        # 5. Pagos
        conn.execute(text("DELETE FROM pagos WHERE estudiante_id = :eid"), {"eid": est_id})
        conn.execute(text("""
            INSERT INTO pagos (estudiante_id, periodo_id, concepto, monto, fecha_vencimiento, fecha_pago, estado, nro_operacion)
            VALUES
            (:eid, :pid, 'Matrícula Regular 2026 II-B', 350.00, '2026-08-15', '2026-08-10', 'CANCELADO', 'OP-982142'),
            (:eid, :pid, 'Cuota Académica 01 (2026 II-B)', 850.00, '2026-08-30', '2026-08-28', 'CANCELADO', 'OP-994312'),
            (:eid, :pid, 'Cuota Académica 02 (2026 II-B)', 850.00, '2026-09-30', NULL, 'PENDIENTE', NULL);
        """), {"eid": est_id, "pid": p_act_id})

        # 6. Ficha de Bienestar
        conn.execute(text("""
            INSERT INTO fichas_bienestar (estudiante_id, contacto_emergencia, telefono_emergencia, parentesco_contacto, direccion_actual, ocupacion_padres, ingreso_familiar, condicion_vivienda, seguro_salud, alergias_condiciones)
            VALUES
            (:eid, 'Rosa María Espino Quispe', '991234567', 'Madre', 'Av. Universitaria 1450, Urb. Maranga, San Miguel, Lima', 'Padre: Ingeniero Civil / Madre: Docente', 4500.00, 'Propia', 'Seguro Estudiantil Universitario + EsSalud', 'Ninguna alergia registrada')
            ON CONFLICT (estudiante_id) DO UPDATE SET
                contacto_emergencia = EXCLUDED.contacto_emergencia,
                telefono_emergencia = EXCLUDED.telefono_emergencia,
                direccion_actual = EXCLUDED.direccion_actual;
        """), {"eid": est_id})

        # 7. Empleos
        conn.execute(text("""
            INSERT INTO empleos (empresa, puesto, modalidad, ubicacion, descripcion, requisitos, funciones, remuneracion, fecha_publicacion, fecha_limite, carrera_afin)
            VALUES
            ('Banco de Crédito del Perú (BCP)', 'Practicante Pre-Profesional de Desarrollo Full-Stack', 'Híbrido', 'Lima (Sede Central La Molina)',
             'Nos encontramos en la búsqueda de un talento universitario para incorporarse a nuestro equipo de soluciones digitales.',
             'Estudiante a partir de 7mo ciclo de Ingeniería de Sistemas. Conocimientos en Python, FastAPI, React/Vue y bases de datos relacionales.',
             'Desarrollo de microservicios, soporte a APIs transaccionales y aseguramiento de calidad con pruebas unitarias.',
             'S/ 1,450.00 + Seguro FOLA', CURRENT_DATE - 5, CURRENT_DATE + 20, 'INGENIERÍA DE SISTEMAS DE INFORMACIÓN'),
            ('Interbank - InnovaCX', 'Practicante de Arquitectura Cloud & DevOps', 'Remoto', 'San Isidro',
             'Únete al laboratorio de innovación financiera para diseñar infraestructura moderna y pipelines CI/CD.',
             'Conocimientos en contenedores Docker, Linux, Git y nociones de AWS / GCP.',
             'Automatización de despliegues, monitoreo de métricas y mantenimiento de pipelines de integración continua.',
             'S/ 1,500.00 + Beneficios de ley', CURRENT_DATE - 3, CURRENT_DATE + 15, 'INGENIERÍA DE SISTEMAS DE INFORMACIÓN'),
            ('NTT Data Perú', 'Trainee en Base de Datos & Business Intelligence', 'Presencial', 'Miraflores',
             'Oportunidad para especializarse en ingeniería de datos, modelamiento analítico y cuadros de mando.',
             'Modelamiento entidad-relación, PostgreSQL, Power BI y SQL avanzado.',
             'Elaboración de consultas complejas, optimización de índices y soporte a reportes ejecutivos.',
             'S/ 1,350.00 + Capacitaciones oficiales', CURRENT_DATE - 1, CURRENT_DATE + 25, 'INGENIERÍA DE SISTEMAS DE INFORMACIÓN')
            ON CONFLICT DO NOTHING;
        """))

        # 8. Postulación previa
        emp_id = conn.execute(text("SELECT id FROM empleos LIMIT 1")).scalar()
        if emp_id:
            conn.execute(text("""
                INSERT INTO postulaciones (estudiante_id, empleo_id, fecha_postulacion, estado)
                VALUES (:eid, :empid, NOW() - INTERVAL '3 days', 'EN REVISION')
                ON CONFLICT (estudiante_id, empleo_id) DO NOTHING;
            """), {"eid": est_id, "empid": emp_id})

        # 9. Avisos Académicos
        conn.execute(text("""
            DELETE FROM avisos_academicos;
            INSERT INTO avisos_academicos (titulo, contenido, fecha, tipo)
            VALUES
            ('Cronograma de Evaluaciones Parciales 2026-II', 'Se comunica a los estudiantes que las evaluaciones parciales iniciarán el próximo lunes según el rol de exámenes publicado en el portal.', CURRENT_DATE - 2, 'ACADEMICO'),
            ('Campaña de Actualización de Datos y Bienestar', 'Recuerde actualizar su Ficha Integral de Bienestar para la vigencia del seguro de accidentes estudiantiles.', CURRENT_DATE - 4, 'INFORMATIVO'),
            ('Feria Laboral de Tecnologías de la Información 2026', 'Más de 30 empresas del rubro tech estarán entrevistando postulantes universitarios el día viernes en el auditorio central.', CURRENT_DATE - 6, 'URGENTE');
        """))

        print("¡Migración y seed v3 ejecutado exitosamente!")

if __name__ == "__main__":
    run()
