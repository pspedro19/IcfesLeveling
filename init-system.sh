#!/bin/bash

# =============================================================================
# ICFES LEVELING - Inicialización Automática del Sistema
# Este script se ejecuta automáticamente al levantar Docker Compose
# =============================================================================

echo "🚀 ICFES LEVELING - Iniciando configuración automática..."

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 30

# Ejecutar configuración completa
echo "🔧 Ejecutando configuración completa del sistema..."
if [ -f "/root/IcfesLeveling/scripts/setup-complete-system.sh" ]; then
    /root/IcfesLeveling/scripts/setup-complete-system.sh
else
    echo "❌ Script de configuración no encontrado"
    exit 1
fi

echo "✅ Sistema ICFES LEVELING configurado exitosamente"