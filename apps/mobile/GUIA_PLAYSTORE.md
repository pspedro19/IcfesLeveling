# Guía Completa: Publicar ICFES Leveling en Play Store

## Requisitos Previos

- [ ] Cuenta de Google Play Console ($25 USD, pago único)
- [ ] Flutter SDK instalado
- [ ] Android Studio instalado
- [ ] Java JDK 11 o superior

---

## FASE 1: Generar Archivos Android

El proyecto actualmente solo tiene `lib/`. Necesitas generar los archivos de plataforma.

```bash
cd C:\Users\pedro\OneDrive\Documents\ICFESLEVELING\IcfesLeveling\apps\mobile

# Generar archivos de plataforma Android
flutter create --platforms=android .

# Verificar que se creó
ls android/
```

---

## FASE 2: Configurar build.gradle

### 2.1 Editar `android/app/build.gradle`

```groovy
android {
    namespace "com.icfesleveling.app"
    compileSdkVersion 34

    defaultConfig {
        applicationId "com.icfesleveling.app"
        minSdkVersion 21
        targetSdkVersion 34
        versionCode 1
        versionName "1.0.0"

        // Soporte para multidex
        multiDexEnabled true
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

### 2.2 Editar `android/app/src/main/AndroidManifest.xml`

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <!-- Permisos necesarios -->
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
    <uses-permission android:name="android.permission.VIBRATE"/>
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED"/>

    <application
        android:label="ICFES Leveling"
        android:name="${applicationName}"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:usesCleartextTraffic="false">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize">

            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>

        <!-- Firebase Messaging -->
        <meta-data
            android:name="com.google.firebase.messaging.default_notification_icon"
            android:resource="@drawable/ic_notification"/>

        <meta-data
            android:name="com.google.firebase.messaging.default_notification_channel_id"
            android:value="high_importance_channel"/>

    </application>
</manifest>
```

---

## FASE 3: Crear Keystore para Firmar

### 3.1 Generar Keystore

```bash
# Crear carpeta para keystore (FUERA del proyecto, en lugar seguro)
mkdir C:\keystores

# Generar keystore
keytool -genkey -v -keystore C:\keystores\icfes-leveling.jks -keyalg RSA -keysize 2048 -validity 10000 -alias icfes-leveling

# Te pedirá:
# - Contraseña del keystore (GUÁRDALA SEGURO)
# - Nombre y apellido
# - Organización
# - Ciudad, Estado, País
```

### 3.2 Crear `android/key.properties`

```properties
storePassword=TU_CONTRASEÑA_KEYSTORE
keyPassword=TU_CONTRASEÑA_KEY
keyAlias=icfes-leveling
storeFile=C:/keystores/icfes-leveling.jks
```

**IMPORTANTE:** Agregar a `.gitignore`:
```
android/key.properties
*.jks
```

### 3.3 Configurar Signing en `android/app/build.gradle`

```groovy
// Antes de android { }
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file('key.properties')
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}

android {
    // ... código existente ...

    signingConfigs {
        release {
            keyAlias keystoreProperties['keyAlias']
            keyPassword keystoreProperties['keyPassword']
            storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
            storePassword keystoreProperties['storePassword']
        }
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            // ... resto de config ...
        }
    }
}
```

---

## FASE 4: Configurar Firebase

### 4.1 Crear proyecto en Firebase Console

1. Ir a https://console.firebase.google.com
2. Crear nuevo proyecto "ICFES Leveling"
3. Agregar app Android con package name: `com.icfesleveling.app`
4. Descargar `google-services.json`
5. Colocar en `android/app/google-services.json`

### 4.2 Configurar gradle para Firebase

**android/build.gradle:**
```groovy
buildscript {
    dependencies {
        classpath 'com.google.gms:google-services:4.4.0'
    }
}
```

**android/app/build.gradle (al final):**
```groovy
apply plugin: 'com.google.gms.google-services'
```

---

