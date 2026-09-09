"""
Servidor Mimolove - Fase 2
Muestra el formulario y, al enviarlo, genera la página de amor
usando el motor de la Fase 1 (generador/generar.py).
"""
import os
import re
import sys
import uuid
from datetime import datetime

from flask import Flask, request, render_template, send_from_directory, abort

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "generator"))
from generar import generar_pagina  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
TEMPLATE_DIR = os.path.join(BASE_DIR, "generator")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB por request


def slugify(texto):
    texto = texto.lower().strip()
    texto = re.sub(r"[áàä]", "a", texto)
    texto = re.sub(r"[éèë]", "e", texto)
    texto = re.sub(r"[íìï]", "i", texto)
    texto = re.sub(r"[óòö]", "o", texto)
    texto = re.sub(r"[úùü]", "u", texto)
    texto = re.sub(r"[ñ]", "n", texto)
    texto = re.sub(r"[^a-z0-9]+", "-", texto).strip("-")
    return texto or "pagina"


def extraer_youtube_id(url):
    if not url:
        return None
    match = re.search(r"(?:youtu\.be/|v=|embed/)([A-Za-z0-9_-]{11})", url)
    return match.group(1) if match else None


def parrafos_desde_texto(texto):
    bloques = re.split(r"\n\s*\n", texto.strip())
    return [b.strip().replace("\n", " ") for b in bloques if b.strip()]


@app.route("/")
def formulario():
    return render_template("formulario.html")


@app.route("/generar", methods=["POST"])
def generar():
    f = request.form

    nombre1 = f.get("nombre1", "").strip()
    nombre2 = f.get("nombre2", "").strip()
    apodo = f.get("apodo", "").strip() or None
    fecha_str = f.get("fecha_inicio", "")
    carta_raw = f.get("carta", "")
    firma_carta = f.get("firma_carta", "").strip() or None
    youtube_url = f.get("youtube_url", "").strip()
    cupon_texto = f.get("cupon_texto", "").strip() or None
    paleta = f.get("paleta", "rosa")
    if paleta not in ("rosa", "nocturno", "dorado"):
        paleta = "rosa"

    planes = [p.strip() for p in f.getlist("plan") if p.strip()]
    amores = [a.strip() for a in f.getlist("amo") if a.strip()]

    if not nombre1 or not nombre2 or not fecha_str or not carta_raw:
        return "Faltan campos obligatorios. Vuelve atrás y complétalos.", 400

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    except ValueError:
        return "Fecha inválida.", 400

    # ---- Procesar fotos subidas ----
    slug_base = slugify(f"{nombre1}-y-{nombre2}")
    slug = f"{slug_base}-{uuid.uuid4().hex[:6]}"
    carpeta_fotos = os.path.join(UPLOAD_DIR, slug)
    os.makedirs(carpeta_fotos, exist_ok=True)

    archivos = request.files.getlist("fotos")
    captions = request.form.getlist("captions")
    fotos_paths = []
    for i, archivo in enumerate(archivos):
        if archivo and archivo.filename:
            ext = os.path.splitext(archivo.filename)[1] or ".jpg"
            ruta = os.path.join(carpeta_fotos, f"foto{i+1}{ext}")
            archivo.save(ruta)
            caption = captions[i].strip() if i < len(captions) and captions[i].strip() else None
            fotos_paths.append((ruta, caption))

    if not fotos_paths:
        return "Debes subir al menos una foto.", 400

    datos = {
        "nombre1": nombre1,
        "nombre2": nombre2,
        "apodo": apodo,
        "anio": fecha.year,
        "mes_idx": fecha.month - 1,
        "dia": fecha.day,
        "carta_parrafos": parrafos_desde_texto(carta_raw),
        "firma_carta": firma_carta,
        "lista_planes": planes,
        "lista_amo": amores,
        "youtube_id": extraer_youtube_id(youtube_url),
        "cupon_texto": cupon_texto,
        "mensaje_cierre": "Te amo.",
        "paleta": paleta,
    }

    salida = os.path.join(GENERATED_DIR, f"{slug}.html")
    generar_pagina(datos, fotos_paths, salida, template_dir=TEMPLATE_DIR)

    link = f"/p/{slug}"
    return f"""
    <!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>¡Lista tu página!</title>
    <style>
      body{{font-family:'Cormorant Garamond',serif;background:#fbf1ea;color:#3a1f1f;
           text-align:center;padding:60px 20px;}}
      a.btn{{display:inline-block;margin-top:20px;background:#7c2b3f;color:#fff;
           padding:14px 30px;border-radius:30px;text-decoration:none;font-size:18px;}}
    </style></head><body>
      <h1>¡Tu página está lista! ❤️</h1>
      <p>Puedes verla y compartirla desde este link:</p>
      <a class="btn" href="{link}" target="_blank">Ver mi página</a>
    </body></html>
    """


@app.route("/p/<slug>")
def ver_pagina(slug):
    ruta = os.path.join(GENERATED_DIR, f"{slug}.html")
    if not os.path.exists(ruta):
        abort(404)
    return send_from_directory(GENERATED_DIR, f"{slug}.html")


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    modo_debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=modo_debug, host="0.0.0.0", port=puerto)
