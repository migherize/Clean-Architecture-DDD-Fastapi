## **📂 Estructura del Proyecto**

```plaintext
├── app
│   ├── application                # Lógica de negocio (servicios y casos de uso)
│   ├── config                      # Configuración global y logging
│   ├── data                        # Datos estáticos o seeds
│   ├── domain                      # Entidades y contratos de repositorios
│   ├── infrastructure              # Implementaciones técnicas (DB, APIs externas, etc.)
│   ├── interfaces                  # Entradas y salidas (API REST, Schemas)
│   ├── logs                        # Archivos de log
│   ├── main.py                     # Punto de entrada FastAPI
│   └── utils                       # Funciones auxiliares
├── data                            # Datos globales o fixtures
├── docker-compose.yml              # Orquestación Docker
├── Dockerfile                      # Imagen del servicio
├── logs                            # Logs persistentes
├── README.md                       # Documentación principal
├── requirements.txt                # Dependencias Python
└── tests                           # Pruebas unitarias e integración
```

---

## **📊 Flujo de la Aplicación**

```plaintext
         📱 Cliente (Frontend / App)
                   │
                   ▼
        ┌───────────────────────────┐
        │        Interfaces         │  ← FastAPI (Routers, Schemas)
        └───────────────────────────┘
                   │  (Pydantic valida entrada)
                   ▼
        ┌───────────────────────────┐
        │        Application        │  ← Casos de uso
        └───────────────────────────┘
                   │  (Usa interfaces de dominio)
                   ▼
        ┌───────────────────────────┐
        │          Domain           │  ← Entidades y contratos (interfaces)
        └───────────────────────────┘
                   ▲
                   │  (Infra implementa contratos)
        ┌───────────────────────────┐
        │      Infrastructure       │  ← DB, APIs externas, archivos
        └───────────────────────────┘
                   │  (Datos reales)
                   ▼
              🗄 Base de datos
```

---

## **📝 Descripción por Capa**

### **Interfaces (app/interfaces)**

* Contiene routers de FastAPI.
* Define `schemas` (modelos Pydantic) para validar entrada/salida.
* Actúa como “puerta de entrada” de datos hacia la aplicación.

### **Application (app/application)**

* Implementa **casos de uso** de la aplicación.
* Orquesta la interacción entre **interfaces** y **dominio**.
* No accede directamente a la base de datos.

### **Domain (app/domain)**

* Define **entidades** (modelos de negocio puros).
* Declara **contratos** (interfaces de repositorios) que la infraestructura implementará.
* No tiene dependencias con infraestructura.

### **Infrastructure (app/infrastructure)**

* Implementa los contratos definidos en `domain`.
* Contiene:

  * Conexión a base de datos (`database_strategies.py`, `session.py`).
  * Configuración (`config/db_config.py`).
  * Mappers y adaptadores a APIs externas.
  * Manejo de errores (`error_handlers.py`).

### **Config (app/config)**

* Parámetros globales de la app.
* Configuración de logging.
* Carga de variables de entorno.

### **Utils (app/utils)**

* Funciones y utilidades compartidas.

---

## **🚀 Arranque rápido**

- **Instalar dependencias**:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
- **Levantar el servidor**:
```bash
uvicorn app.main:app --reload
```
- **Probar**: abre `http://localhost:8000` y `http://localhost:8000/docs`.

---

## **🔌 Estrategia de conexión a Base de Datos**

Este boilerplate usa el patrón Strategy para la base de datos (ver `app/infrastructure/database_strategies.py`). Las estrategias disponibles son:

- **sqlite**: por defecto, archivo `database_sqlite.db` en la raíz del proyecto.
- **postgresql**: usa `DBSettings` desde `app/infrastructure/config/db_config.py`.
- **mysql**: usa variables `MYSQL_*` específicas.

Flujo de inicialización:
- `app/infrastructure/session.py` lee `DB` del entorno y crea la estrategia: `DatabaseStrategyFactory.create_strategy(db_type=DB)`.
- La estrategia seleccionada valida la conexión (`validate_connection`) y crea tablas si no existen (`Base.metadata.create_all`) vía `create_tables_if_not_exist`.
- La dependencia `get_db()` inyecta una `Session` de SQLAlchemy en los endpoints.

Notas importantes:
- Asegúrate de que tus modelos ORM estén importados antes de la llamada a `create_all`. Recomendado: importarlos al final de `app/infrastructure/base.py` (ver ejemplo más abajo).
- Drivers:
  - PostgreSQL: instala `psycopg2-binary` si vas a usar Postgres.
  - MySQL: instala `PyMySQL` si vas a usar MySQL.

