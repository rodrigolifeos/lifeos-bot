"""
Servicio de base de datos — Supabase
"""
import os
from supabase import create_client, Client
from datetime import datetime, date

_client: Client = None

def get_db() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Faltan SUPABASE_URL y SUPABASE_KEY en el .env")
        _client = create_client(url, key)
    return _client


# ─────────────── COMIDAS ───────────────

def guardar_comida(user_id: int, datos: dict) -> dict:
    db = get_db()
    registro = {
        "user_id": str(user_id),
        "descripcion": datos.get("descripcion"),
        "calorias_estimadas": datos.get("calorias_estimadas"),
        "proteinas_g": datos.get("proteinas_g"),
        "carbohidratos_g": datos.get("carbohidratos_g"),
        "grasas_g": datos.get("grasas_g"),
        "momento": datos.get("momento"),
        "fecha": date.today().isoformat(),
        "created_at": datetime.now().isoformat()
    }
    result = db.table("comidas").insert(registro).execute()
    return result.data[0] if result.data else {}

def obtener_comidas_hoy(user_id: int) -> list:
    db = get_db()
    result = db.table("comidas") \
        .select("*") \
        .eq("user_id", str(user_id)) \
        .eq("fecha", date.today().isoformat()) \
        .execute()
    return result.data or []


# ─────────────── GASTOS ───────────────

def guardar_gasto(user_id: int, datos: dict) -> dict:
    db = get_db()
    registro = {
        "user_id": str(user_id),
        "descripcion": datos.get("descripcion"),
        "monto": datos.get("monto"),
        "categoria": datos.get("categoria"),
        "fecha": date.today().isoformat(),
        "created_at": datetime.now().isoformat()
    }
    result = db.table("gastos").insert(registro).execute()
    return result.data[0] if result.data else {}

def obtener_gastos_semana(user_id: int) -> list:
    from datetime import timedelta
    db = get_db()
    hace_7_dias = (date.today() - timedelta(days=7)).isoformat()
    result = db.table("gastos") \
        .select("*") \
        .eq("user_id", str(user_id)) \
        .gte("fecha", hace_7_dias) \
        .order("fecha", desc=True) \
        .execute()
    return result.data or []

def obtener_gastos_hoy(user_id: int) -> list:
    db = get_db()
    result = db.table("gastos") \
        .select("*") \
        .eq("user_id", str(user_id)) \
        .eq("fecha", date.today().isoformat()) \
        .execute()
    return result.data or []


# ─────────────── ENTRENAMIENTOS ───────────────

def guardar_entrenamiento(user_id: int, datos: dict) -> dict:
    db = get_db()
    registro = {
        "user_id": str(user_id),
        "ejercicio": datos.get("ejercicio"),
        "series": datos.get("series"),
        "repeticiones": datos.get("repeticiones"),
        "peso_kg": datos.get("peso_kg"),
        "duracion_min": datos.get("duracion_min"),
        "notas": datos.get("notas"),
        "fecha": date.today().isoformat(),
        "created_at": datetime.now().isoformat()
    }
    result = db.table("entrenamientos").insert(registro).execute()
    return result.data[0] if result.data else {}

def obtener_entrenamientos_hoy(user_id: int) -> list:
    db = get_db()
    result = db.table("entrenamientos") \
        .select("*") \
        .eq("user_id", str(user_id)) \
        .eq("fecha", date.today().isoformat()) \
        .execute()
    return result.data or []


# ─────────────── TAREAS ───────────────

def guardar_tarea(user_id: int, datos: dict) -> dict:
    db = get_db()
    registro = {
        "user_id": str(user_id),
        "titulo": datos.get("titulo"),
        "prioridad": datos.get("prioridad", "media"),
        "completada": False,
        "fecha": date.today().isoformat(),
        "created_at": datetime.now().isoformat()
    }
    result = db.table("tareas").insert(registro).execute()
    return result.data[0] if result.data else {}

def obtener_tareas_hoy(user_id: int) -> list:
    db = get_db()
    result = db.table("tareas") \
        .select("*") \
        .eq("user_id", str(user_id)) \
        .eq("fecha", date.today().isoformat()) \
        .execute()
    return result.data or []

def completar_tarea(tarea_id: str) -> bool:
    db = get_db()
    result = db.table("tareas") \
        .update({"completada": True}) \
        .eq("id", tarea_id) \
        .execute()
    return len(result.data) > 0


# ─────────────── DATOS DEL DÍA (para Life Score) ───────────────

def obtener_datos_dia(user_id: int) -> dict:
    return {
        "comidas": obtener_comidas_hoy(user_id),
        "gastos": obtener_gastos_hoy(user_id),
        "entrenamientos": obtener_entrenamientos_hoy(user_id),
        "tareas": obtener_tareas_hoy(user_id)
    }
