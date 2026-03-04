# ARCHITECTURE.md — ICFES Leveling Architecture Decision Records

> Decisiones arquitectónicas del proyecto, su contexto y consecuencias.

---

## ADR-001: Monorepo Structure

**Estado:** Aceptado  
**Contexto:** Necesitamos coordinar backend, mobile, AI service y WebSocket con modelos de datos compartidos.  
**Decisión:** Monorepo con estructura `apps/` para cada servicio y `database/` para esquemas compartidos.  
**Consecuencias:**
- (+) Cambios cross-service en un solo PR.
- (+) Versionado unificado.
- (-) CI/CD más complejo (debe detectar qué servicio cambió).

---

## ADR-002: FastAPI como Framework Backend

**Estado:** Aceptado  
**Contexto:** Necesitamos API REST de alto rendimiento con soporte async, validación automática, y buena integración con Python científico (NumPy/SciPy para IRT).  
**Decisión:** FastAPI con Pydantic v2 y SQLAlchemy 2.0.  
**Consecuencias:**
- (+) Auto-documentación OpenAPI.
- (+) Validación tipo-segura con Pydantic.
- (+) Async nativo con rendimiento superior a Django/Flask.
- (+) Ecosistema Python para cálculos IRT (NumPy, SciPy).
- (-) Menos maduro que Django para admin panels.

---

## ADR-003: PostgreSQL 16 como BD Principal

**Estado:** Aceptado  
**Contexto:** 60+ modelos relacionales con integridad referencial fuerte, soporte JSON, arrays, y UUIDs.  
**Decisión:** PostgreSQL 16 con SQLAlchemy ORM y Alembic migrations.  
**Consecuencias:**
- (+) ACID compliance para economía virtual y transacciones.
- (+) Soporte nativo JSON y arrays para metadata flexible.
- (+) UUID como PK nativo.
- (-) Requiere más tuning que SQLite para dev local (mitigado con Docker).

---

## ADR-004: Redis como Cache Layer

**Estado:** Aceptado  
**Contexto:** Leaderboards, sesiones, tokens revocados, y cache de respuestas AI requieren acceso sub-milisegundo.  
**Decisión:** Redis 7 con LRU eviction policy, 256MB max memory.  
**Consecuencias:**
- (+) Latencia sub-ms para leaderboards y cache.
- (+) TTL nativo para expiración de cache AI (30 días).
- (+) Pub/Sub para eventos real-time.
- (-) Datos volátiles; no usar para estado crítico sin backup a PostgreSQL.

---

## ADR-005: ClickHouse para Analytics

**Estado:** Aceptado  
**Contexto:** Necesitamos time-series analytics para tracking de rendimiento, patrones de error, y métricas de engagement a escala.  
**Decisión:** ClickHouse para datos analíticos separados de PostgreSQL operacional.  
**Consecuencias:**
- (+) Queries analíticos 10-100x más rápidos que PostgreSQL.
- (+) Compresión columnar eficiente para series temporales.
- (-) Servicio adicional que mantener.
- (-) No soporta UPDATE/DELETE eficientes (append-only).

---

## ADR-006: Flutter para Mobile

**Estado:** Aceptado  
**Contexto:** App mobile con animaciones complejas (RPG), rendimiento nativo, y soporte iOS + Android desde un solo codebase.  
**Decisión:** Flutter SDK ≥3.0 con Riverpod para state management.  
**Consecuencias:**
- (+) Single codebase para iOS y Android.
- (+) Rendimiento de animaciones superior (Rive, Lottie).
- (+) Hot reload para desarrollo rápido.
- (-) Tamaño de APK mayor que nativo.
- (-) Menor ecosistema de librerías que React Native.

---

## ADR-007: Riverpod sobre Provider/BLoC

**Estado:** Aceptado  
**Contexto:** State management para app compleja con múltiples features interconectadas.  
**Decisión:** Riverpod ^2.5.0 exclusivamente (NO Provider, BLoC, GetX).  
**Consecuencias:**
- (+) Type-safe sin BuildContext.
- (+) Testing superior.
- (+) Auto-dispose de providers.
- (-) Curva de aprendizaje para el equipo.

---

## ADR-008: Offline-First con Hive

**Estado:** Aceptado  
**Contexto:** Usuarios colombianos en zonas rurales con conectividad intermitente deben poder practicar sin internet.  
**Decisión:** Hive como BD local NoSQL + ActionQueue + SyncManager.  
**Consecuencias:**
- (+) Práctica 100% offline.
- (+) Sincronización transparente al reconectar.
- (+) Hive es rápido y ligero.
- (-) Complejidad de resolución de conflictos.
- (-) Datos de juego pueden divergir temporalmente.

---

## ADR-009: IRT 3PL para Testing Adaptativo

