#!/usr/bin/env python3
"""
🔧 SERVICIO DE SISTEMA EXPERTO
Integra el motor de reglas con MQTT y Supabase
"""

import os
import json
import time
from datetime import datetime
from expert_system import ExpertSystem
import paho.mqtt.client as mqtt
from supabase import create_client, Client

# ========================================
# CONFIGURACIÓN
# ========================================

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ========================================
# INICIALIZACIÓN
# ========================================

print("🚀 Iniciando Servicio de Sistema Experto...")

# Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# MQTT
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.tls_set()

# Sistema Experto
experto = ExpertSystem()

# Estado actual del sistema
system_state = {
    'temp': 0,
    'hum': 0,
    'config': {
        'setpoint': 24,
        'hysteresis': 2,
        'tempMax': 30,
        'tempMin': 18
    },
    'relays': {}
}

last_analysis_time = 0
ANALYSIS_INTERVAL = 30  # Analizar cada 30 segundos

# ========================================
# FUNCIONES MQTT
# ========================================

def on_mqtt_connect(client, userdata, flags, rc):
    print(f"✅ MQTT conectado (rc={rc})")
    client.subscribe("esp32/sensores")
    client.subscribe("esp32/relay/status")
    client.subscribe("esp32/config")

def on_mqtt_message(client, userdata, msg):
    global system_state, last_analysis_time
    
    try:
        data = json.loads(msg.payload.decode())
        
        if msg.topic == "esp32/sensores":
            system_state['temp'] = data.get('temp', 0)
            system_state['hum'] = data.get('hum', 0)
            print(f"📊 Sensores actualizados: {system_state['temp']:.1f}°C, {system_state['hum']:.0f}%")
            
        elif msg.topic == "esp32/relay/status":
            system_state['relays'] = data
            
        elif msg.topic == "esp32/config":
            system_state['config'].update(data)
            print(f"⚙️ Config actualizada: {data}")
        
        # Ejecutar análisis si ha pasado el intervalo
        current_time = time.time()
        if current_time - last_analysis_time >= ANALYSIS_INTERVAL:
            ejecutar_analisis()
            last_analysis_time = current_time
            
    except Exception as e:
        print(f"❌ Error procesando MQTT: {e}")

mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message

# ========================================
# FUNCIONES DE ANÁLISIS
# ========================================

def ejecutar_analisis():
    """Ejecuta análisis del sistema experto y guarda en Supabase"""
    try:
        print("\n" + "="*70)
        print("⚙️ EJECUTANDO ANÁLISIS DEL SISTEMA EXPERTO")
        print("="*70)
        
        # Ejecutar evaluación
        diagnostico = experto.evaluar(system_state)
        
        # Mostrar resumen en consola
        print(f"\n📊 Estado: {diagnostico['estado_general'].upper()}")
        print(f"🔴 Severidad: {diagnostico['severidad_maxima'].upper()}")
        print(f"📋 Reglas activadas: {diagnostico['total_reglas_activadas']}")
        
        if diagnostico['problemas']:
            print(f"\n⚠️ Problemas ({len(diagnostico['problemas'])}):")
            for problema in diagnostico['problemas'][:3]:
                print(f"  • {problema}")
        
        if diagnostico['recomendaciones']:
            print(f"\n💡 Recomendaciones ({len(diagnostico['recomendaciones'])}):")
            for rec in diagnostico['recomendaciones'][:3]:
                print(f"  • {rec}")
        
        # Guardar en Supabase
        guardar_en_supabase(diagnostico)
        
        # Publicar alertas urgentes por MQTT si es necesario
        if diagnostico['severidad_maxima'] == 'critica':
            publicar_alerta_critica(diagnostico)
        
        print("\n✅ Análisis completado y guardado")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error en análisis: {e}")

def guardar_en_supabase(diagnostico: dict):
    """Guarda el diagnóstico en Supabase"""
    try:
        # Preparar datos para insertar
        data_to_insert = {
            'estado_general': diagnostico['estado_general'],
            'severidad_maxima': diagnostico['severidad_maxima'],
            'total_reglas': diagnostico['total_reglas_activadas'],
            'diagnostico_completo': json.dumps(diagnostico, ensure_ascii=False),
            'temperatura_actual': system_state['temp'],
            'humedad_actual': system_state['hum'],
            'problemas': json.dumps(diagnostico['problemas'], ensure_ascii=False),
            'recomendaciones': json.dumps(diagnostico['recomendaciones'], ensure_ascii=False)
        }
        
        # Insertar en tabla expert_analysis
        result = supabase.table('expert_analysis').insert(data_to_insert).execute()
        print(f"💾 Diagnóstico guardado en Supabase (ID: {result.data[0]['id'] if result.data else 'N/A'})")
        
    except Exception as e:
        print(f"❌ Error guardando en Supabase: {e}")

def publicar_alerta_critica(diagnostico: dict):
    """Publica alerta crítica por MQTT para que el bot de Telegram la procese"""
    try:
        alerta = {
            'tipo': 'ALERTA_CRITICA',
            'estado': diagnostico['estado_general'],
            'severidad': diagnostico['severidad_maxima'],
            'problemas': diagnostico['problemas'][:3],
            'recomendaciones': diagnostico['recomendaciones'][:3],
            'timestamp': datetime.now().isoformat()
        }
        
        mqtt_client.publish("esp32/alert/critical", json.dumps(alerta))
        print("📢 Alerta crítica publicada por MQTT")
        
    except Exception as e:
        print(f"❌ Error publicando alerta: {e}")

# ========================================
# FUNCIONES DE UTILIDAD
# ========================================

def crear_tabla_supabase():
    """
    Crea la tabla en Supabase si no existe.
    Ejecutar esto manualmente en el SQL Editor de Supabase:
    
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
    
    CREATE INDEX idx_expert_created_at ON expert_analysis(created_at DESC);
    CREATE INDEX idx_expert_severidad ON expert_analysis(severidad_maxima);
    """
    print("""
📝 INSTRUCCIONES PARA CREAR TABLA EN SUPABASE:

1. Ve a tu proyecto en Supabase
2. Abre el SQL Editor
3. Ejecuta este SQL:

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

CREATE INDEX idx_expert_created_at ON expert_analysis(created_at DESC);
CREATE INDEX idx_expert_severidad ON expert_analysis(severidad_maxima);

4. ¡Listo! La tabla está creada
    """)

# ========================================
# MAIN
# ========================================

def main():
    print("\n" + "="*70)
    print("⚙️ SERVICIO DE SISTEMA EXPERTO")
    print("="*70)
    print("✅ Motor de reglas cargado")
    print(f"✅ {len(experto.reglas)} reglas disponibles")
    print(f"⏱️ Análisis cada {ANALYSIS_INTERVAL} segundos")
    print("="*70 + "\n")
    
    # Mostrar instrucciones para crear tabla
    crear_tabla_supabase()
    
    # Conectar MQTT
    try:
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print("✅ MQTT conectado\n")
    except Exception as e:
        print(f"⚠️ Error MQTT: {e}\n")
    
    # Ejecutar análisis inicial después de 10 segundos
    time.sleep(10)
    ejecutar_analisis()
    
    # Mantener el servicio corriendo
    print("🤖 Servicio corriendo (Ctrl+C para detener)\n")
    print("📊 Esperando datos de sensores...\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo servicio...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("✅ Servicio detenido\n")

if __name__ == '__main__':
    main()