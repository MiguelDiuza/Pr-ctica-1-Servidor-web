# Parte 2 — Despliegue en AWS (pendiente)

> Aún no implementado. Esta es la arquitectura acordada para que el equipo sepa hacia dónde va.

```
VPC 10.0.0.0/16
├── Subred pública 10.0.1.0/24  (ruta a Internet Gateway)
│     └── EC2 "web" Ubuntu 24.04 — contenedor web (misma imagen de app/) + IP elástica
│           SG-web: entrada 80/8000 desde 0.0.0.0/0 (ESP32 y navegador), 22 solo desde la IP del equipo
└── Subred privada 10.0.2.0/24  (sin ruta a Internet)
      └── EC2 "db" Ubuntu 24.04 — PostgreSQL (o Amazon RDS)
            SG-db: entrada 5432 SOLO desde SG-web
```

Equivalencias con el entorno local:

| Local (docker-compose) | AWS |
|---|---|
| red `publica` + puerto 8000 publicado | subred pública + IP elástica + SG-web |
| red `privada` (`internal: true`) | subred privada sin ruta a internet + SG-db |
| `DATABASE_URL=...@db:5432/...` | `DATABASE_URL=...@<IP-privada-de-db>:5432/...` |

Pendiente de decidir: cuenta (AWS Academy Learner Lab vs. cuenta propia) y si se automatiza con Terraform.
