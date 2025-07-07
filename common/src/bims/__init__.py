"""
Namespace package `bims` (PEP-420).
Оставляем файл, чтобы IDE видела пакет, но не создаём дубликатов в других wheel.
"""
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)
