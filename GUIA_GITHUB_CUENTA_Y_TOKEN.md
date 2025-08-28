# 🔐 GUÍA COMPLETA: CREAR CUENTA GITHUB Y GENERAR TOKEN

## 📝 PARTE 1: CREAR CUENTA NUEVA EN GITHUB

### 1️⃣ **Ir a GitHub**
```
https://github.com
```

### 2️⃣ **Click en "Sign up" (esquina superior derecha)**

### 3️⃣ **Completar el proceso de registro**

**Paso 1 - Email:**
```
Enter your email: tu_email@gmail.com
```
- Click "Continue"

**Paso 2 - Password:**
```
Create a password: TuPassword123!Seguro
```
- Mínimo 8 caracteres
- Debe incluir números y letras
- Click "Continue"

**Paso 3 - Username:**
```
Enter a username: tunombre-apellido-2025
```
- Ejemplo: pedro-perez-2025
- Click "Continue"

**Paso 4 - Verificación:**
```
Would you like to receive product updates? → n (opcional)
```
- Resolver el puzzle/captcha
- Click "Create account"

### 4️⃣ **Verificar email**
- Revisar tu correo
- Copiar el código de 6 dígitos
- Pegar en GitHub
- Click "Verify"

### 5️⃣ **Configuración inicial (opcional)**
- Puedes hacer click en "Skip personalization"

---

## 🔑 PARTE 2: GENERAR PERSONAL ACCESS TOKEN

### 1️⃣ **Ir a Settings (Configuración)**
- Click en tu foto de perfil (esquina superior derecha)
- Click en "Settings"

### 2️⃣ **Ir a Developer settings**
- Scroll hasta el final del menú lateral izquierdo
- Click en "Developer settings"

### 3️⃣ **Personal access tokens**
- Click en "Personal access tokens"
- Click en "Tokens (classic)"

### 4️⃣ **Generate new token**
- Click en "Generate new token"
- Click en "Generate new token (classic)"

### 5️⃣ **Configurar el token**

**Note (Nombre del token):**
```
IcfesLeveling-Project-2025
```

**Expiration (Expiración):**
```
90 days (o "No expiration" para permanente)
```

**Select scopes (Permisos):**
Marcar las siguientes casillas:
- ✅ **repo** (acceso completo a repositorios privados)
  - ✅ repo:status
  - ✅ repo_deployment
  - ✅ public_repo
  - ✅ repo:invite
- ✅ **workflow** (actualizar GitHub Actions)
- ✅ **write:packages** (si usas packages)
- ✅ **admin:org** (si trabajas con organizaciones)
- ✅ **gist** (crear gists)
- ✅ **user** (leer perfil de usuario)
  - ✅ read:user
  - ✅ user:email

### 6️⃣ **Generar el token**
- Scroll hasta abajo
- Click en "Generate token" (botón verde)

### 7️⃣ **⚠️ COPIAR EL TOKEN INMEDIATAMENTE**
```
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**IMPORTANTE:** 
- 🚨 **COPIA EL TOKEN AHORA** - No lo podrás ver de nuevo
- 📋 Guárdalo en un lugar seguro (gestor de contraseñas)
- 🔒 NO lo compartas con nadie
- 📝 NO lo subas a repositorios públicos

---

## 🖥️ PARTE 3: CONFIGURAR GIT EN TU COMPUTADORA

### 1️⃣ **Configurar nombre y email**
```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu_email@gmail.com"
```

**Ejemplo:**
```bash
git config --global user.name "Pedro Perez"
git config --global user.email "pedro.perez@gmail.com"
```

### 2️⃣ **Usar el token para autenticación**

**Opción A - Al hacer push (recomendado para Windows):**
```bash
# Cuando hagas git push, te pedirá:
Username: tu-usuario-github
Password: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # (pegar tu token aquí)
```

**Opción B - Guardar credenciales:**
```bash
# Windows
git config --global credential.helper manager

# macOS
git config --global credential.helper osxkeychain

