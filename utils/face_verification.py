import os
import cv2
import numpy as np
import face_recognition
import logging

# Ensure numpy is properly imported for type checking
from numpy import bool_ as np_bool, number as np_number

# Configurar logging
logger = logging.getLogger(__name__)

def extract_face_from_id_card(id_card_path):
    """
    Extrae el rostro de la imagen de la CCCD

    Args:
        id_card_path: Ruta a la imagen de la CCCD

    Returns:
        face_encoding: Codificación del rostro encontrado
        face_location: Ubicación del rostro en la imagen
        success: True si se encontró un rostro, False en caso contrario
        message: Mensaje de error o éxito
    """
    try:
        # Verificar si el archivo existe
        if not os.path.exists(id_card_path):
            logger.error(f"No se encontró el archivo: {id_card_path}")
            return None, None, False, "No se encontró la imagen de la CCCD"

        # Cargar la imagen
        image = face_recognition.load_image_file(id_card_path)

        # Detectar rostros en la imagen
        face_locations = face_recognition.face_locations(image)

        # Verificar si se encontró algún rostro
        if len(face_locations) == 0:
            logger.warning(f"No se encontraron rostros en la imagen: {id_card_path}")
            return None, None, False, "No se encontraron rostros en la imagen de la CCCD"

        # Si se encontraron múltiples rostros, usar el primero
        if len(face_locations) > 1:
            logger.warning(f"Se encontraron múltiples rostros ({len(face_locations)}) en la imagen: {id_card_path}")

        # Obtener la codificación del rostro
        face_encodings = face_recognition.face_encodings(image, face_locations)

        if len(face_encodings) == 0:
            logger.warning(f"No se pudo codificar el rostro en la imagen: {id_card_path}")
            return None, None, False, "No se pudo codificar el rostro en la imagen de la CCCD"

        # Devolver la codificación del primer rostro encontrado
        return face_encodings[0], face_locations[0], True, "Rostro extraído correctamente"

    except Exception as e:
        logger.error(f"Error al extraer el rostro de la CCCD: {str(e)}")
        return None, None, False, f"Error al procesar la imagen: {str(e)}"

def extract_face_from_selfie(selfie_path):
    """
    Extrae el rostro de la imagen de selfie

    Args:
        selfie_path: Ruta a la imagen de selfie

    Returns:
        face_encoding: Codificación del rostro encontrado
        face_location: Ubicación del rostro en la imagen
        success: True si se encontró un rostro, False en caso contrario
        message: Mensaje de error o éxito
    """
    try:
        # Verificar si el archivo existe
        if not os.path.exists(selfie_path):
            logger.error(f"No se encontró el archivo: {selfie_path}")
            return None, None, False, "No se encontró la imagen de selfie"

        # Cargar la imagen
        image = face_recognition.load_image_file(selfie_path)

        # Detectar rostros en la imagen
        face_locations = face_recognition.face_locations(image)

        # Verificar si se encontró algún rostro
        if len(face_locations) == 0:
            logger.warning(f"No se encontraron rostros en la imagen: {selfie_path}")
            return None, None, False, "No se encontraron rostros en la imagen de selfie"

        # Si se encontraron múltiples rostros, usar el primero
        if len(face_locations) > 1:
            logger.warning(f"Se encontraron múltiples rostros ({len(face_locations)}) en la imagen: {selfie_path}")

        # Obtener la codificación del rostro
        face_encodings = face_recognition.face_encodings(image, face_locations)

        if len(face_encodings) == 0:
            logger.warning(f"No se pudo codificar el rostro en la imagen: {selfie_path}")
            return None, None, False, "No se pudo codificar el rostro en la imagen de selfie"

        # Devolver la codificación del primer rostro encontrado
        return face_encodings[0], face_locations[0], True, "Rostro extraído correctamente"

    except Exception as e:
        logger.error(f"Error al extraer el rostro de la selfie: {str(e)}")
        return None, None, False, f"Error al procesar la imagen: {str(e)}"

def compare_faces(id_card_encoding, selfie_encoding, tolerance=0.6):
    """
    Compara dos codificaciones de rostros para determinar si son la misma persona

    Args:
        id_card_encoding: Codificación del rostro de la CCCD
        selfie_encoding: Codificación del rostro de la selfie
        tolerance: Umbral de tolerancia para considerar que los rostros coinciden (menor es más estricto)

    Returns:
        match: True si los rostros coinciden, False en caso contrario
        distance: Distancia entre los rostros (menor distancia indica mayor similitud)
        message: Mensaje descriptivo del resultado
    """
    try:
        if id_card_encoding is None or selfie_encoding is None:
            return False, 1.0, "No se pueden comparar las codificaciones de rostros"

        # Calcular la distancia entre los rostros
        face_distances = face_recognition.face_distance([id_card_encoding], selfie_encoding)

        if len(face_distances) == 0:
            return False, 1.0, "Error al calcular la distancia entre rostros"

        distance = face_distances[0]

        # Determinar si los rostros coinciden según la tolerancia
        match = distance <= tolerance

        # Crear mensaje descriptivo
        if match:
            confidence = (1.0 - distance) * 100
            message = f"Los rostros coinciden con una confianza del {confidence:.2f}%"
        else:
            message = "Los rostros no coinciden"

        return match, distance, message

    except Exception as e:
        logger.error(f"Error al comparar rostros: {str(e)}")
        return False, 1.0, f"Error al comparar rostros: {str(e)}"

def verify_face_match(id_card_path, selfie_path, tolerance=0.6):
    """
    Verifica si el rostro en la imagen de la CCCD coincide con el rostro en la selfie

    Args:
        id_card_path: Ruta a la imagen de la CCCD
        selfie_path: Ruta a la imagen de selfie
        tolerance: Umbral de tolerancia para considerar que los rostros coinciden (menor es más estricto)

    Returns:
        result: Diccionario con el resultado de la verificación
    """
    result = {
        'success': False,
        'match': False,
        'distance': 1.0,
        'message': "",
        'id_card_face_found': False,
        'selfie_face_found': False
    }

    # Extraer rostro de la CCCD
    id_card_encoding, id_card_location, id_card_success, id_card_message = extract_face_from_id_card(id_card_path)
    result['id_card_face_found'] = bool(id_card_success)  # Convertir a bool nativo de Python

    if not id_card_success:
        result['message'] = id_card_message
        return result

    # Extraer rostro de la selfie
    selfie_encoding, selfie_location, selfie_success, selfie_message = extract_face_from_selfie(selfie_path)
    result['selfie_face_found'] = bool(selfie_success)  # Convertir a bool nativo de Python

    if not selfie_success:
        result['message'] = selfie_message
        return result

    # Comparar rostros
    match, distance, message = compare_faces(id_card_encoding, selfie_encoding, tolerance)

    result['success'] = True
    result['match'] = bool(match)  # Convertir a bool nativo de Python
    result['distance'] = float(distance)  # Convertir a float nativo de Python
    result['message'] = message

    # Asegurar que todos los valores son serializables a JSON
    for key in result:
        if isinstance(result[key], np_bool):
            result[key] = bool(result[key])
        elif isinstance(result[key], np_number):
            result[key] = float(result[key])

    return result
