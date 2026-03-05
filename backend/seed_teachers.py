"""
Script para añadir profesores de prueba con horarios.
Ejecutar tras seed.py:

    cd backend
    python seed_teachers.py
"""
import asyncio

from app.core.database import AsyncSessionLocal
from app.models.teacher import Teacher
from app.models.schedule import Schedule


# Dias: 0=Lunes 1=Martes 2=Miércoles 3=Jueves 4=Viernes
# Tramos: 1-8 (horas del día)

TEACHERS = [
    {
        "nombre": "Amaia",
        "apellidos": "Etxeberria Zubiaurre",
        "email": "amaia.etxeberria@ikastola.eus",
        "telefono": "688001001",
        "especialidades": ["Matemáticas", "Física"],
        "niveles": ["ESO", "Bachillerato"],
        "max_sustituciones_semana": 3,
        "notas": "Coordinadora de 2º de Bachillerato. Disponible tramos de tarde.",
        "horario": [
            # Lunes
            {"dia": 0, "tramo": 1, "curso": "2ºBACH-A", "asignatura": "Matemáticas", "aula": "A01", "libre": False},
            {"dia": 0, "tramo": 2, "curso": "1ºESO-B", "asignatura": "Matemáticas", "aula": "A01", "libre": False},
            {"dia": 0, "tramo": 3, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 0, "tramo": 4, "curso": "2ºESO-A", "asignatura": "Física", "aula": "A02", "libre": False},
            # Martes
            {"dia": 1, "tramo": 1, "curso": "2ºBACH-A", "asignatura": "Matemáticas", "aula": "A01", "libre": False},
            {"dia": 1, "tramo": 2, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 1, "tramo": 3, "curso": "1ºESO-B", "asignatura": "Matemáticas", "aula": "A01", "libre": False},
            {"dia": 1, "tramo": 4, "curso": "2ºESO-A", "asignatura": "Física", "aula": "A02", "libre": False},
            # Miércoles
            {"dia": 2, "tramo": 1, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 2, "tramo": 2, "curso": "2ºBACH-A", "asignatura": "Matemáticas", "aula": "A01", "libre": False},
            {"dia": 2, "tramo": 3, "curso": "1ºESO-B", "asignatura": "Matemáticas", "aula": "A01", "libre": False},
            {"dia": 2, "tramo": 4, "curso": "2ºESO-A", "asignatura": "Física", "aula": "A02", "libre": False},
            # Jueves
            {"dia": 3, "tramo": 1, "curso": "2ºBACH-A", "asignatura": "Matemáticas", "aula": "A01", "libre": False},
            {"dia": 3, "tramo": 2, "curso": "1ºESO-B", "asignatura": "Matemáticas", "aula": "A01", "libre": False},
            {"dia": 3, "tramo": 3, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 3, "tramo": 4, "curso": "2ºESO-A", "asignatura": "Física", "aula": "A02", "libre": False},
            # Viernes
            {"dia": 4, "tramo": 1, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 4, "tramo": 2, "curso": "2ºBACH-A", "asignatura": "Matemáticas", "aula": "A01", "libre": False},
            {"dia": 4, "tramo": 3, "curso": "1ºESO-B", "asignatura": "Matemáticas", "aula": "A01", "libre": False},
        ],
    },
    {
        "nombre": "Josu",
        "apellidos": "Larrañaga Mendiburu",
        "email": "josu.larranaga@ikastola.eus",
        "telefono": "688001002",
        "especialidades": ["Lengua Castellana", "Literatura"],
        "niveles": ["ESO", "Bachillerato"],
        "max_sustituciones_semana": 2,
        "notas": "Jefe del departamento de Humanidades.",
        "horario": [
            # Lunes
            {"dia": 0, "tramo": 1, "curso": "3ºESO-A", "asignatura": "Lengua Castellana", "aula": "B03", "libre": False},
            {"dia": 0, "tramo": 2, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 0, "tramo": 3, "curso": "1ºBACH-B", "asignatura": "Literatura", "aula": "B03", "libre": False},
            {"dia": 0, "tramo": 4, "curso": "4ºESO-C", "asignatura": "Lengua Castellana", "aula": "B03", "libre": False},
            # Martes
            {"dia": 1, "tramo": 1, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 1, "tramo": 2, "curso": "3ºESO-A", "asignatura": "Lengua Castellana", "aula": "B03", "libre": False},
            {"dia": 1, "tramo": 3, "curso": "1ºBACH-B", "asignatura": "Literatura", "aula": "B03", "libre": False},
            {"dia": 1, "tramo": 4, "curso": "4ºESO-C", "asignatura": "Lengua Castellana", "aula": "B03", "libre": False},
            # Miércoles
            {"dia": 2, "tramo": 1, "curso": "3ºESO-A", "asignatura": "Lengua Castellana", "aula": "B03", "libre": False},
            {"dia": 2, "tramo": 2, "curso": "1ºBACH-B", "asignatura": "Literatura", "aula": "B03", "libre": False},
            {"dia": 2, "tramo": 3, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 2, "tramo": 4, "curso": "4ºESO-C", "asignatura": "Lengua Castellana", "aula": "B03", "libre": False},
            # Jueves
            {"dia": 3, "tramo": 1, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 3, "tramo": 2, "curso": "3ºESO-A", "asignatura": "Lengua Castellana", "aula": "B03", "libre": False},
            {"dia": 3, "tramo": 3, "curso": "4ºESO-C", "asignatura": "Lengua Castellana", "aula": "B03", "libre": False},
            {"dia": 3, "tramo": 4, "curso": "1ºBACH-B", "asignatura": "Literatura", "aula": "B03", "libre": False},
            # Viernes
            {"dia": 4, "tramo": 1, "curso": "3ºESO-A", "asignatura": "Lengua Castellana", "aula": "B03", "libre": False},
            {"dia": 4, "tramo": 2, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 4, "tramo": 3, "curso": "4ºESO-C", "asignatura": "Lengua Castellana", "aula": "B03", "libre": False},
        ],
    },
    {
        "nombre": "Miren",
        "apellidos": "Aizpurua Goikoetxea",
        "email": "miren.aizpurua@ikastola.eus",
        "telefono": "688001003",
        "especialidades": ["Inglés"],
        "niveles": ["Primaria", "ESO"],
        "max_sustituciones_semana": 2,
        "notas": "Certificación Cambridge C2. Puede reforzar cualquier clase de ESO.",
        "horario": [
            # Lunes
            {"dia": 0, "tramo": 1, "curso": "1ºESO-A", "asignatura": "Inglés", "aula": "C05", "libre": False},
            {"dia": 0, "tramo": 2, "curso": "2ºESO-B", "asignatura": "Inglés", "aula": "C05", "libre": False},
            {"dia": 0, "tramo": 3, "curso": "3ºESO-B", "asignatura": "Inglés", "aula": "C05", "libre": False},
            {"dia": 0, "tramo": 4, "curso": None, "asignatura": None, "aula": None, "libre": True},
            # Martes
            {"dia": 1, "tramo": 1, "curso": "1ºESO-A", "asignatura": "Inglés", "aula": "C05", "libre": False},
            {"dia": 1, "tramo": 2, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 1, "tramo": 3, "curso": "2ºESO-B", "asignatura": "Inglés", "aula": "C05", "libre": False},
            {"dia": 1, "tramo": 4, "curso": "3ºESO-B", "asignatura": "Inglés", "aula": "C05", "libre": False},
            # Miércoles
            {"dia": 2, "tramo": 1, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 2, "tramo": 2, "curso": "1ºESO-A", "asignatura": "Inglés", "aula": "C05", "libre": False},
            {"dia": 2, "tramo": 3, "curso": "2ºESO-B", "asignatura": "Inglés", "aula": "C05", "libre": False},
            {"dia": 2, "tramo": 4, "curso": "3ºESO-B", "asignatura": "Inglés", "aula": "C05", "libre": False},
            # Jueves
            {"dia": 3, "tramo": 1, "curso": "1ºESO-A", "asignatura": "Inglés", "aula": "C05", "libre": False},
            {"dia": 3, "tramo": 2, "curso": "2ºESO-B", "asignatura": "Inglés", "aula": "C05", "libre": False},
            {"dia": 3, "tramo": 3, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 3, "tramo": 4, "curso": "3ºESO-B", "asignatura": "Inglés", "aula": "C05", "libre": False},
            # Viernes
            {"dia": 4, "tramo": 1, "curso": "1ºESO-A", "asignatura": "Inglés", "aula": "C05", "libre": False},
            {"dia": 4, "tramo": 2, "curso": "2ºESO-B", "asignatura": "Inglés", "aula": "C05", "libre": False},
            {"dia": 4, "tramo": 3, "curso": None, "asignatura": None, "aula": None, "libre": True},
        ],
    },
    {
        "nombre": "Iñaki",
        "apellidos": "Urrutia Beloki",
        "email": "inaki.urrutia@ikastola.eus",
        "telefono": "688001004",
        "especialidades": ["Historia", "Geografía", "Filosofía"],
        "niveles": ["ESO", "Bachillerato"],
        "max_sustituciones_semana": 3,
        "notas": "Muy polivalente, acepta cualquier guardia sin problema.",
        "horario": [
            # Lunes
            {"dia": 0, "tramo": 1, "curso": "4ºESO-A", "asignatura": "Historia", "aula": "B01", "libre": False},
            {"dia": 0, "tramo": 2, "curso": "1ºBACH-A", "asignatura": "Historia de España", "aula": "B01", "libre": False},
            {"dia": 0, "tramo": 3, "curso": "2ºESO-C", "asignatura": "Geografía", "aula": "B01", "libre": False},
            {"dia": 0, "tramo": 4, "curso": None, "asignatura": None, "aula": None, "libre": True},
            # Martes
            {"dia": 1, "tramo": 1, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 1, "tramo": 2, "curso": "4ºESO-A", "asignatura": "Historia", "aula": "B01", "libre": False},
            {"dia": 1, "tramo": 3, "curso": "2ºBACH-B", "asignatura": "Filosofía", "aula": "B02", "libre": False},
            {"dia": 1, "tramo": 4, "curso": "2ºESO-C", "asignatura": "Geografía", "aula": "B01", "libre": False},
            # Miércoles
            {"dia": 2, "tramo": 1, "curso": "1ºBACH-A", "asignatura": "Historia de España", "aula": "B01", "libre": False},
            {"dia": 2, "tramo": 2, "curso": "4ºESO-A", "asignatura": "Historia", "aula": "B01", "libre": False},
            {"dia": 2, "tramo": 3, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 2, "tramo": 4, "curso": "2ºBACH-B", "asignatura": "Filosofía", "aula": "B02", "libre": False},
            # Jueves
            {"dia": 3, "tramo": 1, "curso": "2ºESO-C", "asignatura": "Geografía", "aula": "B01", "libre": False},
            {"dia": 3, "tramo": 2, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 3, "tramo": 3, "curso": "4ºESO-A", "asignatura": "Historia", "aula": "B01", "libre": False},
            {"dia": 3, "tramo": 4, "curso": "1ºBACH-A", "asignatura": "Historia de España", "aula": "B01", "libre": False},
            # Viernes
            {"dia": 4, "tramo": 1, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 4, "tramo": 2, "curso": "2ºESO-C", "asignatura": "Geografía", "aula": "B01", "libre": False},
            {"dia": 4, "tramo": 3, "curso": "2ºBACH-B", "asignatura": "Filosofía", "aula": "B02", "libre": False},
        ],
    },
    {
        "nombre": "Leire",
        "apellidos": "Sarasola Iturriaga",
        "email": "leire.sarasola@ikastola.eus",
        "telefono": "688001005",
        "especialidades": ["Biología", "Química", "Ciencias Naturales"],
        "niveles": ["ESO", "Bachillerato"],
        "max_sustituciones_semana": 2,
        "notas": "Tutora de 3ºESO-A. Prefiere no hacer guardia en la hora del recreo (tramo 4).",
        "horario": [
            # Lunes
            {"dia": 0, "tramo": 1, "curso": "3ºESO-A", "asignatura": "Biología", "aula": "LAB1", "libre": False},
            {"dia": 0, "tramo": 2, "curso": "2ºBACH-B", "asignatura": "Química", "aula": "LAB1", "libre": False},
            {"dia": 0, "tramo": 3, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 0, "tramo": 4, "curso": "1ºESO-C", "asignatura": "Ciencias Naturales", "aula": "LAB1", "libre": False},
            # Martes
            {"dia": 1, "tramo": 1, "curso": "3ºESO-A", "asignatura": "Biología", "aula": "LAB1", "libre": False},
            {"dia": 1, "tramo": 2, "curso": "1ºESO-C", "asignatura": "Ciencias Naturales", "aula": "LAB1", "libre": False},
            {"dia": 1, "tramo": 3, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 1, "tramo": 4, "curso": "2ºBACH-B", "asignatura": "Química", "aula": "LAB1", "libre": False},
            # Miércoles
            {"dia": 2, "tramo": 1, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 2, "tramo": 2, "curso": "3ºESO-A", "asignatura": "Biología", "aula": "LAB1", "libre": False},
            {"dia": 2, "tramo": 3, "curso": "1ºESO-C", "asignatura": "Ciencias Naturales", "aula": "LAB1", "libre": False},
            {"dia": 2, "tramo": 4, "curso": "2ºBACH-B", "asignatura": "Química", "aula": "LAB1", "libre": False},
            # Jueves
            {"dia": 3, "tramo": 1, "curso": "2ºBACH-B", "asignatura": "Química", "aula": "LAB1", "libre": False},
            {"dia": 3, "tramo": 2, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 3, "tramo": 3, "curso": "3ºESO-A", "asignatura": "Biología", "aula": "LAB1", "libre": False},
            {"dia": 3, "tramo": 4, "curso": "1ºESO-C", "asignatura": "Ciencias Naturales", "aula": "LAB1", "libre": False},
            # Viernes
            {"dia": 4, "tramo": 1, "curso": "3ºESO-A", "asignatura": "Biología", "aula": "LAB1", "libre": False},
            {"dia": 4, "tramo": 2, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 4, "tramo": 3, "curso": "1ºESO-C", "asignatura": "Ciencias Naturales", "aula": "LAB1", "libre": False},
        ],
    },
    {
        "nombre": "Gorka",
        "apellidos": "Arrizabalaga Txoperena",
        "email": "gorka.arrizabalaga@ikastola.eus",
        "telefono": "688001006",
        "especialidades": ["Educación Física"],
        "niveles": ["ESO", "Bachillerato"],
        "max_sustituciones_semana": 4,
        "notas": "Gran disponibilidad para guardias. Conoce todos los grupos y el patio.",
        "horario": [
            # Lunes
            {"dia": 0, "tramo": 1, "curso": "1ºESO-A", "asignatura": "Educación Física", "aula": "GIM", "libre": False},
            {"dia": 0, "tramo": 2, "curso": "3ºESO-B", "asignatura": "Educación Física", "aula": "GIM", "libre": False},
            {"dia": 0, "tramo": 3, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 0, "tramo": 4, "curso": "2ºBACH-A", "asignatura": "Educación Física", "aula": "GIM", "libre": False},
            # Martes
            {"dia": 1, "tramo": 1, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 1, "tramo": 2, "curso": "1ºESO-A", "asignatura": "Educación Física", "aula": "GIM", "libre": False},
            {"dia": 1, "tramo": 3, "curso": "4ºESO-B", "asignatura": "Educación Física", "aula": "GIM", "libre": False},
            {"dia": 1, "tramo": 4, "curso": None, "asignatura": None, "aula": None, "libre": True},
            # Miércoles
            {"dia": 2, "tramo": 1, "curso": "3ºESO-B", "asignatura": "Educación Física", "aula": "GIM", "libre": False},
            {"dia": 2, "tramo": 2, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 2, "tramo": 3, "curso": "2ºBACH-A", "asignatura": "Educación Física", "aula": "GIM", "libre": False},
            {"dia": 2, "tramo": 4, "curso": "4ºESO-B", "asignatura": "Educación Física", "aula": "GIM", "libre": False},
            # Jueves
            {"dia": 3, "tramo": 1, "curso": "4ºESO-B", "asignatura": "Educación Física", "aula": "GIM", "libre": False},
            {"dia": 3, "tramo": 2, "curso": "3ºESO-B", "asignatura": "Educación Física", "aula": "GIM", "libre": False},
            {"dia": 3, "tramo": 3, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 3, "tramo": 4, "curso": "1ºESO-A", "asignatura": "Educación Física", "aula": "GIM", "libre": False},
            # Viernes
            {"dia": 4, "tramo": 1, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 4, "tramo": 2, "curso": "2ºBACH-A", "asignatura": "Educación Física", "aula": "GIM", "libre": False},
            {"dia": 4, "tramo": 3, "curso": "4ºESO-B", "asignatura": "Educación Física", "aula": "GIM", "libre": False},
        ],
    },
    {
        "nombre": "Ane",
        "apellidos": "Kortabarria Elola",
        "email": "ane.kortabarria@ikastola.eus",
        "telefono": "688001007",
        "especialidades": ["Tecnología", "Informática"],
        "niveles": ["ESO"],
        "max_sustituciones_semana": 2,
        "notas": "Responsable del aula de informática. Puede dar guardias en sala TIC.",
        "horario": [
            # Lunes
            {"dia": 0, "tramo": 1, "curso": "2ºESO-A", "asignatura": "Tecnología", "aula": "TIC1", "libre": False},
            {"dia": 0, "tramo": 2, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 0, "tramo": 3, "curso": "4ºESO-B", "asignatura": "Informática", "aula": "TIC1", "libre": False},
            {"dia": 0, "tramo": 4, "curso": "3ºESO-C", "asignatura": "Tecnología", "aula": "TIC1", "libre": False},
            # Martes
            {"dia": 1, "tramo": 1, "curso": "2ºESO-A", "asignatura": "Tecnología", "aula": "TIC1", "libre": False},
            {"dia": 1, "tramo": 2, "curso": "3ºESO-C", "asignatura": "Tecnología", "aula": "TIC1", "libre": False},
            {"dia": 1, "tramo": 3, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 1, "tramo": 4, "curso": "4ºESO-B", "asignatura": "Informática", "aula": "TIC1", "libre": False},
            # Miércoles
            {"dia": 2, "tramo": 1, "curso": "4ºESO-B", "asignatura": "Informática", "aula": "TIC1", "libre": False},
            {"dia": 2, "tramo": 2, "curso": "2ºESO-A", "asignatura": "Tecnología", "aula": "TIC1", "libre": False},
            {"dia": 2, "tramo": 3, "curso": "3ºESO-C", "asignatura": "Tecnología", "aula": "TIC1", "libre": False},
            {"dia": 2, "tramo": 4, "curso": None, "asignatura": None, "aula": None, "libre": True},
            # Jueves
            {"dia": 3, "tramo": 1, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 3, "tramo": 2, "curso": "4ºESO-B", "asignatura": "Informática", "aula": "TIC1", "libre": False},
            {"dia": 3, "tramo": 3, "curso": "2ºESO-A", "asignatura": "Tecnología", "aula": "TIC1", "libre": False},
            {"dia": 3, "tramo": 4, "curso": "3ºESO-C", "asignatura": "Tecnología", "aula": "TIC1", "libre": False},
            # Viernes
            {"dia": 4, "tramo": 1, "curso": "3ºESO-C", "asignatura": "Tecnología", "aula": "TIC1", "libre": False},
            {"dia": 4, "tramo": 2, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 4, "tramo": 3, "curso": "2ºESO-A", "asignatura": "Tecnología", "aula": "TIC1", "libre": False},
        ],
    },
    {
        "nombre": "Xabier",
        "apellidos": "Galdos Irastorza",
        "email": "xabier.galdos@ikastola.eus",
        "telefono": "688001008",
        "especialidades": ["Música", "Arte"],
        "niveles": ["ESO"],
        "max_sustituciones_semana": 3,
        "notas": "Director del coro del centro. Flexible con horario de guardias.",
        "horario": [
            # Lunes
            {"dia": 0, "tramo": 1, "curso": "1ºESO-B", "asignatura": "Música", "aula": "MUS", "libre": False},
            {"dia": 0, "tramo": 2, "curso": "3ºESO-A", "asignatura": "Arte", "aula": "MUS", "libre": False},
            {"dia": 0, "tramo": 3, "curso": "2ºESO-B", "asignatura": "Música", "aula": "MUS", "libre": False},
            {"dia": 0, "tramo": 4, "curso": None, "asignatura": None, "aula": None, "libre": True},
            # Martes
            {"dia": 1, "tramo": 1, "curso": "2ºESO-B", "asignatura": "Música", "aula": "MUS", "libre": False},
            {"dia": 1, "tramo": 2, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 1, "tramo": 3, "curso": "1ºESO-B", "asignatura": "Música", "aula": "MUS", "libre": False},
            {"dia": 1, "tramo": 4, "curso": "3ºESO-A", "asignatura": "Arte", "aula": "MUS", "libre": False},
            # Miércoles
            {"dia": 2, "tramo": 1, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 2, "tramo": 2, "curso": "1ºESO-B", "asignatura": "Música", "aula": "MUS", "libre": False},
            {"dia": 2, "tramo": 3, "curso": "2ºESO-B", "asignatura": "Música", "aula": "MUS", "libre": False},
            {"dia": 2, "tramo": 4, "curso": "3ºESO-A", "asignatura": "Arte", "aula": "MUS", "libre": False},
            # Jueves
            {"dia": 3, "tramo": 1, "curso": "3ºESO-A", "asignatura": "Arte", "aula": "MUS", "libre": False},
            {"dia": 3, "tramo": 2, "curso": "2ºESO-B", "asignatura": "Música", "aula": "MUS", "libre": False},
            {"dia": 3, "tramo": 3, "curso": None, "asignatura": None, "aula": None, "libre": True},
            {"dia": 3, "tramo": 4, "curso": "1ºESO-B", "asignatura": "Música", "aula": "MUS", "libre": False},
            # Viernes
            {"dia": 4, "tramo": 1, "curso": "1ºESO-B", "asignatura": "Música", "aula": "MUS", "libre": False},
            {"dia": 4, "tramo": 2, "curso": "3ºESO-A", "asignatura": "Arte", "aula": "MUS", "libre": False},
            {"dia": 4, "tramo": 3, "curso": None, "asignatura": None, "aula": None, "libre": True},
        ],
    },
]


