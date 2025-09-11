# Makefile para Sistema ICFES Leveling
# Sistema educativo gamificado de preparación ICFES
# 
# Comandos principales:
#   make setup     - Configuración inicial completa
#   make seed      - Cargar datos y procesar imágenes
#   make run       - Levantar todos los servicios
#   make test      - Ejecutar tests completos
#   make clean     - Limpiar archivos temporales

# =============================================================================
# CONFIGURACIÓN GLOBAL
# =============================================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker-compose

# Directorios del proyecto
PROJECT_ROOT := $(shell pwd)
SCRIPTS_DIR := $(PROJECT_ROOT)/scripts
DATABASE_DIR := $(PROJECT_ROOT)/database
BACKEND_DIR := $(PROJECT_ROOT)/apps/backend
FRONTEND_DIR := $(PROJECT_ROOT)/apps/frontend

# Archivos de datos críticos
EXCEL_MAIN := $(DATABASE_DIR)/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx
EXCEL_ALT := $(DATABASE_DIR)/seed_data/questionsv2.xlsx
IMAGES_DIR := $(DATABASE_DIR)/allquestions
SQL_LOAD_FILE := $(DATABASE_DIR)/seed_data/complete_questions_load.sql

# Configuración de colores para output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
WHITE := \033[37m
RESET := \033[0m

# =============================================================================
# COMANDOS PRINCIPALES
# =============================================================================

.PHONY: help
help: ## 📋 Mostrar esta ayuda
	@echo ""
	@echo "$(CYAN)🎯 Sistema ICFES Leveling - Comandos Make$(RESET)"
	@echo "$(CYAN)=========================================$(RESET)"
	@echo ""
	@echo "$(GREEN)📦 CONFIGURACIÓN INICIAL:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*📦/ {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)🗄️  GESTIÓN DE DATOS:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*🗄️/ {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(MAGENTA)🚀 SERVICIOS:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*🚀/ {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(RED)🧹 MANTENIMIENTO:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*🧹/ {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# =============================================================================
# CONFIGURACIÓN INICIAL
# =============================================================================

.PHONY: setup
setup: ## 📦 Configuración completa del proyecto (deps + .env + docker)
	@echo "$(CYAN)🔧 Configurando proyecto ICFES Leveling...$(RESET)"
	@$(MAKE) check-prerequisites
	@$(MAKE) create-env
	@$(MAKE) install-deps
	@$(MAKE) setup-docker
	@echo "$(GREEN)✅ Configuración completa exitosa$(RESET)"

.PHONY: check-prerequisites
check-prerequisites: ## 📦 Verificar prerequisites del sistema
	@echo "$(YELLOW)🔍 Verificando prerequisites...$(RESET)"
	@command -v python3 >/dev/null 2>&1 || (echo "$(RED)❌ Python 3 no encontrado$(RESET)" && exit 1)
	@command -v pip3 >/dev/null 2>&1 || (echo "$(RED)❌ pip3 no encontrado$(RESET)" && exit 1)
	@command -v docker >/dev/null 2>&1 || (echo "$(RED)❌ Docker no encontrado$(RESET)" && exit 1)
	@command -v docker-compose >/dev/null 2>&1 || (echo "$(RED)❌ Docker Compose no encontrado$(RESET)" && exit 1)
	@echo "$(GREEN)✅ Prerequisites verificados$(RESET)"

.PHONY: create-env
create-env: ## 📦 Crear archivo .env si no existe
	@echo "$(YELLOW)📄 Configurando variables de entorno...$(RESET)"
	@if [ ! -f .env ]; then \
		cp .env.example .env && \
		echo "$(GREEN)✅ Archivo .env creado desde .env.example$(RESET)"; \
	else \
		echo "$(BLUE)ℹ️  Archivo .env ya existe$(RESET)"; \
	fi
	@echo "$(YELLOW)⚠️  Revisa y actualiza las variables en .env según tu configuración$(RESET)"

.PHONY: install-deps
install-deps: ## 📦 Instalar dependencias Python
	@echo "$(YELLOW)📦 Instalando dependencias Python...$(RESET)"
	@if [ -f $(BACKEND_DIR)/requirements.txt ]; then \
		$(PIP) install -r $(BACKEND_DIR)/requirements.txt; \
		echo "$(GREEN)✅ Dependencias backend instaladas$(RESET)"; \
	fi
	@echo "$(GREEN)✅ Dependencias instaladas$(RESET)"

.PHONY: setup-docker
setup-docker: ## 📦 Preparar servicios Docker
	@echo "$(YELLOW)🐳 Preparando servicios Docker...$(RESET)"
	@$(DOCKER_COMPOSE) pull postgres redis clickhouse/clickhouse-server
	@echo "$(GREEN)✅ Imágenes Docker descargadas$(RESET)"

# =============================================================================
# GESTIÓN DE DATOS E IMÁGENES
# =============================================================================

.PHONY: seed
seed: ## 🗄️ Pipeline completo de carga de datos (transform → seed → verify)
	@echo "$(CYAN)🌱 Iniciando pipeline de carga de datos...$(RESET)"
	@$(MAKE) transform-paths
	@$(MAKE) load-questions
	@$(MAKE) verify-integrity
	@echo "$(GREEN)✅ Pipeline de datos completado$(RESET)"

.PHONY: transform-paths
transform-paths: ## 🗄️ Transformar rutas del Excel a relativas
	@echo "$(YELLOW)🔄 Transformando rutas de imágenes...$(RESET)"
	@if [ ! -f "$(EXCEL_MAIN)" ]; then \
		echo "$(RED)❌ Excel principal no encontrado: $(EXCEL_MAIN)$(RESET)"; \
		exit 1; \
	fi
	@$(PYTHON) $(SCRIPTS_DIR)/path_transformer.py \
		--excel "$(EXCEL_MAIN)" \
		--inplace \
		--project-root "$(PROJECT_ROOT)"
	@echo "$(GREEN)✅ Rutas transformadas exitosamente$(RESET)"

.PHONY: verify-paths
verify-paths: ## 🗄️ Solo verificar rutas sin modificar Excel
	@echo "$(YELLOW)🔍 Verificando rutas de imágenes...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/path_transformer.py \
		--excel "$(EXCEL_MAIN)" \
		--verify \
		--project-root "$(PROJECT_ROOT)"

.PHONY: load-questions
load-questions: ## 🗄️ Cargar preguntas a base de datos con imágenes
	@echo "$(YELLOW)📚 Cargando preguntas a base de datos...$(RESET)"
	@$(MAKE) ensure-db
	@$(PYTHON) $(SCRIPTS_DIR)/seed_questions.py \
		--excel "$(EXCEL_MAIN)" \
		--with-images \
		--batch-size 500 \
		--project-root "$(PROJECT_ROOT)"
	@echo "$(GREEN)✅ Preguntas cargadas exitosamente$(RESET)"

.PHONY: load-questions-all
load-questions-all: ## 🗄️ Cargar TODAS las preguntas (con y sin imágenes)
	@echo "$(YELLOW)📚 Cargando todas las preguntas...$(RESET)"
	@$(MAKE) ensure-db
	@$(PYTHON) $(SCRIPTS_DIR)/seed_questions.py \
		--excel "$(EXCEL_MAIN)" \
		--batch-size 500 \
		--project-root "$(PROJECT_ROOT)"

.PHONY: load-sql-complete
load-sql-complete: ## 🗄️ Cargar preguntas desde archivo SQL pre-generado (RÁPIDO)
	@echo "$(YELLOW)📚 Cargando 476 preguntas desde archivo SQL...$(RESET)"
	@if [ ! -f "$(SQL_LOAD_FILE)" ]; then \
		echo "$(RED)❌ Archivo SQL no encontrado. Ejecuta: make generate-sql$(RESET)"; \
		exit 1; \
	fi
	@$(MAKE) ensure-db
	@echo "$(BLUE)📥 Ejecutando carga SQL directa...$(RESET)"
	@docker exec -i $$($(DOCKER_COMPOSE) ps -q postgres) psql -U gameplay -d icfes_leveling < "$(SQL_LOAD_FILE)" || \
		psql -h localhost -p 5432 -U gameplay -d icfes_leveling -f "$(SQL_LOAD_FILE)"
	@echo "$(GREEN)✅ 476 preguntas cargadas exitosamente desde SQL$(RESET)"

.PHONY: generate-sql
generate-sql: ## 🗄️ Generar archivo SQL para carga rápida (476 preguntas)
	@echo "$(YELLOW)⚙️ Generando archivo SQL desde Excel...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/offline_sql_generator.py
	@echo "$(GREEN)✅ Archivo SQL generado: $(SQL_LOAD_FILE)$(RESET)"

# =============================================================================
# VALIDACIONES DE PRODUCCIÓN
# =============================================================================

.PHONY: validate-all
validate-all: ## 🔍 Ejecutar todas las validaciones de producción
	@echo "$(CYAN)🔍 Iniciando validaciones completas de producción...$(RESET)"
	@$(MAKE) validate-data
	@$(MAKE) validate-sql
	@$(MAKE) validate-performance
	@echo "$(GREEN)✅ Validaciones de producción completadas$(RESET)"

.PHONY: validate-data
validate-data: ## 🔍 Validar integridad de datos y archivos
	@echo "$(YELLOW)📊 Validando integridad de datos...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/production_validator.py
	@echo "$(GREEN)✅ Validación de datos completada$(RESET)"

.PHONY: validate-sql
validate-sql: ## 🔍 Validar lógica SQL y consultas críticas
	@echo "$(YELLOW)🗃️ Validando lógica SQL...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/validate_sql_logic.py
	@echo "$(GREEN)✅ Validación SQL completada$(RESET)"

.PHONY: validate-performance
validate-performance: ## 🔍 Validar performance y métricas críticas
	@echo "$(YELLOW)⚡ Validando performance del sistema...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/validate_performance.py
	@echo "$(GREEN)✅ Validación de performance completada$(RESET)"

.PHONY: validate-security
validate-security: ## 🔍 Validar medidas de seguridad implementadas
	@echo "$(YELLOW)🔒 Validando seguridad del sistema...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/validate_security.py
	@echo "$(GREEN)✅ Validación de seguridad completada$(RESET)"

.PHONY: health-check
health-check: ## 🩺 Health check rápido del sistema
	@echo "$(YELLOW)🩺 Ejecutando health check...$(RESET)"
	@echo "$(BLUE)📋 Verificando archivos críticos...$(RESET)"
	@test -f "$(SQL_LOAD_FILE)" && echo "$(GREEN)✅ SQL file exists$(RESET)" || echo "$(RED)❌ SQL file missing$(RESET)"
	@test -d "$(DATABASE_DIR)/allquestions" && echo "$(GREEN)✅ Images directory exists$(RESET)" || echo "$(RED)❌ Images directory missing$(RESET)"
	@echo "$(BLUE)📋 Contando recursos...$(RESET)"
	@find "$(DATABASE_DIR)/allquestions" -name "*.png" -o -name "*.jpg" | wc -l | xargs -I {} echo "$(GREEN)✅ {} imágenes encontradas$(RESET)"
	@echo "$(GREEN)✅ Health check completado$(RESET)"

.PHONY: verify-integrity
verify-integrity: ## 🗄️ Verificar integridad de archivos multimedia
	@echo "$(YELLOW)🔍 Verificando integridad de assets...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/verify_assets.py \
		--excel "$(EXCEL_MAIN)" \
		--output-dir reports \
		--project-root "$(PROJECT_ROOT)"
	@echo "$(GREEN)✅ Verificación de integridad completada$(RESET)"

.PHONY: create-placeholders
create-placeholders: ## 🗄️ Crear placeholders para imágenes faltantes
	@echo "$(YELLOW)🖼️ Creando placeholders para imágenes faltantes...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/verify_assets.py \
		--excel "$(EXCEL_MAIN)" \
		--output-dir reports \
		--create-placeholders \
		--project-root "$(PROJECT_ROOT)"

# =============================================================================
# SERVICIOS Y EJECUCIÓN
# =============================================================================

.PHONY: run
run: ## 🚀 Levantar todos los servicios (desarrollo)
	@echo "$(CYAN)🚀 Levantando servicios ICFES Leveling...$(RESET)"
	@$(MAKE) ensure-env
	@$(DOCKER_COMPOSE) up -d postgres redis clickhouse
	@echo "$(YELLOW)⏳ Esperando que los servicios estén listos...$(RESET)"
	@sleep 10
	@$(DOCKER_COMPOSE) up -d backend frontend websocket ai-service
	@echo ""
	@echo "$(GREEN)✅ Servicios levantados exitosamente$(RESET)"
	@echo ""
	@echo "$(CYAN)📋 Acceso a servicios:$(RESET)"
	@echo "  🌐 Frontend:     http://localhost:4001"
	@echo "  🔧 Backend API:  http://localhost:4000"
	@echo "  📚 API Docs:     http://localhost:4000/docs"
	@echo "  🔌 WebSocket:    ws://localhost:4002"
	@echo "  🤖 AI Service:   http://localhost:8002"

.PHONY: run-local
run-local: ## 🚀 Ejecutar en modo local (sin Docker)
	@echo "$(CYAN)🏠 Ejecutando localmente...$(RESET)"
	@./start-local.sh

.PHONY: stop
stop: ## 🚀 Detener todos los servicios
	@echo "$(YELLOW)⏹️ Deteniendo servicios...$(RESET)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Servicios detenidos$(RESET)"

.PHONY: restart
restart: ## 🚀 Reiniciar todos los servicios
	@$(MAKE) stop
	@$(MAKE) run

.PHONY: logs
logs: ## 🚀 Ver logs de todos los servicios
	@$(DOCKER_COMPOSE) logs -f

.PHONY: logs-backend
logs-backend: ## 🚀 Ver logs solo del backend
	@$(DOCKER_COMPOSE) logs -f backend

.PHONY: logs-frontend
logs-frontend: ## 🚀 Ver logs solo del frontend
	@$(DOCKER_COMPOSE) logs -f frontend

.PHONY: status
status: ## 🚀 Verificar estado de servicios
	@echo "$(CYAN)📊 Estado de servicios:$(RESET)"
	@$(DOCKER_COMPOSE) ps

# =============================================================================
# TESTING Y VALIDACIÓN
# =============================================================================

.PHONY: test
test: ## 🧪 Ejecutar todos los tests
	@echo "$(CYAN)🧪 Ejecutando tests completos...$(RESET)"
	@$(MAKE) test-services
	@$(MAKE) test-render
	@$(MAKE) test-flow
	@echo "$(GREEN)✅ Todos los tests completados$(RESET)"

.PHONY: test-services
test-services: ## 🧪 Test de conectividad de servicios
	@echo "$(YELLOW)🔌 Testeando conectividad de servicios...$(RESET)"
	@curl -f http://localhost:4000/health || (echo "$(RED)❌ Backend no responde$(RESET)" && exit 1)
	@curl -f http://localhost:4001 || (echo "$(RED)❌ Frontend no responde$(RESET)" && exit 1)
	@echo "$(GREEN)✅ Servicios responden correctamente$(RESET)"

.PHONY: test-render
test-render: ## 🧪 Test E2E de renderizado de imágenes
	@echo "$(YELLOW)🖼️ Testeando renderizado de imágenes...$(RESET)"
	@$(PYTHON) -c "import requests; r = requests.get('http://localhost:4000/media/images/question/test.png'); print('✅ Servicio media OK' if r.status_code in [200, 404] else '❌ Error en servicio media')"

.PHONY: test-flow
test-flow: ## 🧪 Test de flujo completo estudiante
	@echo "$(YELLOW)👤 Testeando flujo completo estudiante...$(RESET)"
	@if [ -f test_complete_flow.py ]; then \
		$(PYTHON) test_complete_flow.py; \
	else \
		echo "$(YELLOW)⚠️ Script de test de flujo no encontrado$(RESET)"; \
	fi

.PHONY: test-db
test-db: ## 🧪 Test de conexión a base de datos
	@echo "$(YELLOW)🗄️ Testeando conexión a base de datos...$(RESET)"
	@$(DOCKER_COMPOSE) exec -T postgres pg_isready -U gameplay -d gameplay_db || \
		(echo "$(RED)❌ PostgreSQL no está listo$(RESET)" && exit 1)
	@echo "$(GREEN)✅ PostgreSQL conectado correctamente$(RESET)"

# =============================================================================
# MANTENIMIENTO Y LIMPIEZA
# =============================================================================

.PHONY: clean
clean: ## 🧹 Limpiar archivos temporales y cache
	@echo "$(YELLOW)🧹 Limpiando archivos temporales...$(RESET)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -prune -o -name "*.log" -delete 2>/dev/null || true
	@rm -rf reports/*.json reports/*.csv 2>/dev/null || true
	@echo "$(GREEN)✅ Archivos temporales limpiados$(RESET)"

.PHONY: clean-docker
clean-docker: ## 🧹 Limpiar contenedores e imágenes Docker
	@echo "$(YELLOW)🐳 Limpiando Docker...$(RESET)"
	@$(DOCKER_COMPOSE) down --volumes --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)✅ Docker limpiado$(RESET)"

.PHONY: clean-all
clean-all: ## 🧹 Limpieza completa (archivos + Docker)
	@$(MAKE) clean
	@$(MAKE) clean-docker

.PHONY: reset-db
reset-db: ## 🧹 Reiniciar base de datos (⚠️ DESTRUCTIVO)
	@echo "$(RED)⚠️ ATENCIÓN: Esto eliminará TODOS los datos de la BD$(RESET)"
	@read -p "¿Estás seguro? [y/N]: " confirm && [ "$$confirm" = "y" ]
	@$(DOCKER_COMPOSE) down -v
	@$(DOCKER_COMPOSE) up -d postgres redis clickhouse
	@sleep 10
	@echo "$(GREEN)✅ Base de datos reiniciada$(RESET)"

# =============================================================================
# COMANDOS DE UTILIDAD
# =============================================================================

.PHONY: backup
backup: ## 💾 Crear backup de la base de datos
	@echo "$(YELLOW)💾 Creando backup...$(RESET)"
	@mkdir -p backups
	@$(DOCKER_COMPOSE) exec -T postgres pg_dump -U gameplay gameplay_db > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup creado en backups/$(RESET)"

.PHONY: restore
restore: ## 💾 Restaurar backup de BD (especificar BACKUP=archivo.sql)
	@if [ -z "$(BACKUP)" ]; then \
		echo "$(RED)❌ Especifica archivo: make restore BACKUP=archivo.sql$(RESET)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)📥 Restaurando backup $(BACKUP)...$(RESET)"
	@$(DOCKER_COMPOSE) exec -T postgres psql -U gameplay -d gameplay_db < $(BACKUP)
	@echo "$(GREEN)✅ Backup restaurado$(RESET)"

.PHONY: shell-backend
shell-backend: ## 🔧 Shell interactivo en contenedor backend
	@$(DOCKER_COMPOSE) exec backend /bin/bash

.PHONY: shell-db
shell-db: ## 🔧 Shell interactivo en PostgreSQL
	@$(DOCKER_COMPOSE) exec postgres psql -U gameplay -d gameplay_db

.PHONY: monitor
monitor: ## 📊 Monitorear recursos del sistema
	@$(DOCKER_COMPOSE) exec backend top

# =============================================================================
# COMANDOS INTERNOS
# =============================================================================

.PHONY: ensure-env
ensure-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)❌ Archivo .env no encontrado. Ejecuta: make create-env$(RESET)"; \
		exit 1; \
	fi

.PHONY: ensure-db
ensure-db:
	@echo "$(YELLOW)🔍 Verificando disponibilidad de BD...$(RESET)"
	@$(DOCKER_COMPOSE) up -d postgres redis clickhouse
	@timeout=30; \
	while ! $(DOCKER_COMPOSE) exec -T postgres pg_isready -U gameplay -d gameplay_db >/dev/null 2>&1; do \
		if [ $$timeout -eq 0 ]; then \
			echo "$(RED)❌ Timeout esperando PostgreSQL$(RESET)"; \
			exit 1; \
		fi; \
		echo "$(YELLOW)⏳ Esperando PostgreSQL... ($$timeout s)$(RESET)"; \
		sleep 2; \
		timeout=$$((timeout-2)); \
	done
	@echo "$(GREEN)✅ Base de datos disponible$(RESET)"

# =============================================================================
# INFORMACIÓN DEL PROYECTO
# =============================================================================

.PHONY: info
info: ## ℹ️ Información del proyecto
	@echo ""
	@echo "$(CYAN)🎯 ICFES Leveling - Sistema Educativo Gamificado$(RESET)"
	@echo "$(CYAN)===============================================$(RESET)"
	@echo ""
	@echo "$(GREEN)📁 Estructura del proyecto:$(RESET)"
	@echo "  • $(BACKEND_DIR)  - FastAPI Backend"
	@echo "  • $(FRONTEND_DIR) - Next.js Frontend"
	@echo "  • $(DATABASE_DIR)  - Datos y SQL"
	@echo "  • $(SCRIPTS_DIR)   - Scripts de automatización"
	@echo ""
	@echo "$(GREEN)🗃️ Archivos de datos:$(RESET)"
	@echo "  • Excel principal: $(EXCEL_MAIN)"
	@echo "  • Imágenes: $(IMAGES_DIR)"
	@echo ""
	@echo "$(GREEN)🔗 Servicios (cuando esté ejecutándose):$(RESET)"
	@echo "  • Frontend:    http://localhost:4001"
	@echo "  • Backend:     http://localhost:4000"  
	@echo "  • API Docs:    http://localhost:4000/docs"
	@echo "  • PostgreSQL:  localhost:5433"
	@echo "  • Redis:       localhost:6379"
	@echo "  • ClickHouse:  localhost:8123"
	@echo ""

# =============================================================================
# COMANDOS RÁPIDOS (ALIASES)
# =============================================================================

.PHONY: up
up: run ## 🚀 Alias para 'make run'

.PHONY: down  
down: stop ## 🚀 Alias para 'make stop'

.PHONY: build
build: setup ## 📦 Alias para 'make setup'

.PHONY: install
install: setup ## 📦 Alias para 'make setup'