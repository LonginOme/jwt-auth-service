# Практика №3 — Контейнеризация и деплой в Kubernetes

**Тема:** Сервис генерации и валидации JWT токенов с ролями (Тема 19)  
**Студент:** Фокин Максим Юрьевич, группа ИКМО-06-25

---

## Ссылка на репозиторий

https://github.com/LonginOme/jwt-auth-service

---

## Список микросервисов и образов

| Микросервис | Docker-образ | Порт |
|---|---|---|
| API Gateway | api-gateway:latest | 8000 |
| Auth Service | auth-service:latest | 8001 |
| PostgreSQL | postgres:15 | 5432 |

---

## Инструкция по развёртыванию в Minikube

```bash