import time
import logging
from typing import Any, Callable, Optional, Dict, List
from functools import wraps
from enum import Enum


class ErrorType(Enum):
    """Tipos de errores para categorización"""
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    DATA_VALIDATION_ERROR = "data_validation_error"
    FILE_IO_ERROR = "file_io_error"
    PARSING_ERROR = "parsing_error"
    UNKNOWN_ERROR = "unknown_error"


class ValidationError(Exception):
    """Excepción personalizada para errores de validación"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message)
        self.field = field
        self.value = value
        self.message = message


class RetryConfig:
    """Configuración para reintentos con backoff exponencial"""
    
    def __init__(self, 
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0,
                 jitter: bool = True):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter


def retry_with_backoff(config: RetryConfig = None, 
                      retry_on: tuple = (Exception,),
                      logger: logging.Logger = None):
    """
    Decorador para reintentos con backoff exponencial
    
    Args:
        config: Configuración de reintentos
        retry_on: Tupla de excepciones en las que reintentar
        logger: Logger para registrar reintentos
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    
                    if attempt == config.max_retries:
                        if logger:
                            logger.error(f"❌ Función {func.__name__} falló después de {config.max_retries} reintentos: {str(e)}")
                        raise
                    
                    delay = min(
                        config.base_delay * (config.backoff_factor ** attempt),
                        config.max_delay
                    )
                    
                    if config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)
                    
                    if logger:
                        logger.warning(f"⚠️ Intento {attempt + 1}/{config.max_retries + 1} falló para {func.__name__}: {str(e)}. Reintentando en {delay:.2f}s")
                    
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


class DataValidator:
    """Validador de datos con reglas configurables"""
    
    @staticmethod
    def validate_movie_data(movie_data: Dict[str, Any], logger: logging.Logger = None) -> Dict[str, Any]:
        """
        Valida y limpia datos de película
        
        Args:
            movie_data: Datos de película a validar
            logger: Logger para registrar validaciones
            
        Returns:
            Dict con datos validados y limpios
            
        Raises:
            ValidationError: Si los datos no pasan la validación
        """
        if not isinstance(movie_data, dict):
            raise ValidationError("Los datos de película deben ser un diccionario", "movie_data", movie_data)
        
        validated_data = {}
        errors = []
        
        # Validar título (obligatorio)
        title = movie_data.get('title', '').strip()
        if not title:
            errors.append("Título es obligatorio")
        else:
            validated_data['title'] = title
        
        # Validar y limpiar rating
        try:
            rating = movie_data.get('rating')
            if rating is not None:
                rating_float = float(rating)
                if 0 <= rating_float <= 10:
                    validated_data['rating'] = rating_float
                else:
                    if logger:
                        logger.warning(f"⚠️ Rating fuera de rango (0-10): {rating_float}")
                    validated_data['rating'] = None
            else:
                validated_data['rating'] = None
        except (ValueError, TypeError):
            if logger:
                logger.warning(f"⚠️ Rating inválido: {movie_data.get('rating')}")
            validated_data['rating'] = None
        
        # Validar y limpiar año
        try:
            date_published = movie_data.get('date_published', '')
            if date_published:
                year = int(str(date_published)[:4])
                if 1888 <= year <= 2030:  # Rango válido de años de cine
                    validated_data['year'] = year
                else:
                    if logger:
                        logger.warning(f"⚠️ Año fuera de rango válido: {year}")
                    validated_data['year'] = None
            else:
                validated_data['year'] = None
        except (ValueError, TypeError):
            if logger:
                logger.warning(f"⚠️ Fecha de publicación inválida: {movie_data.get('date_published')}")
            validated_data['year'] = None
        
        # Validar duración
        try:
            duration = movie_data.get('duration_minutes')
            if duration is not None:
                duration_int = int(float(duration))
                if 1 <= duration_int <= 1000:  # Rango razonable de minutos
                    validated_data['duration'] = duration_int
                else:
                    if logger:
                        logger.warning(f"⚠️ Duración fuera de rango: {duration_int} minutos")
                    validated_data['duration'] = None
            else:
                validated_data['duration'] = None
        except (ValueError, TypeError):
            if logger:
                logger.warning(f"⚠️ Duración inválida: {movie_data.get('duration_minutes')}")
            validated_data['duration'] = None
        
        # Validar metascore
        try:
            metascore = movie_data.get('metascore')
            if metascore is not None:
                metascore_float = float(metascore)
                if 0 <= metascore_float <= 100:
                    validated_data['metascore'] = metascore_float
                else:
                    if logger:
                        logger.warning(f"⚠️ Metascore fuera de rango (0-100): {metascore_float}")
                    validated_data['metascore'] = None
            else:
                validated_data['metascore'] = None
        except (ValueError, TypeError):
            if logger:
                logger.warning(f"⚠️ Metascore inválido: {movie_data.get('metascore')}")
            validated_data['metascore'] = None
        
        # Validar actores
        validated_data['actors'] = DataValidator._validate_actors_list(
            movie_data.get('actors', []), logger
        )
        
        # Validar URL
        movie_url = movie_data.get('movie_url', '').strip()
        if movie_url and (movie_url.startswith('http://') or movie_url.startswith('https://')):
            validated_data['movie_url'] = movie_url
        else:
            validated_data['movie_url'] = movie_url  # Guardar aunque no sea válida
            if movie_url and logger:
                logger.warning(f"⚠️ URL de película posiblemente inválida: {movie_url}")
        
        # Copiar otros campos
        for field in ['date_published', 'alternate_title', 'movie_id']:
            if field in movie_data:
                validated_data[field] = movie_data[field]
        
        if errors:
            raise ValidationError(f"Errores de validación: {'; '.join(errors)}")
        
        if logger:
            logger.debug(f"✅ Datos de película validados: {validated_data['title']}")
        
        return validated_data
    
    @staticmethod
    def _validate_actors_list(actors_data: Any, logger: logging.Logger = None) -> List[str]:
        """Valida y limpia lista de actores"""
        if not actors_data:
            return []
        
        try:
            if isinstance(actors_data, list):
                clean_actors = [str(actor).strip() for actor in actors_data if actor and str(actor).strip()]
                return clean_actors[:20]  # Límite máximo de 20 actores
            elif isinstance(actors_data, str):
                import ast
                try:
                    # Intentar evaluar como lista literal
                    actors_list = ast.literal_eval(actors_data)
                    if isinstance(actors_list, list):
                        clean_actors = [str(actor).strip() for actor in actors_list if actor and str(actor).strip()]
                        return clean_actors[:20]
                except:
                    # Si falla, dividir por separadores comunes
                    separators = [';', ',', '|']
                    for sep in separators:
                        if sep in actors_data:
                            clean_actors = [actor.strip() for actor in actors_data.split(sep) if actor.strip()]
                            return clean_actors[:20]
                    
                    # Si no hay separadores, tratar como un solo actor
                    return [actors_data.strip()] if actors_data.strip() else []
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ Error procesando actores: {e}")
            return []
        
        return []


