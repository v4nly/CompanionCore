from flask import Flask, render_template, request, jsonify
import os
import json
import re
from ai_providers import obtener_proveedor_ia

app = Flask(__name__)
ai_provider = obtener_proveedor_ia()

# Archivo donde se guardará el historial de chat automáticamente
HISTORY_FILE = "chat_history.json"

def load_history():
    """Carga el historial de chat desde el archivo JSON si existe."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    """Guarda la lista completa de mensajes en el archivo JSON."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

sesion_activa = {
    "personaje_data": None,
    "afecto_actual": 0
}

# Cargamos el historial en memoria al arrancar la app
chat_history = load_history()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/personajes", methods=["GET"])
def listar_personajes():
    if not os.path.exists("characters"):
        return jsonify([])
    archivos = [f.replace(".json", "") for f in os.listdir("characters") if f.endswith(".json")]
    return jsonify(archivos)

@app.route("/api/cargar_personaje", methods=["POST"])
def cargar_personaje():
    nombre_archivo = request.json.get("personaje")
    ruta = os.path.join("characters", f"{nombre_archivo}.json")
    
    if not os.path.exists(ruta):
        return jsonify({"error": "Personaje no encontrado"}), 404
        
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    sesion_activa["personaje_data"] = data
    sesion_activa["afecto_actual"] = data.get("initial_affection", 0)
    
    return jsonify({
        "status": "ok", 
        "name": data["name"],
        "initial_emotion": "normal"
    })

@app.route("/chat", methods=["POST"])
def chat():
    if not sesion_activa["personaje_data"]:
        return jsonify({"error": "Ningún personaje seleccionado"}), 400
        
    user_input = request.json.get("message", "")
    char = sesion_activa["personaje_data"]
    
    prompt_completo = f"{char['system_prompt']}\n\n[ESTADO ACTUAL DE AFECTO: {sesion_activa['afecto_actual']}]\nUsuario: {user_input}\n{char['name']}:"

    try:
        respuesta_ia = ai_provider.generar_respuesta(prompt_completo)
    except Exception as e:
        return jsonify({"error": f"Error conectando con la IA: {str(e)}"}), 500

    match = re.search(r"\[(.*?)\]\s*\[affection:\s*(\d+)\]", respuesta_ia)
    emocion = "normal"
    
    if match:
        emocion = match.group(1)
        sesion_activa["afecto_actual"] = int(match.group(2))
    
    # Limpieza total de comandos extraños que repita la IA
    mensaje_limpio = re.sub(r"\[.*?\]", "", respuesta_ia).strip()

    # --- NUEVO: GUARDAR MENSAJES AUTOMÁTICAMENTE ---
    chat_history.append({"sender": "user", "text": user_input})
    chat_history.append({"sender": "bot", "text": mensaje_limpio, "emotion": emocion, "character": char["name"]})
    save_history(chat_history)
    # ---------------------------------------------

    return jsonify({
        "response": mensaje_limpio,
        "emotion": emocion
    })

# --- NUEVO: RUTA PARA CARGAR EL HISTORIAL EN LA VISTA ---
@app.route("/api/get_history", methods=["GET"])
def get_history():
    return jsonify(chat_history)
# -------------------------------------------------------

@app.route("/minijuego_ganado", methods=["POST"])
def minijuego_ganado():
    puntos = request.json.get("puntos", 5)
    sesion_activa["afecto_actual"] = min(100, sesion_activa["afecto_actual"] + puntos)
    return jsonify({"status": "ok"})

@app.route('/api/sprites_disponibles')
def sprites_disponibles():
    carpeta_sprites = os.path.join('static', 'sprites')
    try:
        archivos = os.listdir(carpeta_sprites)
        sprites = [f for f in archivos if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    except FileNotFoundError:
        sprites = []
    return jsonify(sprites)

if __name__ == "__main__":
    app.run(debug=True, port=8000)