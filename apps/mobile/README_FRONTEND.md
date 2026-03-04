# ICFES Leveling - Frontend (Mobile App)

## 📱 Descripción General
Esta es la aplicación móvil oficial de la plataforma **ICFES Leveling**, desarrollada con **Flutter**. La aplicación está diseñada bajo una filosofía **Offline-First**, permitiendo a los estudiantes practicar para el examen ICFES incluso sin conexión a internet, con un sistema de **Aprendizaje Adaptativo** y **Gamificación**.

---

## 🏗️ Arquitectura
La aplicación sigue los principios de **Clean Architecture** combinados con **Riverpod** para la gestión de estado reactiva.

### Capas:
1.  **Domain (Capa de Negocio)**: Contiene Entidades (`Entities`), Repositorios (interfaces) y Casos de Uso (`UseCases`). Es independiente de cualquier framework.
2.  **Data (Capa de Datos)**: Implementa los repositorios. Contiene Modelos (`Models`), Fuentes de Datos de Remotas (`RemoteDataSources`) y Locales (`LocalDataSources`).
3.  **Presentation (Capa de Interfaz)**: Contiene las Páginas (`Pages`), Widgets y Providers de Riverpod (`Notifiers`).

---

## 📁 Estructura de Carpetas

### `lib/core/`
Infraestructura compartida y utilidades base.
- **`network/`**: Configuración de `Dio`, `ApiClient` e Interceptores.
  - `auth_interceptor.dart`: Inyecta tokens JWT.
  - `offline_interceptor.dart`: Detecta fallos de red y encola acciones.
- **`sync/`**: Gestión de sincronización offline.
  - `sync_manager.dart`: Orquestador de subida de datos.
  - `action_queue.dart`: Cola de acciones pendientes en Hive.
- **`storage/`**: Persistencia local.
  - `question_cache.dart`: Gestión de caché de preguntas para modo offline.
- **`constants/`**: Endpoints de la API y constantes globales.

### `lib/features/`
Módulos funcionales independientes. Cada uno sigue la estructura *Domain/Data/Presentation*.
- **`auth/`**: Login, registro y persistencia de sesión.
- **`practice/`**: Motor central de aprendizaje, manejo de preguntas y respuestas.
- **`engagement/`**: Sistema de gamificación (Corazones, Rachas).
- **`leaderboard/`**: Ligas y ranking de usuarios.
- **`home/`**: Dashboard principal y estado de sincronización.

---

## 🔌 Estrategia Offline-First

La aplicación garantiza la continuidad del estudio mediante:
1.  **Prefetching**: Descarga lotes de preguntas (`batch`) cuando hay conexión para usarlas offline.
2.  **Interceptores de Red**: Si una acción falla por falta de internet (ej. enviar respuesta), el `OfflineInterceptor` captura el error y devuelve un `202 Accepted` de forma optimista.
3.  **Cola de Acciones (Action Queue)**: Las acciones fallidas se guardan en una caja de **Hive**.
4.  **Sincronización Automática**: El `SyncManager` escucha cambios de conectividad y sube las acciones pendientes en cuanto se restablece la conexión.

---

## 🛠️ Tecnologías Principales
- **Framework**: [Flutter](https://flutter.dev/)
- **Gestión de Estado**: [Riverpod](https://riverpod.dev/)
- **Networking**: [Dio](https://pub.dev/packages/dio)
- **Persistencia NoSQL**: [Hive](https://pub.dev/packages/hive)
- **Persistencia Segura**: [Flutter Secure Storage](https://pub.dev/packages/flutter_secure_storage)
- **Navegación**: [GoRouter](https://pub.dev/packages/go_router)

---

## 🚀 Comandos Útiles
- **Instalar dependencias**: `flutter pub get`
- **Generar código (Hive/JsonSerializable)**: `flutter pub run build_runner build --delete-conflicting-outputs`
- **Ejecutar en modo debug**: `flutter run`