async def seed_teachers() -> None:
    async with AsyncSessionLocal() as db:
        added = 0
        skipped = 0
        for t_data in TEACHERS:
            # Evitar duplicados por email
            from sqlalchemy import select
            result = await db.execute(select(Teacher).where(Teacher.email == t_data["email"]))
            existing = result.scalar_one_or_none()
            if existing:
                print(f"  ⚠ Ya existe: {t_data['email']} — omitido")
                skipped += 1
                continue

            teacher = Teacher(
                nombre=t_data["nombre"],
                apellidos=t_data["apellidos"],
                email=t_data["email"],
                telefono=t_data.get("telefono"),
                especialidades=t_data["especialidades"],
                niveles=t_data["niveles"],
                max_sustituciones_semana=t_data.get("max_sustituciones_semana", 2),
                activo=True,
                notas=t_data.get("notas"),
            )
            db.add(teacher)
            await db.flush()  # obtener teacher.id

            for h in t_data["horario"]:
                slot = Schedule(
                    teacher_id=teacher.id,
                    dia_semana=h["dia"],
                    tramo_horario=h["tramo"],
                    curso=h.get("curso"),
                    asignatura=h.get("asignatura"),
                    aula=h.get("aula"),
                    es_libre=h["libre"],
                )
                db.add(slot)

            print(f"  ✓ {teacher.nombre} {teacher.apellidos} ({len(t_data['horario'])} tramos)")
            added += 1

        await db.commit()
        print(f"\nResultado: {added} profesores añadidos, {skipped} omitidos.")


if __name__ == "__main__":
    asyncio.run(seed_teachers())