class ErrorHandler:
    """Manejador centralizado de errores"""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_counts = {}
    
    def handle_error(self, 
                     error: Exception, 
                     error_type: ErrorType,
                     context: str = "",
                     data: Any = None,
                     fatal: bool = False) -> bool:
        """
        Maneja errores de forma centralizada
        
        Args:
            error: Excepción ocurrida
            error_type: Tipo de error para categorización
            context: Contexto donde ocurrió el error
            data: Datos relacionados con el error
            fatal: Si el error es fatal (detiene la ejecución)
            
        Returns:
            bool: True si se debe continuar, False si se debe detener
        """
        error_key = f"{error_type.value}:{context}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        error_msg = f"{'🚨 FATAL' if fatal else '❌ ERROR'} [{error_type.value}] {context}: {str(error)}"
        
        if data:
            error_msg += f" | Datos: {str(data)[:200]}..."
        
        if fatal:
            self.logger.critical(error_msg)
            return False
        else:
            self.logger.error(error_msg)
            
            # Si hay demasiados errores del mismo tipo, considerarlo fatal
            if self.error_counts[error_key] > 10:
                self.logger.critical(f"🚨 Demasiados errores del tipo {error_key} ({self.error_counts[error_key]}). Deteniendo.")
                return False
            
            return True
    
    def get_error_summary(self) -> Dict[str, int]:
        """Retorna resumen de errores ocurridos"""
        return self.error_counts.copy()
    
    def reset_error_counts(self):
        """Resetea los contadores de errores"""
        self.error_counts.clear()


class SafeOperations:
    """Operaciones seguras con manejo de errores integrado"""
    
    @staticmethod
    def safe_file_write(file_path: str, content: Any, encoding: str = 'utf-8', logger: logging.Logger = None) -> bool:
        """Escritura segura de archivos con manejo de errores"""
        try:
            import json
            import os
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Escribir a archivo temporal primero
            temp_path = f"{file_path}.tmp"
            
            with open(temp_path, 'w', encoding=encoding) as f:
                if isinstance(content, (dict, list)):
                    json.dump(content, f, ensure_ascii=False, indent=2)
                else:
                    f.write(str(content))
            
            # Mover archivo temporal al destino final
            os.replace(temp_path, file_path)
            
            if logger:
                logger.info(f"✅ Archivo escrito exitosamente: {file_path}")
            
            return True
            
        except Exception as e:
            if logger:
                logger.error(f"❌ Error escribiendo archivo {file_path}: {str(e)}")
            
            # Limpiar archivo temporal si existe
            try:
                import os
                if os.path.exists(f"{file_path}.tmp"):
                    os.remove(f"{file_path}.tmp")
            except:
                pass
            
            return False
    
    @staticmethod
    def safe_file_read(file_path: str, encoding: str = 'utf-8', logger: logging.Logger = None) -> Optional[Any]:
        """Lectura segura de archivos con manejo de errores"""
        try:
            import json
            import os
            
            if not os.path.exists(file_path):
                if logger:
                    logger.warning(f"⚠️ Archivo no existe: {file_path}")
                return None
            
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                
                # Intentar parsear como JSON
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Si no es JSON válido, retornar como string
                    return content
            
        except Exception as e:
            if logger:
                logger.error(f"❌ Error leyendo archivo {file_path}: {str(e)}")
            return None 