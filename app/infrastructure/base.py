"""
Definición del objeto base para los modelos de SQLAlchemy en TidyTasks.

Todos los modelos ORM deben heredar de esta clase `Base`.
"""

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