## FASE 5: Crear Assets de la App

### 5.1 Iconos (usar Android Studio o herramientas online)

Crear iconos en estas resoluciones y colocar en:
```
android/app/src/main/res/
├── mipmap-hdpi/ic_launcher.png      (72x72)
├── mipmap-mdpi/ic_launcher.png      (48x48)
├── mipmap-xhdpi/ic_launcher.png     (96x96)
├── mipmap-xxhdpi/ic_launcher.png    (144x144)
├── mipmap-xxxhdpi/ic_launcher.png   (192x192)
```

### 5.2 Splash Screen

Editar `android/app/src/main/res/drawable/launch_background.xml`

---

## FASE 6: Build Release

### 6.1 Limpiar y Construir

```bash
cd C:\Users\pedro\OneDrive\Documents\ICFESLEVELING\IcfesLeveling\apps\mobile

# Limpiar builds anteriores
flutter clean

# Obtener dependencias
flutter pub get

# Build App Bundle (recomendado para Play Store)
flutter build appbundle --release

# El archivo estará en:
# build/app/outputs/bundle/release/app-release.aab
```

### 6.2 Alternativa: Build APK

```bash
# Para testing o distribución directa
flutter build apk --release --split-per-abi

# Genera 3 APKs optimizados:
# build/app/outputs/flutter-apk/app-armeabi-v7a-release.apk
# build/app/outputs/flutter-apk/app-arm64-v8a-release.apk
# build/app/outputs/flutter-apk/app-x86_64-release.apk
```

---

## FASE 7: Crear Cuenta en Google Play Console

### 7.1 Registro

1. Ir a https://play.google.com/console
2. Pagar $25 USD (una vez)
3. Completar información del desarrollador
4. Verificar identidad

### 7.2 Crear Nueva App

1. Click "Crear app"
2. Nombre: "ICFES Leveling"
3. Idioma: Español
4. Tipo: App
5. Gratis o de pago: Gratis

---

## FASE 8: Configurar Ficha de Play Store

### 8.1 Información Principal

| Campo | Valor Sugerido |
|-------|----------------|
| Nombre | ICFES Leveling |
| Descripción breve | Prepárate para el ICFES con gamificación |
| Descripción completa | (Ver abajo) |
| Categoría | Educación |
| Etiquetas | ICFES, Saber 11, Estudiar, Colombia |

### 8.2 Descripción Completa Sugerida

```
🎮 ICFES LEVELING - La forma divertida de prepararte para el ICFES

Transforma tu preparación para el examen ICFES Saber 11 en una aventura épica. Sube de nivel, gana XP, compite en ligas y domina todas las materias.

✨ CARACTERÍSTICAS PRINCIPALES:

📚 PRÁCTICA ADAPTATIVA
• Preguntas que se adaptan a tu nivel
• Sistema de repetición espaciada
• Retroalimentación instantánea

🔥 SISTEMA DE RACHAS
• Mantén tu racha diaria
• Multiplica tu XP con días consecutivos
• Congela tu racha si necesitas un descanso

💪 CORAZONES Y MODO GRACIA
• Sistema de vidas como en videojuegos
• Modo gracia para seguir practicando

🏆 LIGAS COMPETITIVAS
• Compite con otros estudiantes
• Sube de liga semana a semana
• Demuestra que eres el mejor

📊 DIAGNÓSTICO INTELIGENTE
• Identifica tus fortalezas y debilidades
• Plan de estudio personalizado
• Seguimiento de tu progreso

🌙 MODO OFFLINE
• Practica sin internet
• Sincronización automática

MATERIAS INCLUIDAS:
• Lectura Crítica
• Matemáticas
• Ciencias Naturales
• Sociales y Ciudadanas
• Inglés

¡Descarga ahora y comienza tu camino hacia el éxito en el ICFES!
```

### 8.3 Assets Gráficos Requeridos