---

## **🧱 Cómo agregar tablas/modelos (SQLAlchemy)**

1) Crea el módulo del modelo, por ejemplo `app/infrastructure/models/todo.py`:
```python
from sqlalchemy import Column, Integer, String, Boolean
from app.infrastructure.base import Base

class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
```

2) Asegura el registro del modelo en `Base.metadata` importándolo temprano.
   Opción recomendada: al final de `app/infrastructure/base.py` agrega el import:
```python
# Registrar modelos para que Base.metadata los conozca
from app.infrastructure.models.todo import Todo  # noqa: F401
```
Con esto, cuando la estrategia ejecute `create_tables_if_not_exist()`, la tabla se creará si no existe.

---

## **🛰️ Cómo agregar endpoints (Routers)**

1) Crea schemas Pydantic (v2) para I/O en `app/interfaces/schemas/todo.py`:
```python
from pydantic import BaseModel, ConfigDict

class TodoBase(BaseModel):
    title: str

class TodoCreate(TodoBase):
    pass

class TodoOut(TodoBase):
    id: int
    is_completed: bool
    model_config = ConfigDict(from_attributes=True)
```

2) Crea el router en `app/interfaces/api/todos.py`:
```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.session import get_db
from app.interfaces.schemas.todo import TodoCreate, TodoOut
from app.infrastructure.models.todo import Todo

router = APIRouter(prefix="/todos", tags=["Todos"])

@router.post("/", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate, db: Session = Depends(get_db)):
    todo = Todo(title=payload.title)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo

@router.get("/", response_model=List[TodoOut])
def list_todos(db: Session = Depends(get_db)):
    return db.query(Todo).all()

@router.get("/{todo_id}", response_model=TodoOut)
 def get_todo(todo_id: int, db: Session = Depends(get_db)):
     todo = db.get(Todo, todo_id)
     if not todo:
         raise HTTPException(status_code=404, detail="Todo no encontrado")
     return todo

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
 def delete_todo(todo_id: int, db: Session = Depends(get_db)):
     todo = db.get(Todo, todo_id)
     if not todo:
         raise HTTPException(status_code=404, detail="Todo no encontrado")
     db.delete(todo)
     db.commit()
```

3) Incluye el router en `app/main.py`:
```python
from app.interfaces.api.todos import router as todos_router
app.include_router(todos_router, prefix="/api")
```

Con esto tendrás endpoints CRUD básicos como:
- POST `/api/todos/`
- GET `/api/todos/`
- GET `/api/todos/{todo_id}`
- DELETE `/api/todos/{todo_id}`

---

## **⚙️ Variables de entorno**

La variable clave para elegir estrategia es `DB` con valores: `sqlite`, `postgresql` o `mysql`.

- Ejemplo general (`.env`):
```env
# Estrategia
DB=sqlite  # o: postgresql, mysql
```

- Si usas PostgreSQL, además define (usados por `DBSettings`):
```env
DB=postgresql
USERDB=postgres
PASSWORDDB=postgres
NAME_SERVICEDB=localhost
PORT=5432
NAMEDB=my_database
```
Instala driver:
```bash
pip install psycopg2-binary
```

- Si usas MySQL, define (usados por `MySQLStrategy`):
```env
DB=mysql
MYSQL_USER=root
MYSQL_PASSWORD=secret
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=my_database
```
Instala driver:
```bash
pip install PyMySQL
```

Notas:
- Para SQLite no necesitas variables adicionales (usa `database_sqlite.db` por defecto). Si deseas cambiar la ruta, ajusta la inicialización de `SQLiteStrategy` para pasar `db_path`.
- El endpoint raíz muestra el valor de `DB_TYPE` si lo defines, pero la estrategia se decide con `DB`.

---

## **🐳 Docker (opcional)**

- Construir y levantar con Docker Compose:
```bash
docker compose up --build
```
- Variables de entorno: asegúrate de tener un `.env` en la raíz o define las variables en `docker-compose.yml`.

---

## **🧭 Resumen del flujo**

- Cliente HTTP → Router (`app/interfaces/api/...`) → Schemas validan entrada → Caso de uso (opcional, en `app/application`) → Repositorio/ORM (`app/infrastructure/...`) → DB.
- La sesión de DB se inyecta con `Depends(get_db)` desde `app/infrastructure/session.py`.
- La estrategia de DB valida conexión y crea tablas al iniciar.
