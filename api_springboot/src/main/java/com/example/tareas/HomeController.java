package com.example.tareas;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HomeController {

    @GetMapping("/")
    public Map<String, String> root() {
        return Map.of(
            "servicio", "api-tareas",
            "lenguaje", "java",
            "base_de_datos", "mysql"
        );
    }
}
