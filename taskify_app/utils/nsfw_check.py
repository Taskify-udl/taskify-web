from django.apps import apps
from PIL import Image
import torch

def analizar_contenido_peligroso(image_file):
    """
    Analiza una imagen en busca de contenido inapropiado usando CLIP.
    Retorna un diccionario con las probabilidades de cada etiqueta.
    """
    try:
        app_config = apps.get_app_config('taskify_app')
        model = getattr(app_config, 'clip_model', None)
        processor = getattr(app_config, 'clip_processor', None)

        if not model or not processor:
            print("Modelo CLIP no disponible. Saltando verificación NSFW.")
            return {}

        image = Image.open(image_file)

        labels = [
            "a photo of safe content",           # Clase segura
            "a photo of violence or gore",       # Gore
            "blood and injuries",                # Sangre
            "illegal drugs or cocaine",          # Drogas
            "firearms and weapons",              # Armas
            "explicit nudity",                   # Desnudos explícitos
            "nude human body"                    # Cuerpo desnudo
        ]

        # Preparamos los inputs
        inputs = processor(text=labels, images=image, return_tensors="pt", padding=True)

        # La IA "piensa"
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Calculamos probabilidades (softmax)
        probs = outputs.logits_per_image.softmax(dim=1)
        
        # Convertimos a lista legible
        resultados = probs.tolist()[0]
        
        # Unimos etiquetas con su probabilidad
        analisis = dict(zip(labels, resultados))
        
        return analisis

    except Exception as e:
        print(f"Error en análisis NSFW: {e}")
        return {}

def es_contenido_seguro(analisis):
    """
    Determina si el contenido es seguro basándose en el análisis.
    Retorna True si es seguro, False si detecta contenido inapropiado.
    """
    if not analisis:
        return True  # Si falla el análisis, permitimos por defecto (fail-open) o denegamos? Fail-open para no bloquear.

    # Umbral de seguridad: 'safe content' debe ser la clase dominante o tener una probabilidad alta
    safe_score = analisis.get("a photo of safe content", 0)
    
    # Si 'safe content' es muy bajo (< 0.2) o alguna categoría peligrosa es muy alta (> 0.5)
    # O simplemente si la categoría con mayor probabilidad NO es 'safe content'
    
    max_label = max(analisis, key=analisis.get)
    
    if max_label != "a photo of safe content":
        # Si la etiqueta ganadora no es "safe content", es peligroso
        return False
        
    if safe_score < 0.4:
        # Si la confianza en que es seguro es baja, sospechamos
        return False

    return True
