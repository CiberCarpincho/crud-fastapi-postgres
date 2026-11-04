import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Tarea(Base):
    __tablename__ = "tareas"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(String)
    completada = Column(Boolean, default=False)

Base.metadata.create_all(engine)

class TareaIn(BaseModel):
    titulo: str
    descripcion: str | None = None
    completada: bool = False

app = FastAPI()

@app.post("/tareas")
def crear(t: TareaIn):
    db = Session()
    obj = Tarea(**t.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.get("/tareas")
def listar():
    return Session().query(Tarea).all()

@app.get("/tareas/{id}")
def obtener(id: int):
    obj = Session().get(Tarea, id)
    if not obj: raise HTTPException(404, "No encontrada")
    return obj

@app.put("/tareas/{id}")
def actualizar(id: int, t: TareaIn):
    db = Session()
    obj = db.get(Tarea, id)
    if not obj: raise HTTPException(404, "No encontrada")
    for k, v in t.model_dump().items(): setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj

@app.delete("/tareas/{id}")
def eliminar(id: int):
    db = Session()
    obj = db.get(Tarea, id)
    if not obj: raise HTTPException(404, "No encontrada")
    db.delete(obj); db.commit()
    return {"ok": True}