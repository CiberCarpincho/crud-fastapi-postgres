package com.example.tareas;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/tareas")
public class TareaController {
    private final TareaRepository repo;

    public TareaController(TareaRepository repo) { this.repo = repo; }

    private Tarea buscar(Long id) {
        return repo.findById(id).orElseThrow(
            () -> new ResponseStatusException(HttpStatus.NOT_FOUND, "No encontrada"));
    }

    @PostMapping
    public Tarea crear(@RequestBody Tarea t) {
        t.setId(null);
        return repo.save(t);
    }

    @GetMapping
    public List<Tarea> listar() { return repo.findAll(); }

    @GetMapping("/{id}")
    public Tarea obtener(@PathVariable Long id) { return buscar(id); }

    @PutMapping("/{id}")
    public Tarea actualizar(@PathVariable Long id, @RequestBody Tarea t) {
        Tarea obj = buscar(id);
        obj.setTitulo(t.getTitulo());
        obj.setDescripcion(t.getDescripcion());
        obj.setCompletada(t.isCompletada());
        return repo.save(obj);
    }

    @DeleteMapping("/{id}")
    public Map<String, Boolean> eliminar(@PathVariable Long id) {
        repo.delete(buscar(id));
        return Map.of("ok", true);
    }
}