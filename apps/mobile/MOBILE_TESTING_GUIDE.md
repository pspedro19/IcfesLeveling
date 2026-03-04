# 🧪 Guía de Pruebas Móviles (Frontend + Backend)

Esta guía explica cómo orquestar las pruebas para asegurar que la aplicación Flutter se comunique correctamente con el backend FastAPI.

---

## 🏗️ 1. El Rol de Docker
**Docker no se usa para desplegar la app móvil en el teléfono**, pero es vital para el **Backend**.
- **Para qué sirve**: Para levantar la base de datos, Redis, y la API en un entorno controlado y reproducible.
- **Comando**:
  ```bash
  docker-compose up -to-build backend db redis
  ```

---

## 📱 2. Preparación del Frontend (Flutter)

### Conectividad (El punto más importante)
Si usas el **Android Emulator**, `localhost` o `127.0.0.1` se refiere al propio emulador, no a tu PC.
- **Android Emulator**: Usa `10.0.2.2` para acceder al backend en tu PC.
- **iOS Simulator**: Puedes usar `localhost`.
- **Dispositivo Físico**: Usa la dirección IP de tu PC (ej. `192.168.1.15`).

**Configuración en el código:**
Actualiza `lib/core/constants/api_constants.dart`:
```dart
static const String baseUrl = 'http://10.0.2.2:4000/api/v1'; // Para Android Emulator
```

---

## 🛠️ 3. Pasos para Probar

### Paso A: Levantar el Backend
Asegúrate de que las migraciones estén aplicadas:
1.  Inicia el backend (vía Docker o localmente).
2.  Verifica el acceso a la documentación en `http://localhost:4000/docs`.

### Paso B: Ejecutar Flutter
Desde la carpeta `apps/mobile`:
1.  **Limpiar y obtener paquetes**: 
    ```bash
    flutter pub get
    ```
2.  **Lanzar la app**: 
    ```bash
    flutter run
    ```

---

## 👁️ 4. Cómo ver Distintas Vistas
Para navegar rápidamente entre vistas durante el desarrollo sin pasar por todo el flujo de login:

1.  **GoRouter**: Puedes cambiar la ruta inicial en `lib/main.dart` o `lib/app/app_router.dart`.
2.  **Hot Reload**: Flutter permite ver cambios en la UI casi instantáneamente.
3.  **Device Preview** (Opcional): Si quieres ver cómo queda la app en distintos tamaños de pantalla (iPhone, iPad, Android) simultáneamente, puedes añadir el paquete `device_preview` a `pubspec.yaml`.

---

## 📶 5. Probando el Modo Offline
Para validar que mi lógica de **Offline-First** funciona:
1.  **Simular Desconexión**: Desactiva el WiFi en el emulador/simulator.
2.  **Realizar Acciones**: Responde preguntas o usa corazones. Deberías ver un mensaje de "Acción encolada".
3.  **Reconexión**: Activa el WiFi. El `SyncManager` detectará el cambio y subirá las acciones pendientes automáticamente.
4.  **Verificación**: Revisa los logs del backend para confirmar que las peticiones llegaron después de la reconexión.
