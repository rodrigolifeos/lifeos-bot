"""
Servicio de Claude AI — Interpreta mensajes y extrae datos estructurados
"""
import os
import json
import anthropic
from datetime import datetime

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Sos el asistente de Life OS, un sistema de vida cuantificada.
Tu trabajo es interpretar mensajes en lenguaje natural (en español argentino) y extraer datos estructurados.

Tenés que devolver SIEMPRE un JSON con esta estructura:
{
  "tipo": "comida" | "gasto" | "entrenamiento" | "tarea" | "evento_calendario" | "consulta" | "desconocido",
  "datos": { ... campos específicos según el tipo },
  "respuesta": "mensaje amigable para el usuario (en español argentino, máximo 2 líneas)"
}

Campos según tipo:

COMIDA:
{
  "tipo": "comida",
  "datos": {
    "descripcion": "nombre del alimento",
    "calorias_estimadas": número (estimá si no se especifica),
    "proteinas_g": número,
    "carbohidratos_g": número,
    "grasas_g": número,
    "momento": "desayuno" | "almuerzo" | "merienda" | "cena" | "snack"
  }
}

GASTO:
{
  "tipo": "gasto",
  "datos": {
    "descripcion": "descripción del gasto",
    "monto": número en pesos,
    "categoria": "comida" | "transporte" | "entretenimiento" | "salud" | "ropa" | "servicios" | "negocio" | "otro"
  }
}

ENTRENAMIENTO:
{
  "tipo": "entrenamiento",
  "datos": {
    "ejercicio": "nombre del ejercicio",
    "series": número o null,
    "repeticiones": número o null,
    "peso_kg": número o null,
    "duracion_min": número o null,
    "notas": "observaciones adicionales"
  }
}

TAREA:
{
  "tipo": "tarea",
  "datos": {
    "titulo": "título de la tarea",
    "prioridad": "alta" | "media" | "baja",
    "completada": false
  }
}

EVENTO_CALENDARIO:
{
  "tipo": "evento_calendario",
  "datos": {
    "titulo": "título del evento",
    "fecha_hora": "ISO 8601 o descripción como 'mañana a las 10'",
    "duracion_min": número,
    "notas": "descripción adicional"
  }
}

CONSULTA (el usuario pide información, no registrar algo):
{
  "tipo": "consulta",
  "datos": { "subtipo": "resumen" | "consejo" | "motivacion" | "otro" },
  "respuesta": "..."
}

Ejemplos de mensajes y su interpretación:
- "comí milanesa con ensalada" → tipo comida, estimá calorías razonablemente
- "gasté 3500 en nafta" → tipo gasto, categoría transporte
- "hice 4x10 press de banca con 60kg" → tipo entrenamiento
- "mañana a las 10 reunión con el contador" → tipo evento_calendario
- "no me dan ganas de laburar" → tipo consulta, subtipo motivacion, respondé con algo motivador

Fecha y hora actual: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """

Respondé SOLO con el JSON, sin texto adicional, sin markdown."""


def interpretar_mensaje(mensaje: str, historial: list = None) -> dict:
    """
    Interpreta un mensaje del usuario y retorna un dict con tipo, datos y respuesta.
    """
    mensajes = []
    
    if historial:
        mensajes.extend(historial[-4:])  # últimos 2 intercambios para contexto
    
    mensajes.append({"role": "user", "content": mensaje})
    
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=mensajes
    )
    
    texto = response.content[0].text.strip()
    
    # Limpiar markdown si Claude lo puso igual
    if texto.startswith("```"):
        texto = texto.split("```")[1]
        if texto.startswith("json"):
            texto = texto[4:]
    
    return json.loads(texto)


def generar_resumen_dia(datos_dia: dict) -> str:
    """
    Genera un resumen narrativo del día con los datos registrados.
    """
    prompt = f"""
Sos el asistente de Life OS. Generá un resumen motivador del día del usuario en español argentino.
Datos del día:
{json.dumps(datos_dia, ensure_ascii=False, indent=2)}

El resumen tiene que:
- Ser amigable y motivador, máximo 5 líneas
- Mencionar lo que hizo bien
- Dar un consejo o reflexión para mañana
- Incluir el Life Score calculado (0-100) basado en: comidas registradas (25pts), entrenamiento (25pts), gastos dentro del rango (25pts), tareas completadas (25pts)
"""
    
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text.strip()


def calcular_life_score(datos_dia: dict) -> int:
    """
    Calcula el Life Score del día (0-100).
    """
    score = 0
    
    # Comidas (25 pts) — al menos 3 registros
    comidas = datos_dia.get("comidas", [])
    score += min(25, len(comidas) * 8)
    
    # Entrenamiento (25 pts) — al menos 1 sesión
    entrenamientos = datos_dia.get("entrenamientos", [])
    score += 25 if len(entrenamientos) > 0 else 0
    
    # Gastos (25 pts) — si registró al menos 1 gasto
    gastos = datos_dia.get("gastos", [])
    score += min(25, len(gastos) * 12) if gastos else 0
    
    # Tareas (25 pts) — tareas completadas
    tareas = datos_dia.get("tareas", [])
    completadas = sum(1 for t in tareas if t.get("completada"))
    total_tareas = len(tareas)
    if total_tareas > 0:
        score += int(25 * (completadas / total_tareas))
    
    return min(100, score)
