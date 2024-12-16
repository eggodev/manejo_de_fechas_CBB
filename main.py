from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

app = FastAPI()

# Constantes globales
horarioAtencion = (9, 17)  # Horario de atención (9:00 a 17:00)
duracionCita = 30  # Duración de la cita en minutos
tiempoEspera = 60  # Tiempo de espera en minutos

# Modelo de entrada
class Cita(BaseModel):
    startTime: Optional[str]  # Puede ser una fecha en formato ISO o null

# Modelo de salida
class FechaDisponible(BaseModel):
    fechaDisponible: str  # Fechas disponibles en formato amigable

@app.post("/obtener-fechas-disponibles", response_model=List[FechaDisponible])
async def obtener_fechas_disponibles(citas: List[Cita]):
    # Paso 1: Almacenar el JSON en citas_ya_agendadas
    citas_ya_agendadas = [
        datetime.fromisoformat(cita.startTime).date()  # Solo usamos la fecha, sin la hora
        for cita in citas 
        if cita.startTime is not None
    ]
    
    # Si no hay citas agendadas (todos son null)
    if not citas_ya_agendadas:
        fechas_disponibles = _buscar_fechas_disponibles()
        return [{"fechaDisponible": _formatear_fecha(fecha)} for fecha in fechas_disponibles]
    
    # Paso 2: Ordenar las fechas en formato ISO UTC de menor a mayor
    citas_ya_agendadas.sort()

    # Paso 3 y 4: Buscar las siguientes 5 fechas disponibles
    fechas_disponibles = _buscar_fechas_disponibles(citas_ya_agendadas)
    
    # Convertir las fechas disponibles a un formato amigable
    return [{"fechaDisponible": _formatear_fecha(fecha)} for fecha in fechas_disponibles]

# Función para buscar fechas disponibles
def _buscar_fechas_disponibles(citas_ya_agendadas=None):
    """
    Encuentra las próximas 5 fechas disponibles, priorizando lunes y miércoles,
    y evitando conflictos con citas ya agendadas.
    
    Args:
        citas_ya_agendadas (list): Lista de objetos datetime con las fechas ya ocupadas.

    Returns:
        list: Lista de objetos datetime con las fechas disponibles.
    """
    # Inicializamos variables
    fechas_disponibles = []  # Almacenará las fechas disponibles
    hoy = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).date()  # Solo usamos la fecha
    dia_actual = hoy

    # Set para acceso rápido a citas agendadas, usando solo la fecha
    citas_ocupadas = set(citas_ya_agendadas) if citas_ya_agendadas else set()

    # Recorremos los días hasta encontrar 5 fechas disponibles
    while len(fechas_disponibles) < 5:
        # Determinar si el día actual es lunes o miércoles
        if dia_actual.weekday() in [0, 2]:  # 0 = lunes, 2 = miércoles
            # Filtro adicional para la fecha de hoy
            if dia_actual == hoy:
                if not _es_fecha_disponible_hoy():
                    dia_actual += timedelta(days=1)
                    continue
            # Si no está ocupado, añadir a fechas disponibles
            if dia_actual not in citas_ocupadas:
                fechas_disponibles.append(dia_actual)
        # Avanzar al siguiente día
        dia_actual += timedelta(days=1)

    return fechas_disponibles

# Función para verificar si la fecha de hoy es válida
def _es_fecha_disponible_hoy():
    """
    Verifica si la fecha de hoy es válida considerando el horario de atención,
    la duración de la cita y el tiempo de espera.

    Returns:
        bool: True si la fecha de hoy es válida, False si no lo es.
    """
    ahora = datetime.utcnow()
    hora_actual = ahora.hour + ahora.minute / 60  # Hora actual en formato decimal
    inicio_atencion, fin_atencion = horarioAtencion

    # Calcular el tiempo restante del día dentro del horario de atención
    tiempo_restante = fin_atencion - hora_actual

    # Verificar si hay suficiente tiempo para una cita
    tiempo_necesario = duracionCita / 60 + tiempoEspera / 60  # En horas
    return tiempo_restante >= tiempo_necesario and hora_actual < fin_atencion

# Función para formatear la fecha de manera amigable
def _formatear_fecha(fecha):
    """
    Convierte una fecha en formato "Lunes 30 de Diciembre".
    
    Args:
        fecha (datetime.date): Fecha a formatear.
    
    Returns:
        str: Fecha en formato amigable.
    """
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    dia_semana = dias_semana[fecha.weekday()]
    dia = fecha.day
    mes = meses[fecha.month - 1]
    return f"{dia_semana} {dia} de {mes}"
