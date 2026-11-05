# Taller 6 - Dos APIs CRUD con despliegue en contenedores

Dos implementaciones del mismo CRUD de `tareas`, con lenguaje y base de datos
diferentes, listas para desplegarse localmente con Docker y luego en una
instancia EC2 de AWS.

| API | Lenguaje | Base de datos | Puerto |
|---|---|---|---|
| `api_fastapi` | Python 3.12 + FastAPI | PostgreSQL 16 | `8000` |
| `api_springboot` | Java 21 + Spring Boot | MySQL 8 | `8085` |

Cada API tiene su propio `docker-compose.yml`, su propia base de datos y su
propio volumen, por lo que son independientes entre sí.

## Estructura

```
crud-fastapi-postgres/
├── api_fastapi/
│   ├── app/main.py
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
└── api_springboot/
    ├── src/main/java/com/example/tareas/
    ├── src/main/resources/application.properties
    ├── Dockerfile
    ├── docker-compose.yml
    └── build.gradle
```

## Requisitos

- Docker Engine 24+ y Docker Compose v2+
- (Opcional) Git para clonar el repositorio en EC2

## Ejecución local con contenedores

### 1. API FastAPI + PostgreSQL

```bash
cd api_fastapi
cp .env.example .env   # definir usuario y contraseña propios
docker compose up -d --build
```

- API: <http://localhost:8000/tareas>
- Documentación interactiva: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

### 2. API Spring Boot + MySQL

```bash
cd api_springboot
cp .env.example .env   # definir usuario y contraseña propios
docker compose up -d --build
```

- API: <http://localhost:8085/tareas>
- Swagger UI: <http://localhost:8085/swagger-ui/index.html>
- Health: <http://localhost:8085/actuator/health>

> La primera construcción de Spring Boot descarga Gradle y las dependencias,
> por lo que puede tardar varios minutos.

### Comandos útiles

```bash
docker compose ps          # estado de los contenedores
docker compose logs -f api # logs de la API
docker compose down        # detener (conserva los datos)
docker compose down -v     # detener y borrar la base de datos
```

## Endpoints (iguales en ambas APIs)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/tareas` | Listar todas las tareas |
| `GET` | `/tareas/{id}` | Obtener una tarea |
| `POST` | `/tareas` | Crear una tarea |
| `PUT` | `/tareas/{id}` | Actualizar una tarea |
| `DELETE` | `/tareas/{id}` | Eliminar una tarea |

Cuerpo para `POST` y `PUT`:

```json
{
  "titulo": "Estudiar AWS",
  "descripcion": "Repasar EC2 y contenedores",
  "completada": false
}
```

Ejemplos con `curl` (cambiar el puerto según la API):

```bash
# Crear
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Estudiar AWS","descripcion":"Repasar EC2","completada":false}'

# Listar
curl http://localhost:8000/tareas

# Obtener
curl http://localhost:8000/tareas/1

# Actualizar
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Estudiar AWS","descripcion":"Terminado","completada":true}'

# Eliminar
curl -X DELETE http://localhost:8000/tareas/1
```

## Variables de entorno

Cada proyecto incluye un `.env.example` con las variables requeridas. Antes de
levantar los contenedores hay que crear el `.env` local:

```bash
cp .env.example .env
```

`docker compose` lee automáticamente el archivo `.env`. El `.env` está en
`.gitignore` y **no debe subirse al repositorio**.

- `api_fastapi`: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.
- `api_springboot`: `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_USER`,
  `MYSQL_PASSWORD`.

> Si se cambian las credenciales después de haber levantado los contenedores,
> hay que recrear el volumen de la base de datos (`docker compose down -v`),
> porque las credenciales se crean solo la primera vez que se inicializa.

## Despliegue en AWS EC2

1. Crear una instancia EC2 (Amazon Linux 2023 o Ubuntu 22.04/24.04).
2. Configurar el Security Group con reglas de entrada:
   - `22/tcp` desde tu IP (SSH)
   - `8000/tcp` desde `0.0.0.0/0` (FastAPI)
   - `8085/tcp` desde `0.0.0.0/0` (Spring Boot)
3. Conectarse por SSH e instalar Docker:

   ```bash
   # Amazon Linux 2023
   sudo dnf install -y docker git
   sudo systemctl enable --now docker
   sudo usermod -aG docker $USER
   newgrp docker

   # Ubuntu
   sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
   sudo systemctl enable --now docker
   sudo usermod -aG docker $USER
   newgrp docker
   ```

4. Clonar el repositorio y levantar cada API:

   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd crud-fastapi-postgres

   cd api_fastapi
   cp .env.example .env   # editar con credenciales propias
   docker compose up -d --build

   cd ../api_springboot
   cp .env.example .env   # editar con credenciales propias
   docker compose up -d --build
   ```

5. Verificar desde el navegador o con `curl`:

   ```bash
   curl http://<IP_PUBLICA_EC2>:8000/tareas
   curl http://<IP_PUBLICA_EC2>:8000/health

   curl http://<IP_PUBLICA_EC2>:8085/tareas
   curl http://<IP_PUBLICA_EC2>:8085/actuator/health
   ```

Ambos proyectos usan `restart: unless-stopped`, así que los contenedores se
levantan de nuevo si la instancia EC2 se reinicia.

> La compilación de Spring Boot dentro de una instancia muy pequeña (por
> ejemplo `t3.micro`) puede quedarse sin memoria. Si ocurre, usar al menos
> `t3.medium` o construir la imagen en local y subirla a Amazon ECR.

## Diferencias entre las dos implementaciones

- **FastAPI** usa SQLAlchemy con el driver `psycopg2` y crea la tabla al iniciar.
- **Spring Boot** usa Spring Data JPA con Hibernate y el driver de MySQL; el
  esquema se actualiza con `spring.jpa.hibernate.ddl-auto=update`.

## Notas de seguridad

- Las credenciales de las bases de datos **no están en el código ni en los
  `docker-compose.yml`**: se leen de un `.env` que está ignorado por Git. Solo
  se versiona `.env.example` con valores de ejemplo.
- Los puertos de PostgreSQL y MySQL no se publican al host; solo son
  accesibles desde la red interna de Docker.
- Las respuestas de las APIs solo incluyen `id`, `titulo`, `descripcion` y
  `completada`. No se devuelven credenciales ni detalles de conexión.
- `/actuator/health` está expuesto, pero con `show-details=never`, por lo que
  no revela el motor de base de datos ni rutas internas.
- Las APIs no incluyen autenticación porque el taller no la exige. Para un
  entorno real se debe agregar autenticación (API key, JWT u OAuth2), usar
  HTTPS y restringir el Security Group a las IP necesarias.
- En producción se puede desactivar Swagger con `SPRINGDOC_ENABLED=false`
  (Spring Boot) y restringir `/docs` en FastAPI.