**Estado:** Aceptado  
**Contexto:** Necesitamos medir habilidad real del estudiante y seleccionar preguntas óptimas, no solo contar correctas/incorrectas.  
**Decisión:** Modelo IRT de 3 parámetros (discriminación, dificultad, pseudo-adivinanza) con estimación MLE y selección por Fisher Information.  
**Consecuencias:**
- (+) Medición psicométrica válida.
- (+) Selección óptima de preguntas.
- (+) Calibración continua.
- (-) Requiere mínimo ~30 respuestas para estimación estable.
- (-) Complejidad matemática del backend.

---

## ADR-010: GameEngineService como Fuente Única de Verdad

**Estado:** Aceptado  
**Contexto:** Fórmulas de XP, nivel, daño, y oro estaban duplicadas en múltiples servicios causando inconsistencias.  
**Decisión:** Centralizar TODA la lógica de mecánicas de juego en `game_engine_service.py`. Todo lo demás es legacy.  
**Consecuencias:**
- (+) Una sola fuente de verdad para balanceo.
- (+) Cambios de fórmulas en un solo lugar.
- (+) Testing centralizado.
- (-) Servicio puede crecer mucho; requiere buena organización interna.

---

## ADR-011: Microservicio AI Separado

**Estado:** Aceptado  
**Contexto:** Llamadas a OpenAI/Claude son lentas (2-10s), costosas, y pueden fallar. No deben bloquear el backend principal.  
**Decisión:** AI service como microservicio separado en `apps/ai-service/` con su propio cache Redis.  
**Consecuencias:**
- (+) Aislamiento de fallos (AI caído no tumba el backend).
- (+) Cache independiente con TTL largo (30 días).
- (+) Escalado independiente.
- (-) Latencia de red adicional (mitigado con red Docker interna).

---

## ADR-012: WebSocket para PvP

**Estado:** Aceptado  
**Contexto:** Batallas PvP requieren comunicación bidireccional en tiempo real.  
**Decisión:** Servicio WebSocket en Node.js separado del backend Python.  
**Consecuencias:**
- (+) Node.js optimizado para WebSocket y alta concurrencia I/O.
- (+) Aislado del backend REST.
- (-) Servicio adicional en otro lenguaje.

---

## ADR-013: Wompi + Stripe para Pagos

**Estado:** Aceptado  
**Contexto:** Usuarios colombianos necesitan métodos de pago locales (PSE, Nequi, tarjetas colombianas).  
**Decisión:** Wompi como gateway primario para Colombia, Stripe para pagos internacionales.  
**Consecuencias:**
- (+) Cobertura completa de métodos de pago colombianos.
- (+) Stripe como fallback internacional.
- (-) Dos integraciones de pago que mantener.

---

## DIAGRAMA DE ARQUITECTURA

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTE                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Flutter Mobile App                        │  │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌───────────┐ │  │
│  │  │Riverpod │ │   Hive   │ │   Dio   │ │ GoRouter  │ │  │
│  │  │  State  │ │ Offline  │ │  HTTP   │ │   Nav     │ │  │
│  │  └─────────┘ └──────────┘ └────┬────┘ └───────────┘ │  │
│  └────────────────────────────────┼─────────────────────┘  │
└───────────────────────────────────┼─────────────────────────┘
                                    │ REST API + WebSocket
┌───────────────────────────────────┼─────────────────────────┐
│                        BACKEND                               │
│  ┌────────────────────────────────┼─────────────────────┐   │
│  │         FastAPI Backend (:4000)│                      │   │
│  │  ┌──────────┐ ┌───────────┐ ┌─┴────────┐           │   │
│  │  │  Routes  │ │ Services  │ │  Models  │            │   │
│  │  │(10 tiers)│ │(GameEngine│ │ (60+)    │            │   │
│  │  │          │ │ Practice  │ │          │            │   │
│  │  │          │ │ Mastery   │ │          │            │   │
│  │  │          │ │ IRT, etc) │ │          │            │   │
│  │  └──────────┘ └───────────┘ └──────────┘            │   │
│  └──────┬──────────────┬──────────────┬────────────────┘   │
│         │              │              │                      │
│  ┌──────┴───┐  ┌───────┴────┐  ┌─────┴──────┐             │
│  │PostgreSQL│  │   Redis    │  │ ClickHouse │             │
│  │  16      │  │   7-alpine │  │  Analytics │             │
│  │  (:5433) │  │   (:6379)  │  │  (:8123)   │             │
│  └──────────┘  └────────────┘  └────────────┘             │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  AI Service      │  │  WebSocket       │                │
│  │  FastAPI (:8002) │  │  Node.js (:4002) │                │
│  │  GPT/Claude      │  │  PvP Battles     │                │
│  └──────────────────┘  └──────────────────┘                │
└──────────────────────────────────────────────────────────────┘
```