| Asset | Dimensiones |
|-------|-------------|
| Icono | 512x512 PNG |
| Gráfico de funciones | 1024x500 PNG |
| Capturas de pantalla | Mínimo 2, máximo 8 |
| Video promocional | YouTube (opcional) |

---

## FASE 9: Subir App Bundle

### 9.1 Crear Release

1. Ir a "Producción" > "Crear nueva versión"
2. Subir `app-release.aab`
3. Escribir notas de la versión:
   ```
   Versión 1.0.0 - Lanzamiento inicial

   • Sistema de práctica con preguntas adaptativas
   • Diagnóstico inteligente de fortalezas y debilidades
   • Sistema de rachas y corazones
   • Ligas competitivas semanales
   • Modo offline para practicar sin internet
   ```

### 9.2 Completar Cuestionarios

Google Play requiere completar:
- [ ] Clasificación de contenido (IARC)
- [ ] Política de privacidad (URL)
- [ ] Seguridad de datos
- [ ] Público objetivo y contenido
- [ ] Anuncios (si aplica)

---

## FASE 10: Política de Privacidad

Necesitas una URL con tu política de privacidad. Ejemplo mínimo:

```html
<!-- Hospedar en tu dominio o GitHub Pages -->
<!DOCTYPE html>
<html>
<head>
    <title>Política de Privacidad - ICFES Leveling</title>
</head>
<body>
    <h1>Política de Privacidad</h1>
    <p>Última actualización: [FECHA]</p>

    <h2>Información que recopilamos</h2>
    <p>Recopilamos información necesaria para el funcionamiento de la app:</p>
    <ul>
        <li>Correo electrónico (para crear cuenta)</li>
        <li>Progreso de aprendizaje</li>
        <li>Estadísticas de uso</li>
    </ul>

    <h2>Uso de la información</h2>
    <p>Usamos esta información para:</p>
    <ul>
        <li>Personalizar tu experiencia de aprendizaje</li>
        <li>Mostrar tu progreso y estadísticas</li>
        <li>Mejorar la aplicación</li>
    </ul>

    <h2>Seguridad</h2>
    <p>Protegemos tu información con encriptación y mejores prácticas de seguridad.</p>

    <h2>Contacto</h2>
    <p>Email: soporte@icfesleveling.com</p>
</body>
</html>
```

---

## FASE 11: Revisión y Publicación

### Timeline Típico

| Etapa | Duración |
|-------|----------|
| Primera revisión | 3-7 días |
| Correcciones (si hay) | 1-3 días |
| Aprobación final | 1-2 días |

### Razones Comunes de Rechazo

1. ❌ Política de privacidad faltante o incorrecta
2. ❌ Capturas de pantalla que no coinciden con la app
3. ❌ Permisos no justificados
4. ❌ Contenido inapropiado para la edad declarada
5. ❌ Crashes en la app

---

## Checklist Final

### Antes de Subir
- [ ] `flutter analyze` sin errores
- [ ] `flutter test` pasa
- [ ] Probado en dispositivo físico
- [ ] Firebase configurado
- [ ] Keystore guardado en lugar seguro
- [ ] Icons y splash screen configurados

### En Play Console
- [ ] Información de la app completa
- [ ] Capturas de pantalla subidas
- [ ] Política de privacidad URL
- [ ] Cuestionarios completados
- [ ] App Bundle subido
- [ ] Notas de versión escritas

---

## Comandos Rápidos

```bash
# Generar plataforma Android
flutter create --platforms=android .

# Verificar proyecto
flutter doctor
flutter analyze

# Build para Play Store
flutter build appbundle --release

# Build APK para testing
flutter build apk --release

# Instalar en dispositivo conectado
flutter install --release
```

---

## Soporte

- Documentación Flutter: https://docs.flutter.dev/deployment/android
- Play Console Help: https://support.google.com/googleplay/android-developer
- Firebase Setup: https://firebase.google.com/docs/flutter/setup

---

*Guía creada para ICFES Leveling - Diciembre 2024*
