from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from babel.dates import format_date

app = FastAPI()
security = HTTPBasic()

# Modelo de entrada
class Cita(BaseModel):
    startTime: Optional[str]  # Puede ser una fecha en formato ISO o null

# Modelo de salida
class FechaDisponible(BaseModel):
    fechaDisponible: str  # Fechas disponibles en formato amigable

# Función para verificar credenciales
def verificar_credenciales(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = "usuario"  # Cambia esto por tu nombre de usuario
    correct_password = "contraseña"  # Cambia esto por tu contraseña

    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas",
        )
    return credentials

@app.post("/obtener-fechas-disponibles", response_model=List[FechaDisponible])
async def obtener_fechas_disponibles(citas: List[Cita], credentials: HTTPBasicCredentials = Depends(verificar_credenciales)):
    # Paso 1: Almacenar el JSON en citas_ya_agendadas
    citas_ya_agendadas = [
        datetime.fromisoformat(cita.startTime).date()  # Solo usamos la fecha, sin la hora
        for cita in citas 
        if cita.startTime is not None
    ]
    
    # Si no hay citas agendadas (todos son null)
    if not citas_ya_agendadas:
        return _buscar_fechas_disponibles()
    
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
            # Si no está ocupado, añadir a fechas disponibles
            if dia_actual not in citas_ocupadas:
                fechas_disponibles.append(dia_actual)
        # Avanzar al siguiente día
        dia_actual += timedelta(days=1)

    return fechas_disponibles

# Función para formatear la fecha de manera amigable
def _formatear_fecha(fecha):
    """
    Convierte una fecha en formato "Lunes 30 de Diciembre".
    
    Args:
        fecha (datetime.date): Fecha a formatear.
    
    Returns:
        str: Fecha en formato amigable.
    """
    return format_date(fecha, "EEEE d 'de' MMMM", locale='es')
