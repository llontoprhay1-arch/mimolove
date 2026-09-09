"""
Generador de páginas Mimolove.
Toma un diccionario de datos del cliente + fotos, y produce un archivo
HTML final autocontenido (con las fotos incrustadas en base64).
"""
import base64
import os
from jinja2 import Environment, FileSystemLoader

MESES_ES = ["enero","febrero","marzo","abril","mayo","junio",
            "julio","agosto","septiembre","octubre","noviembre","diciembre"]

PALETAS = {
    "rosa": {
        "paper": "#fbf1ea", "paper_deep": "#f4e3d8", "ink": "#3a1f1f",
        "wine": "#7c2b3f", "wine_deep": "#571d2c", "rose": "#c9647a", "gold": "#b98a4a",
        "line": "rgba(58,31,31,.18)",
        "rueda": ["'#7c2b3f'", "'#c9647a'", "'#b98a4a'", "'#9c3b52'", "'#e0a5b3'"],
    },
    "nocturno": {
        "paper": "#f2f0f6", "paper_deep": "#e4e0ee", "ink": "#20203a",
        "wine": "#2f3577", "wine_deep": "#1b1e4a", "rose": "#6d74c9", "gold": "#8f8fd6",
        "line": "rgba(32,32,58,.18)",
        "rueda": ["'#2f3577'", "'#6d74c9'", "'#8f8fd6'", "'#4a4f9e'", "'#b5b8e6'"],
    },
    "dorado": {
        "paper": "#faf6ec", "paper_deep": "#f0e6cd", "ink": "#3a2f1f",
        "wine": "#8a6a1f", "wine_deep": "#5c4712", "rose": "#c9a24a", "gold": "#e0c068",
        "line": "rgba(58,47,31,.18)",
        "rueda": ["'#8a6a1f'", "'#c9a24a'", "'#e0c068'", "'#a8822c'", "'#e8d6a0'"],
    },
}


def foto_a_base64(path, max_dim=1000, calidad=78):
    """Redimensiona y convierte una foto a base64 (JPEG)."""
    from PIL import Image, ImageOps
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    w, h = img.size
    scale = max_dim / max(w, h)
    if scale < 1:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    import io
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=calidad, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def calcular_tiempo_texto(anio, mes_idx, dia):
    """Calcula un texto tipo '3 años, 5 meses y 26 días' desde la fecha dada hasta hoy."""
    from datetime import date
    inicio = date(anio, mes_idx + 1, dia)
    hoy = date.today()

    years = hoy.year - inicio.year
    months = hoy.month - inicio.month
    days = hoy.day - inicio.day
    if days < 0:
        months -= 1
        # días del mes anterior
        prev_month = hoy.month - 1 or 12
        prev_year = hoy.year if hoy.month > 1 else hoy.year - 1
        from calendar import monthrange
        days += monthrange(prev_year, prev_month)[1]
    if months < 0:
        years -= 1
        months += 12

    partes = []
    if years > 0:
        partes.append(f"{years} año{'s' if years != 1 else ''}")
    if months > 0:
        partes.append(f"{months} mes{'es' if months != 1 else ''}")
    if days > 0 or not partes:
        partes.append(f"{days} día{'s' if days != 1 else ''}")

    if len(partes) == 1:
        return partes[0]
    return ", ".join(partes[:-1]) + " y " + partes[-1]


def generar_pagina(datos, fotos_paths, output_path, template_dir=".", template_name="mimolove_template.html.j2"):
    """
    datos: dict con las llaves:
      nombre1, nombre2, apodo (opcional),
      anio, mes_idx (0-11), dia,
      carta_parrafos (lista de strings), firma_carta (opcional),
      lista_planes (lista de strings), lista_amo (lista de strings),
      youtube_id (opcional), cupon_texto (opcional),
      mensaje_cierre (opcional)
    fotos_paths: lista de tuplas (ruta_archivo, caption_opcional)
    output_path: dónde guardar el HTML final
    """
    env = Environment(loader=FileSystemLoader(template_dir))
    tpl = env.get_template(template_name)

    fotos = []
    for item in fotos_paths:
        if isinstance(item, tuple):
            path, caption = item
        else:
            path, caption = item, None
        fotos.append({"base64": foto_a_base64(path), "caption": caption})

    fecha_texto = f"{datos['dia']} de {MESES_ES[datos['mes_idx']]}, {datos['anio']}"
    tiempo_texto = calcular_tiempo_texto(datos['anio'], datos['mes_idx'], datos['dia'])

    contexto = {
        **datos,
        "fecha_texto": fecha_texto,
        "tiempo_texto": tiempo_texto,
        "fotos": fotos,
        "colores": PALETAS.get(datos.get("paleta", "rosa"), PALETAS["rosa"]),
    }

    html = tpl.render(**contexto)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


if __name__ == "__main__":
    # ---- PRUEBA: recreamos la página de Rhay & Gianeylla con el generador ----
    datos_prueba = {
        "nombre1": "Rhay",
        "nombre2": "Gianeylla",
        "apodo": "Giany",
        "anio": 2023,
        "mes_idx": 2,  # marzo (0-indexado)
        "dia": 13,
        "carta_parrafos": [
            "Para mi Giany, el amor de mi vida ❤️",
            "Hoy cumplimos 3 años y 6 meses, y no puedo evitar sonreír mientras pienso en todo lo que hemos vivido juntos. Parece increíble cuánto tiempo ha pasado, pero lo más bonito es que todavía siento esa felicidad cuando estoy contigo, esa sensación de que no necesito nada más que tenerte a mi lado.",
            "Este mes ha sido muy especial para mí. Hemos tenido momentos más tranquilos, muchas risas, juegos, paseos, conversaciones y esas pequeñas locuras que hacemos juntos.",
            "Te amo muchísimo, Giany. ❤️",
        ],
        "firma_carta": "Feliz 3 años y 6 meses, mi amor.",
        "lista_planes": ["Viajar juntos", "Una escapada de fin de semana", "Un concierto", "Cocinar juntos", "Ver el amanecer"],
        "lista_amo": ["Tu valentía para seguir tus sueños", "Tu forma de cuidar a los demás", "Tu paciencia infinita conmigo", "Tu mirada cuando te concentras", "Tu risa contagiosa", "Tu abrazo fuerte", "El brillo en tus ojos cuando hablas de lo que amas"],
        "youtube_id": "b-XkexlmElM",
        "cupon_texto": "Vale por elegir el restaurante",
        "mensaje_cierre": "Te amo.",
    }

    fotos_dir = "/home/claude/love-page/img"
    fotos_prueba = [
        (f"{fotos_dir}/photo1.jpg", "bajo las flores de cerezo"),
        (f"{fotos_dir}/photo2.jpg", None),
        (f"{fotos_dir}/photo3.jpg", None),
        (f"{fotos_dir}/photo4.jpg", None),
        (f"{fotos_dir}/photo5.jpg", "domingos de mascarilla"),
        (f"{fotos_dir}/photo6.jpg", None),
    ]

    salida = generar_pagina(datos_prueba, fotos_prueba, "prueba_generador.html")
    print("Generado:", salida, "-", os.path.getsize(salida) / 1024, "KB")