# Linux
git config --global credential.helper store
```

---

## 🚀 PARTE 4: SUBIR TU PROYECTO A GITHUB

### 1️⃣ **Crear repositorio nuevo en GitHub**
- Click en "+" (esquina superior derecha)
- Click en "New repository"
- Configurar:
  ```
  Repository name: IcfesLeveling
  Description: Sistema de nivelación ICFES con IA
  Public/Private: Private (recomendado)
  ```
- NO marcar "Initialize this repository with a README"
- Click "Create repository"

### 2️⃣ **En tu computadora (Git Bash o CMD):**
```bash
# Ir a la carpeta del proyecto
cd "C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling\New folder\IcfesLeveling"

# Inicializar git (si no está inicializado)
git init

# Agregar todos los archivos
git add .

# Crear commit inicial
git commit -m "Initial commit: ICFES Leveling System"

# Agregar repositorio remoto
git remote add origin https://github.com/TU-USUARIO/IcfesLeveling.git

# Subir al repositorio
git push -u origin main
```

**Cuando pida credenciales:**
```
Username: tu-usuario-github
Password: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Tu token
```

---

## 📋 COMANDOS ÚTILES

### **Ver estado:**
```bash
git status
```

### **Ver configuración actual:**
```bash
git config --list
```

### **Cambiar URL remota (si necesitas usar token):**
```bash
git remote set-url origin https://TU-TOKEN@github.com/TU-USUARIO/IcfesLeveling.git
```
**Ejemplo:**
```bash
git remote set-url origin https://ghp_xxxxxxxxxxxx@github.com/pedro-perez-2025/IcfesLeveling.git
```

### **Clonar con token:**
```bash
git clone https://ghp_xxxxxxxxxxxx@github.com/TU-USUARIO/IcfesLeveling.git
```

---

## 🔧 TROUBLESHOOTING

### **Error: "Authentication failed"**
```
Solución: Asegúrate de usar el TOKEN, no tu contraseña de GitHub
```

### **Error: "Personal access token requires repo scope"**
```
Solución: Genera un nuevo token con los permisos correctos
```

### **Error: "remote: Invalid username or password"**
```
Solución: 
1. Verifica que estás usando el token correcto
2. Regenera el token si es necesario
3. Usa: git config --global credential.helper manager
```

---

## 🔒 SEGURIDAD

### **Crear archivo .gitignore:**
```bash
# Crear archivo .gitignore en la raíz del proyecto
echo "# Secrets and tokens
.env
*.env
.env.*
config/secrets.json
**/token.txt
**/credentials.json

# Node
node_modules/
npm-debug.log*

# Python
__pycache__/
*.py[cod]
*$py.class
.Python
env/
venv/

# Docker
.docker/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db" > .gitignore
```

### **NUNCA hagas esto:**
```bash
# ❌ MAL - No hardcodees tokens
git remote add origin https://ghp_xxxx@github.com/usuario/repo.git

# ✅ BIEN - Usa prompt de credenciales
git remote add origin https://github.com/usuario/repo.git
```

---

## ✅ VERIFICACIÓN

### **Test rápido:**
1. Crear un archivo test
   ```bash
   echo "Test" > test.txt
   ```

2. Subirlo a GitHub
   ```bash
   git add test.txt
   git commit -m "Test commit"
   git push
   ```

3. Verificar en GitHub.com que el archivo aparece

### **Si funciona:**
- ✅ El token está configurado correctamente
- ✅ Puedes hacer push/pull sin problemas
- ✅ Tu proyecto está respaldado en GitHub

---

## 🎉 ¡LISTO!

Ahora tienes:
1. ✅ Cuenta de GitHub creada
2. ✅ Personal Access Token generado
3. ✅ Git configurado localmente
4. ✅ Capacidad de subir tu proyecto

**Próximos pasos recomendados:**
- Crear README.md con documentación
- Configurar GitHub Actions para CI/CD
- Invitar colaboradores si trabajas en equipo
- Configurar branch protection rules

---

## 📚 RECURSOS ADICIONALES

- [Documentación oficial de GitHub](https://docs.github.com)
- [Crear y gestionar tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)