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
