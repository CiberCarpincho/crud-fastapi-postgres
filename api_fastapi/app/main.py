import os
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.orm import declarative_base, sessionmaker

# La cadena de conexion se inyecta por variable de entorno para no dejarla
# escrita en el codigo ni en la imagen.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Falta la variable de entorno DATABASE_URL")

# pool_pre_ping evita errores por conexiones cerradas por la base de datos.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Tarea(Base):
    __tablename__ = "tareas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(String)
    completada = Column(Boolean, default=False, nullable=False)


class TareaIn(BaseModel):
    titulo: str
    descripcion: str | None = None
    completada: bool = False


class TareaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descripcion: str | None = None
    completada: bool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Reintenta la conexión mientras el contenedor de PostgreSQL termina de arrancar.
    for intento in range(10):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except OperationalError:
            if intento == 9:
                raise
            time.sleep(3)
    yield


app = FastAPI(
    title="API Tareas - FastAPI + PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {"servicio": "api-tareas", "lenguaje": "python", "base_de_datos": "postgresql"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tareas", response_model=TareaOut, status_code=201)
def crear(t: TareaIn, db: DBSession = Depends(get_db)):
    obj = Tarea(**t.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/tareas", response_model=list[TareaOut])
def listar(db: DBSession = Depends(get_db)):
    return db.query(Tarea).all()


@app.get("/tareas/{id}", response_model=TareaOut)
def obtener(id: int, db: DBSession = Depends(get_db)):
    obj = db.get(Tarea, id)
    if not obj:
        raise HTTPException(404, "No encontrada")
    return obj


@app.put("/tareas/{id}", response_model=TareaOut)
def actualizar(id: int, t: TareaIn, db: DBSession = Depends(get_db)):
    obj = db.get(Tarea, id)
    if not obj:
        raise HTTPException(404, "No encontrada")
    for k, v in t.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@app.delete("/tareas/{id}")
def eliminar(id: int, db: DBSession = Depends(get_db)):
    obj = db.get(Tarea, id)
    if not obj:
        raise HTTPException(404, "No encontrada")
    db.delete(obj)
    db.commit()
    return {"ok": True}
