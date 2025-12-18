# 🤖 Sistema ESP32 con IA y Sistema Experto

Sistema completo de monitoreo y control ESP32 con **Inteligencia Artificial (Claude AI)** y **Sistema Experto basado en reglas**.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Sistema Experto](#-sistema-experto)
- [Dashboard](#-dashboard)
- [Solución de Problemas](#-solución-de-problemas)

## ✨ Características

### 🧠 Inteligencia Artificial (Claude AI)
- Análisis predictivo de temperatura
- Detección de tendencias
- Predicciones a 30 minutos
- Diagnóstico inteligente del sistema
- Recomendaciones personalizadas

### ⚙️ Sistema Experto
- **30+ reglas** de evaluación automática
- Categorías:
  - 🌡️ Temperatura (7 reglas)
  - 💧 Humedad (5 reglas)
  - 🔌 Dispositivos (5 reglas)
  - ⚡ Eficiencia (3 reglas)
  - 🚨 Alertas críticas (2+ reglas)
- Severidad: Crítica, Alta, Media, Baja
- Diagnóstico en tiempo real
- Recomendaciones basadas en reglas

### 🤖 Bot de Telegram
- Control por voz y texto
- Respuesta triple:
  1. Texto en Telegram
  2. Audio en Telegram
  3. Voz en parlante ESP32
- Control completo de dispositivos
- Configuración de límites de temperatura

### 📊 Dashboard Web
- Visualización en tiempo real
- Gráficos históricos
- Estado de dispositivos
- Análisis IA y Sistema Experto
- Actualización automática

## 🏗️ Arquitectura

```
┌──────────────┐
│   ESP32      │
│  (Sensores)  │
└──────┬───────┘
       │
       ↓ MQTT
┌──────────────┐
│  MQTT Broker │ ← HiveMQ Cloud
└──────┬───────┘
       │
       ├─→ Bot Telegram (bot_completo.py)
       ├─→ IA Service (ia_service.py)
       └─→ Expert Service (expert_service.py)
       │
       ↓
┌──────────────┐
│   Supabase   │ ← Base de Datos
│  (PostgreSQL)│
└──────┬───────┘
       │
       ↓
┌──────────────┐
│  Dashboard   │ ← HTML + Chart.js
│   (Web UI)   │
└──────────────┘
```

## 📦 Requisitos

### Software
- Python 3.8+
- Node.js (opcional, para testing)

### Librerías Python
```bash
pip install python-telegram-bot --break-system-packages
pip install paho-mqtt --break-system-packages
pip install supabase --break-system-packages
pip install gtts --break-system-packages
pip install speechrecognition --break-system-packages
pip install pydub --break-system-packages
pip install anthropic --break-system-packages
```

### Servicios Cloud
- **Telegram Bot Token** (de @BotFather)
- **HiveMQ Cloud** (broker MQTT)
- **Supabase** (base de datos)
- **Anthropic API Key** (para Claude AI)

## 🚀 Instalación

### 1. Clonar archivos

Coloca estos archivos en tu servidor:
- `bot_completo.py` - Bot de Telegram
- `expert_system.py` - Motor del Sistema Experto
- `expert_service.py` - Servicio del Sistema Experto
- `ia_service.py` - Servicio de IA (si lo tienes)
- `dashboard_pro.html` - Dashboard web

### 2. Configurar variables de entorno

```bash
# Telegram
export TELEGRAM_TOKEN="tu_token_aqui"

# MQTT (HiveMQ)
export MQTT_HOST="tu_broker.hivemq.cloud"
export MQTT_PORT="8883"
export MQTT_USER="tu_usuario"
export MQTT_PASS="tu_password"

# Supabase
export SUPABASE_URL="https://tu-proyecto.supabase.co"
export SUPABASE_KEY="tu_anon_key"

# Anthropic (opcional, solo para IA)
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Crear tablas en Supabase

Ejecuta este SQL en el SQL Editor de Supabase:

```sql
-- Tabla de lecturas de sensores
CREATE TABLE IF NOT EXISTS sensor_readings (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    temperatura DECIMAL(5,2) NOT NULL,
    humedad DECIMAL(5,2) NOT NULL,
    setpoint DECIMAL(5,2),
    alert_status TEXT
);

-- Tabla de configuración
CREATE TABLE IF NOT EXISTS system_config (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    setpoint DECIMAL(5,2) DEFAULT 24,
    hysteresis DECIMAL(5,2) DEFAULT 2,
    temp_max INTEGER DEFAULT 30,
    temp_min INTEGER DEFAULT 18
);

-- Tabla de estados de relays
CREATE TABLE IF NOT EXISTS relay_states (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    relay_number INTEGER NOT NULL,
    relay_name TEXT,
    state BOOLEAN NOT NULL,
    mode INTEGER DEFAULT 2
);

-- Tabla de análisis del Sistema Experto (NUEVA)
CREATE TABLE IF NOT EXISTS expert_analysis (
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

-- Tabla de análisis de IA (opcional)
CREATE TABLE IF NOT EXISTS ia_analysis (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    analisis_completo JSONB,
    temperatura_actual DECIMAL(5,2),
    humedad_actual DECIMAL(5,2)
);

-- Índices
CREATE INDEX idx_sensor_created ON sensor_readings(created_at DESC);
CREATE INDEX idx_expert_created ON expert_analysis(created_at DESC);
CREATE INDEX idx_expert_severidad ON expert_analysis(severidad_maxima);
CREATE INDEX idx_ia_created ON ia_analysis(created_at DESC);
```

## ⚙️ Configuración

### 1. Editar dashboard_pro.html

Abre `dashboard_pro.html` y actualiza las credenciales:

```javascript
const SUPABASE_URL = 'https://tu-proyecto.supabase.co';
const SUPABASE_KEY = 'tu_anon_key_aqui';
```

### 2. Verificar tópicos MQTT

Los servicios esperan estos tópicos:
- `esp32/sensores` - Datos de temperatura/humedad
- `esp32/relay/status` - Estado de dispositivos
- `esp32/config` - Configuración del sistema
- `esp32/relay/{1-4}/cmd` - Comandos ON/OFF
- `esp32/relay/{1-4}/mode` - Cambio de modo
- `esp32/config/set` - Actualizar configuración

## 🎮 Uso

### Iniciar servicios

```bash
# Terminal 1: Bot de Telegram
python3 bot_completo.py

# Terminal 2: Sistema Experto
python3 expert_service.py

# Terminal 3: Dashboard (servidor web simple)
python3 -m http.server 8000
# Luego abre: http://localhost:8000/dashboard_pro.html
```

### Comandos del Bot de Telegram

#### Por Voz o Texto:
```
"temperatura"                    # Ver temperatura actual
"enciende ventilador"           # Encender dispositivo
"apaga calefactor"              # Apagar dispositivo
"temperatura mínima 18"         # Configurar límite mínimo
"temperatura máxima 30"         # Configurar límite máximo
"cambia setpoint a 25"          # Cambiar temperatura objetivo
"estado"                        # Ver estado completo
"modo ventilador automático"   # Cambiar modo de dispositivo
```

#### Comandos de Slash:
```
/start      # Menú principal
/temp       # Ver temperatura
/status     # Estado del sistema
/devices    # Estado de dispositivos
/config     # Ver configuración
/help       # Ayuda completa
```

## 🧠 Sistema Experto

### Reglas Implementadas

#### 🌡️ Temperatura (7 reglas)
- **R001**: Temperatura crítica alta (> tempMax)
- **R002**: Temperatura crítica baja (< tempMin)
- **R003**: Temperatura alta advertencia
- **R004**: Temperatura baja advertencia
- **R005**: Muy por encima del setpoint
- **R006**: Muy por debajo del setpoint
- **R007**: Temperatura en rango óptimo

#### 💧 Humedad (5 reglas)
- **R101**: Humedad crítica alta (> 85%)
- **R102**: Humedad crítica baja (< 20%)
- **R103**: Humedad alta (70-85%)
- **R104**: Humedad baja (20-30%)
- **R105**: Humedad óptima (40-60%)

#### 🔌 Dispositivos (5 reglas)
- **R201**: Ventilador y calefactor simultáneos (conflicto)
- **R202**: Todos apagados con temperatura fuera de rango
- **R203**: Ventilador sin efecto
- **R204**: Calefactor sin efecto
- **R205**: Modo manual con condiciones críticas

#### ⚡ Eficiencia (3 reglas)
- **R301**: Operación eficiente
- **R302**: Histéresis muy pequeña
- **R303**: Histéresis muy grande

#### 🚨 Alertas (2+ reglas)
- **R401**: Múltiples alertas activas
- **R402**: Rango de alertas muy estrecho

### Estados del Sistema

| Estado | Descripción | Color |
|--------|-------------|-------|
| **Óptimo** | Todo funcionando perfectamente | 🟢 Verde |
| **Aceptable** | Advertencias menores | 🟡 Amarillo |
| **Problemático** | Problemas que requieren atención | 🟠 Naranja |
| **Crítico** | Situación urgente | 🔴 Rojo |

### Severidades

| Severidad | Acción Requerida | Ejemplos |
|-----------|------------------|----------|
| **Baja** | Informativa | Temp en rango óptimo |
| **Media** | Monitorear | Humedad elevada |
| **Alta** | Atención pronta | Temp cerca de límites |
| **Crítica** | Acción inmediata | Temp > límite máximo |

### Cómo funciona

1. **Recopilación**: El servicio recibe datos de MQTT cada 5-30 segundos
2. **Evaluación**: Se evalúan todas las 30+ reglas contra los datos actuales
3. **Diagnóstico**: Se genera un diagnóstico completo con:
   - Estado general del sistema
   - Severidad máxima detectada
   - Lista de problemas
   - Recomendaciones específicas
4. **Almacenamiento**: Se guarda en Supabase para histórico
5. **Alertas**: Si es crítico, se publica alerta por MQTT

## 📊 Dashboard

### Secciones

#### 1. 🧠 Análisis IA
- Tendencia de temperatura
- Predicción a 30 minutos
- Diagnóstico inteligente
- Recomendaciones personalizadas

#### 2. ⚙️ Sistema Experto
- Estado general
- Severidad máxima
- Reglas activadas por categoría
- Problemas y recomendaciones

#### 3. 🌡️ Clima Actual
- Temperatura y humedad en tiempo real
- Última actualización
- Setpoint objetivo

#### 4. 📈 Historial
- Gráfico de temperatura
- Gráfico de humedad
- Últimos 20 registros

#### 5. 🔌 Dispositivos
- Estado ON/OFF
- Modo (Automático/Manual/Forzado)
- Nombres personalizados

#### 6. ⚙️ Configuración
- Temperatura objetivo
- Histéresis
- Límites de alerta (máx/mín)

### Actualización automática

- Datos actuales: **cada 5 segundos**
- Gráficos: **cada 5 segundos**
- Dispositivos: **cada 10 segundos**
- Config: **cada 15 segundos**
- Sistema Experto: **cada 30 segundos**
- Análisis IA: **cada 60 segundos**

## 🔧 Solución de Problemas

### El Sistema Experto no se actualiza

1. Verificar que `expert_service.py` esté corriendo
2. Revisar que los datos lleguen por MQTT:
   ```bash
   # Ver logs del servicio
   python3 expert_service.py
   ```
3. Verificar la tabla en Supabase:
   ```sql
   SELECT * FROM expert_analysis ORDER BY created_at DESC LIMIT 5;
   ```

### Dashboard muestra "No hay análisis"

1. Esperar al menos 30 segundos después de iniciar servicios
2. Verificar credenciales de Supabase en el HTML
3. Abrir consola del navegador (F12) para ver errores

### Reglas no se activan correctamente

1. Revisar los valores actuales:
   ```python
   # En expert_service.py, agregar después de system_state:
   print(f"DEBUG: {json.dumps(system_state, indent=2)}")
   ```
2. Verificar umbrales en las reglas en `expert_system.py`
3. Probar el motor directamente:
   ```bash
   python3 expert_system.py
   ```

### Bot no responde

1. Verificar token de Telegram
2. Ver logs:
   ```bash
   python3 bot_completo.py
   ```
3. Verificar conexión MQTT

## 📝 Personalización

### Agregar nuevas reglas

Edita `expert_system.py` en el método `_cargar_reglas()`:

```python
{
    'id': 'R999',
    'nombre': 'Mi nueva regla',
    'severidad': 'media',  # critica, alta, media, baja
    'condicion': lambda d: d['temp'] > 35,  # Tu condición
    'accion': 'Descripción del problema',
    'recomendacion': 'Qué hacer al respecto',
    'tipo': 'temperatura'  # temperatura, humedad, dispositivos, etc.
}
```

### Cambiar intervalos de análisis

En `expert_service.py`:

```python
ANALYSIS_INTERVAL = 30  # Cambiar a los segundos que desees
```

### Personalizar dashboard

Edita `dashboard_pro.html`:
- Colores en `:root { ... }`
- Intervalos de actualización al final del script
- Agregar nuevas secciones en `.dashboard`

## 📈 Estadísticas del Sistema

- **30+ reglas** de evaluación
- **5 categorías** de diagnóstico
- **4 niveles** de severidad
- **Análisis cada 30 segundos**
- **Histórico completo** en Supabase
- **Dashboard en tiempo real**

## 🎯 Roadmap

- [ ] App móvil nativa
- [ ] Notificaciones push
- [ ] Integración con más sensores
- [ ] Machine Learning para predicciones
- [ ] API REST para integraciones
- [ ] Modo offline

## 📄 Licencia

MIT License - Libre de usar y modificar

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor:
1. Fork el proyecto
2. Crea tu feature branch
3. Commit tus cambios
4. Push al branch
5. Abre un Pull Request

## 📧 Soporte

Si tienes problemas:
1. Revisa la sección de [Solución de Problemas](#-solución-de-problemas)
2. Verifica los logs de cada servicio
3. Abre un issue con los detalles del error

---

**Desarrollado con ❤️ usando Python, Claude AI, y mucho café ☕**