# 🚀 GUÍA RÁPIDA - Sistema Experto ESP32

## ⚡ Inicio Rápido (3 pasos)

### 1️⃣ Configurar Variables
```bash
export TELEGRAM_TOKEN="tu_token"
export MQTT_HOST="broker.hivemq.cloud"
export MQTT_USER="usuario"
export MQTT_PASS="password"
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="tu_key"
```

### 2️⃣ Ejecutar SQL en Supabase
```sql
CREATE TABLE expert_analysis (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    estado_general TEXT NOT NULL,
    severidad_maxima TEXT NOT NULL,
    total_reglas INTEGER DEFAULT 0,
    diagnostico_completo JSONB,
    temperatura_actual DECIMAL(5,2),
    humedad_actual DECIMAL(5,2),
    problemas JSONB,
    recomendaciones JSONB
);
```

### 3️⃣ Iniciar Servicios
```bash
chmod +x start.sh
./start.sh
```

## 📁 Archivos del Sistema

| Archivo | Descripción | Líneas |
|---------|-------------|--------|
| `expert_system.py` | Motor de reglas (30+ reglas) | ~400 |
| `expert_service.py` | Servicio MQTT/Supabase | ~275 |
| `bot_completo.py` | Bot Telegram (ya existente) | - |
| `test_expert_system.py` | Suite de pruebas | ~340 |
| `start.sh` | Script de inicio | ~180 |
| `README.md` | Documentación completa | - |

## 🧠 Sistema Experto - Categorías de Reglas

### 🌡️ Temperatura (7 reglas)
```
R001 ❗ Crítica alta (> tempMax)
R002 ❗ Crítica baja (< tempMin)
R003 ⚠️  Alta advertencia (cerca de máx)
R004 ⚠️  Baja advertencia (cerca de mín)
R005 ⚠️  Muy por encima de setpoint
R006 ⚠️  Muy por debajo de setpoint
R007 ✅ En rango óptimo
```

### 💧 Humedad (5 reglas)
```
R101 ❗ Crítica alta (> 85%)
R102 ❗ Crítica baja (< 20%)
R103 ⚠️  Alta (70-85%)
R104 ⚠️  Baja (20-30%)
R105 ✅ Óptima (40-60%)
```

### 🔌 Dispositivos (5 reglas)
```
R201 ❗ Ventilador + Calefactor simultáneos
R202 ❗ Todos apagados con temp fuera de rango
R203 ⚠️  Ventilador sin efecto
R204 ⚠️  Calefactor sin efecto
R205 ❗ Modo manual con condiciones críticas
```

### ⚡ Eficiencia (3 reglas)
```
R301 ✅ Operación eficiente
R302 ⚠️  Histéresis muy pequeña
R303 ⚠️  Histéresis muy grande
```

### 🚨 Alertas (2+ reglas)
```
R401 ❗ Múltiples alertas activas
R402 ⚠️  Rango de alertas muy estrecho
```

## 🎯 Estados del Sistema

| Estado | Color | Descripción |
|--------|-------|-------------|
| **Óptimo** | 🟢 | Todo perfecto |
| **Aceptable** | 🟡 | Advertencias menores |
| **Problemático** | 🟠 | Requiere atención |
| **Crítico** | 🔴 | Acción inmediata |

## 🔥 Severidades

| Nivel | Acción | Tiempo de Respuesta |
|-------|--------|---------------------|
| **Baja** | Monitorear | - |
| **Media** | Revisar en 1 hora | 1h |
| **Alta** | Revisar en 15 min | 15m |
| **Crítica** | Inmediato | AHORA |

## 📊 Dashboard - Secciones

1. **🧠 Análisis IA**
   - Tendencias
   - Predicciones
   - Diagnóstico inteligente

2. **⚙️ Sistema Experto** ← NUEVO
   - Estado general
   - Reglas activadas
   - Problemas y recomendaciones

3. **🌡️ Clima Actual**
   - Temperatura/Humedad
   - Última actualización

4. **📈 Historial**
   - Gráficos en tiempo real
   - Últimos 20 registros

5. **🔌 Dispositivos**
   - Estado ON/OFF
   - Modo operación

6. **⚙️ Configuración**
   - Setpoint
   - Límites de alerta

## ⏱️ Intervalos de Actualización

| Componente | Intervalo | Descripción |
|------------|-----------|-------------|
| Dashboard (datos) | 5s | Temp/Hum actual |
| Dashboard (gráficos) | 5s | Histórico |
| Dashboard (relays) | 10s | Dispositivos |
| Dashboard (config) | 15s | Configuración |
| Sistema Experto | 30s | Análisis completo |
| Análisis IA | 60s | Claude AI |

## 🧪 Probar el Sistema

```bash
# Probar motor de reglas
python3 test_expert_system.py

# Ver análisis en vivo
python3 expert_service.py

# Verificar tabla en Supabase
# En SQL Editor:
SELECT * FROM expert_analysis ORDER BY created_at DESC LIMIT 5;
```

## 🎮 Comandos del Bot

### Control de Límites
```
"temperatura mínima 18"    # Configura límite inferior
"temperatura máxima 30"    # Configura límite superior
"cambia setpoint a 25"     # Cambia temperatura objetivo
```

### Consultas
```
"temperatura"              # Ver temperatura
"estado"                   # Estado completo
"dispositivos"             # Ver relays
"configuración"            # Ver config
```

### Control de Dispositivos
```
"enciende ventilador"      # Encender
"apaga calefactor"         # Apagar
"modo ventilador automático"  # Cambiar modo
```

## 🔧 Troubleshooting

### Sistema Experto no actualiza
```bash
# Verificar servicio
python3 expert_service.py

# Ver última entrada
SELECT created_at, estado_general, severidad_maxima 
FROM expert_analysis 
ORDER BY created_at DESC LIMIT 1;
```

### Dashboard muestra "No hay análisis"
1. Esperar 30s después de iniciar
2. Verificar SUPABASE_URL y SUPABASE_KEY
3. Abrir DevTools (F12) y ver errores

### Reglas no se activan
```bash
# Probar motor directamente
python3 expert_system.py

# Ajustar umbrales en expert_system.py
# Modificar ANALYSIS_INTERVAL en expert_service.py
```

## 📈 Flujo de Datos

```
ESP32 → MQTT → Expert Service → Evaluación → Supabase → Dashboard
          ↓                         ↓
        Bot Telegram           30+ Reglas
```

## 🎨 Personalización

### Agregar Nueva Regla
```python
# En expert_system.py, método _cargar_reglas():
{
    'id': 'R999',
    'nombre': 'Mi nueva regla',
    'severidad': 'media',
    'condicion': lambda d: d['temp'] > 35,
    'accion': 'Descripción del problema',
    'recomendacion': 'Qué hacer',
    'tipo': 'temperatura'
}
```

### Cambiar Intervalo de Análisis
```python
# En expert_service.py:
ANALYSIS_INTERVAL = 30  # Cambiar a los segundos deseados
```

## 📞 Soporte

1. Revisar README.md completo
2. Ejecutar test_expert_system.py
3. Verificar logs de cada servicio
4. Consultar troubleshooting

## 🎉 ¡Listo!

Tu sistema experto está configurado y listo para:
- ✅ Evaluar 30+ reglas automáticamente
- ✅ Detectar problemas en tiempo real
- ✅ Generar recomendaciones inteligentes
- ✅ Visualizar todo en el dashboard
- ✅ Alertar condiciones críticas

**¡A monitorear! 🚀**