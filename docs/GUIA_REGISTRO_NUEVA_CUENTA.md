# 🚀 GUÍA COMPLETA: REGISTRO DE NUEVA CUENTA CON TOKEN

## 📋 PASO A PASO PARA CREAR NUEVA CUENTA

### 1️⃣ **Acceder a la página de registro**
```
http://localhost:4001/auth
```

### 2️⃣ **Click en "Sign Up" (Crear cuenta)**
- En la página de autenticación, hacer click en la pestaña "Sign Up"

### 3️⃣ **Completar el formulario de registro**

**Datos requeridos:**
```
Email: tu_email@ejemplo.com
Username: tu_usuario
Password: tu_contraseña123
Confirm Password: tu_contraseña123
```

**Ejemplo funcional:**
```
Email: estudiante@test.com
Username: estudiante2025
Password: Test123456!
Confirm Password: Test123456!
```

### 4️⃣ **Enviar el formulario**
- Click en el botón "Sign Up"
- El sistema creará la cuenta automáticamente

### 5️⃣ **Respuesta exitosa con TOKEN**

Cuando el registro es exitoso, recibirás:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-generado",
    "username": "estudiante2025",
    "email": "estudiante@test.com"
  }
}
```

### 6️⃣ **El token se guarda automáticamente**
- El frontend guarda el token en localStorage
- Se usa automáticamente en todas las peticiones
- Duración: 24 horas

---

## 🔐 USO DEL TOKEN

### **Automático (Frontend)**
El token se incluye automáticamente en todas las peticiones:
```javascript
headers: {
  'Authorization': `Bearer ${token}`
}
```

### **Manual (Postman/cURL)**
```bash
curl -X GET http://localhost:8001/api/v1/user/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 🎯 FLUJO COMPLETO DESPUÉS DEL REGISTRO

### 1. **Registro exitoso** → Obtienes token
### 2. **Redirección automática** → Dashboard
### 3. **Selección de materia** → Para test diagnóstico
### 4. **Test diagnóstico** → 10 preguntas
### 5. **Resultados** → Score y análisis
### 6. **Plan personalizado** → Videos recomendados
### 7. **Ver videos** → En iframe sin salir de la app

---

## 🛠️ TROUBLESHOOTING

### **Error: "Email already exists"**
```
Solución: Usar un email diferente
Ejemplo: estudiante2@test.com, estudiante3@test.com
```

### **Error: "Invalid token"**
```
Solución: Hacer login nuevamente para obtener nuevo token
```

### **Error: "Password too weak"**
```
Requisitos mínimos:
- 8 caracteres
- 1 mayúscula
- 1 número
- 1 carácter especial (opcional pero recomendado)
```

---

## 📝 EJEMPLO COMPLETO DE REGISTRO

### **1. Datos de prueba:**
```
Email: pedro.perez@estudiante.com
Username: pedroIcfes2025
Password: Icfes2025!Pass
```

### **2. Petición cURL (alternativa manual):**
```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "pedro.perez@estudiante.com",
    "username": "pedroIcfes2025",
    "password": "Icfes2025!Pass"
  }'
```

### **3. Respuesta esperada:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwZWRyb0ljZmVzMjAyNSIsImV4cCI6MTcwNDI0MDAwMH0.xyz123...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440123",
    "username": "pedroIcfes2025",
    "email": "pedro.perez@estudiante.com",
    "created_at": "2025-01-28T10:30:00",
    "is_active": true
  }
}
```

---

## 🎮 DESPUÉS DEL REGISTRO

### **Acciones disponibles con el token:**

1. **Ver perfil:**
   ```
   GET /api/v1/user/me
   ```

2. **Listar materias:**
   ```
   GET /api/v1/subjects
   ```

3. **Iniciar test diagnóstico:**
   ```
   POST /api/v1/diagnostic/start
   {
     "subject_id": "550e8400-e29b-41d4-a716-446655440001"
   }
   ```

4. **Enviar respuestas:**
   ```
   POST /api/v1/diagnostic/submit
   {
     "test_id": "test-id",
     "answers": [...]
   }
   ```

5. **Ver plan de estudio:**
   ```
   GET /api/v1/study-plan/view/{plan_id}
   ```

---

## ✅ VERIFICACIÓN RÁPIDA

### **Test de registro exitoso:**
1. Abrir navegador
2. Ir a http://localhost:4001/auth
3. Click en "Sign Up"
4. Llenar formulario con datos nuevos
5. Click en "Sign Up" button
6. Verificar redirección al dashboard
7. Verificar que aparece el username arriba a la derecha

### **El token está funcionando si:**
- ✅ Puedes ver tu nombre de usuario en el dashboard
- ✅ Puedes acceder a las materias
- ✅ Puedes iniciar un test diagnóstico
- ✅ No recibes errores 401 (Unauthorized)

---

## 🔄 RENOVACIÓN DE TOKEN

El token expira en 24 horas. Para renovar:

### **Opción 1: Login nuevamente**
```json
POST /api/v1/auth/login
{
  "username": "pedroIcfes2025",
  "password": "Icfes2025!Pass"
}
```

### **Opción 2: Refresh token (si está implementado)**
```json
POST /api/v1/auth/refresh
{
  "refresh_token": "..."
}
```

---

## 📱 ALMACENAMIENTO DEL TOKEN

### **Frontend (automático):**
```javascript
// Se guarda en:
localStorage.setItem('token', response.access_token)
localStorage.setItem('user', JSON.stringify(response.user))

// Se lee en:
const token = localStorage.getItem('token')
const user = JSON.parse(localStorage.getItem('user'))
```

### **Para verificar en consola del navegador:**
```javascript
// Abrir DevTools (F12)
// En la consola escribir:
localStorage.getItem('token')
localStorage.getItem('user')
```

---

## 🎉 ¡LISTO!

Con estos pasos puedes:
1. Crear una cuenta nueva
2. Obtener tu token de autenticación
3. Acceder a todas las funcionalidades
4. Tomar tests diagnósticos
5. Recibir planes personalizados
6. Ver videos educativos

**Nota:** Cada cuenta nueva tiene su propio progreso y recomendaciones personalizadas basadas en sus resultados del diagnóstico.