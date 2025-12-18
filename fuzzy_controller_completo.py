#!/usr/bin/env python3
"""
🧠 CONTROLADOR DE LÓGICA DIFUSA INTEGRADO
Sistema completo: Python (servidor) + Documentación para ESP32
Incluye cálculos matemáticos detallados
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import paho.mqtt.client as mqtt
import json
import time
import os
from datetime import datetime
from supabase import create_client, Client

# ========================================
# CONFIGURACIÓN
# ========================================

MQTT_HOST = os.getenv("MQTT_HOST", "broker.hivemq.cloud")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USER = os.getenv("MQTT_USER", "esp32user")
MQTT_PASS = os.getenv("MQTT_PASS", "password")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Inicializar Supabase
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================================
# CLASE: SISTEMA DE LÓGICA DIFUSA
# ========================================

class FuzzyControlSystem:
    """
    Sistema de Control por Lógica Difusa
    
    VARIABLES DE ENTRADA:
    - temperatura: 15-35°C (sensor DHT)
    - humedad: 0-100% (sensor DHT)
    - diff_temp: diferencia con setpoint (-10 a +10°C)
    
    VARIABLES DE SALIDA:
    - ventilador: 0-100% (relay 1)
    - calefactor: 0-100% (relay 2)
    - humidificador: 0-100% (relay 3)
    """
    
    def __init__(self):
        print("🧠 Inicializando Sistema de Lógica Difusa...")
        self._crear_variables_difusas()
        self._crear_reglas()
        self._crear_sistema_control()
        print(f"✅ Sistema difuso creado con {len(self.reglas)} reglas")
    
    def _crear_variables_difusas(self):
        """
        Crea las variables lingüísticas con funciones de pertenencia.
        
        FUNCIONES DE PERTENENCIA TRIANGULARES:
        μ(x) = max(0, min((x-a)/(b-a), (c-x)/(c-b)))
        donde [a, b, c] son los puntos del triángulo
        """
        
        # ENTRADA 1: Temperatura (15-35°C)
        self.temperatura = ctrl.Antecedent(np.arange(15, 36, 0.1), 'temperatura')
        self.temperatura['muy_fria'] = fuzz.trimf(self.temperatura.universe, [15, 15, 20])
        self.temperatura['fria'] = fuzz.trimf(self.temperatura.universe, [18, 21, 24])
        self.temperatura['confortable'] = fuzz.trimf(self.temperatura.universe, [22, 24, 26])
        self.temperatura['caliente'] = fuzz.trimf(self.temperatura.universe, [24, 27, 30])
        self.temperatura['muy_caliente'] = fuzz.trimf(self.temperatura.universe, [28, 35, 35])
        
        # ENTRADA 2: Humedad (0-100%)
        self.humedad = ctrl.Antecedent(np.arange(0, 101, 1), 'humedad')
        self.humedad['muy_baja'] = fuzz.trimf(self.humedad.universe, [0, 0, 30])
        self.humedad['baja'] = fuzz.trimf(self.humedad.universe, [20, 35, 50])
        self.humedad['normal'] = fuzz.trimf(self.humedad.universe, [40, 50, 60])
        self.humedad['alta'] = fuzz.trimf(self.humedad.universe, [50, 65, 80])
        self.humedad['muy_alta'] = fuzz.trimf(self.humedad.universe, [70, 100, 100])
        
        # ENTRADA 3: Diferencia con setpoint (-10 a +10°C)
        self.diff_temp = ctrl.Antecedent(np.arange(-10, 11, 0.1), 'diff_temp')
        self.diff_temp['muy_baja'] = fuzz.trimf(self.diff_temp.universe, [-10, -10, -3])
        self.diff_temp['baja'] = fuzz.trimf(self.diff_temp.universe, [-5, -2, 0])
        self.diff_temp['ok'] = fuzz.trimf(self.diff_temp.universe, [-1, 0, 1])
        self.diff_temp['alta'] = fuzz.trimf(self.diff_temp.universe, [0, 2, 5])
        self.diff_temp['muy_alta'] = fuzz.trimf(self.diff_temp.universe, [3, 10, 10])
        
        # SALIDA 1: Potencia Ventilador (0-100%)
        self.ventilador = ctrl.Consequent(np.arange(0, 101, 1), 'ventilador')
        self.ventilador['apagado'] = fuzz.trimf(self.ventilador.universe, [0, 0, 10])
        self.ventilador['bajo'] = fuzz.trimf(self.ventilador.universe, [5, 25, 45])
        self.ventilador['medio'] = fuzz.trimf(self.ventilador.universe, [35, 50, 65])
        self.ventilador['alto'] = fuzz.trimf(self.ventilador.universe, [55, 75, 95])
        self.ventilador['maximo'] = fuzz.trimf(self.ventilador.universe, [85, 100, 100])
        
        # SALIDA 2: Potencia Calefactor (0-100%)
        self.calefactor = ctrl.Consequent(np.arange(0, 101, 1), 'calefactor')
        self.calefactor['apagado'] = fuzz.trimf(self.calefactor.universe, [0, 0, 10])
        self.calefactor['bajo'] = fuzz.trimf(self.calefactor.universe, [5, 25, 45])
        self.calefactor['medio'] = fuzz.trimf(self.calefactor.universe, [35, 50, 65])
        self.calefactor['alto'] = fuzz.trimf(self.calefactor.universe, [55, 75, 95])
        self.calefactor['maximo'] = fuzz.trimf(self.calefactor.universe, [85, 100, 100])
        
        # SALIDA 3: Potencia Humidificador (0-100%)
        self.humidificador = ctrl.Consequent(np.arange(0, 101, 1), 'humidificador')
        self.humidificador['apagado'] = fuzz.trimf(self.humidificador.universe, [0, 0, 10])
        self.humidificador['bajo'] = fuzz.trimf(self.humidificador.universe, [5, 30, 55])
        self.humidificador['medio'] = fuzz.trimf(self.humidificador.universe, [45, 60, 75])
        self.humidificador['alto'] = fuzz.trimf(self.humidificador.universe, [65, 85, 100])
    
    def _crear_reglas(self):
        """
        Define las reglas difusas IF-THEN.
        
        ESTRUCTURA DE REGLAS:
        IF (antecedente) THEN (consecuente)
        
        OPERADORES LÓGICOS:
        - AND (&): min(μA(x), μB(x))
        - OR (|): max(μA(x), μB(x))
        - NOT (~): 1 - μA(x)
        """
        
        self.reglas = [
            # ===== CONTROL DE VENTILADOR (ENFRIAMIENTO) =====
            # R1: Si temp muy alta → ventilador al máximo
            ctrl.Rule(self.diff_temp['muy_alta'], self.ventilador['maximo']),
            
            # R2: Si temp alta → ventilador alto
            ctrl.Rule(self.diff_temp['alta'], self.ventilador['alto']),
            
            # R3: Si temp OK → ventilador bajo (mínimo)
            ctrl.Rule(self.diff_temp['ok'], self.ventilador['bajo']),
            
            # R4: Si temp baja o muy baja → ventilador apagado
            ctrl.Rule(self.diff_temp['baja'] | self.diff_temp['muy_baja'], 
                     self.ventilador['apagado']),
            
            # ===== CONTROL DE CALEFACTOR (CALENTAMIENTO) =====
            # R5: Si temp muy baja → calefactor al máximo
            ctrl.Rule(self.diff_temp['muy_baja'], self.calefactor['maximo']),
            
            # R6: Si temp baja → calefactor alto
            ctrl.Rule(self.diff_temp['baja'], self.calefactor['alto']),
            
            # R7: Si temp OK → calefactor bajo
            ctrl.Rule(self.diff_temp['ok'], self.calefactor['bajo']),
            
            # R8: Si temp alta o muy alta → calefactor apagado
            ctrl.Rule(self.diff_temp['alta'] | self.diff_temp['muy_alta'], 
                     self.calefactor['apagado']),
            
            # ===== CONTROL DE HUMIDIFICADOR =====
            # R9: Si humedad muy baja → humidificador alto
            ctrl.Rule(self.humedad['muy_baja'], self.humidificador['alto']),
            
            # R10: Si humedad baja → humidificador medio
            ctrl.Rule(self.humedad['baja'], self.humidificador['medio']),
            
            # R11: Si humedad normal → humidificador bajo
            ctrl.Rule(self.humedad['normal'], self.humidificador['bajo']),
            
            # R12: Si humedad alta o muy alta → humidificador apagado
            ctrl.Rule(self.humedad['alta'] | self.humedad['muy_alta'], 
                     self.humidificador['apagado']),
            
            # ===== REGLAS COMBINADAS =====
            # R13: Mucho calor + humedad alta → máximo enfriamiento
            ctrl.Rule(self.temperatura['muy_caliente'] & self.humedad['muy_alta'],
                     [self.ventilador['maximo'], self.calefactor['apagado']]),
            
            # R14: Mucho frío + humedad baja → máximo calentamiento + humidificación
            ctrl.Rule(self.temperatura['muy_fria'] & self.humedad['muy_baja'],
                     [self.calefactor['maximo'], self.humidificador['alto']]),
            
            # R15: Condiciones confortables → modo económico
            ctrl.Rule(self.temperatura['confortable'] & self.humedad['normal'],
                     [self.ventilador['bajo'], self.calefactor['bajo'], 
                      self.humidificador['apagado']]),
        ]
    
    def _crear_sistema_control(self):
        """Crea el sistema de control y su simulación"""
        self.sistema_ctrl = ctrl.ControlSystem(self.reglas)
        self.sistema = ctrl.ControlSystemSimulation(self.sistema_ctrl)
    
    def calcular(self, temp_actual, hum_actual, setpoint):
        """
        Ejecuta el proceso de inferencia difusa.
        
        PROCESO DE INFERENCIA:
        1. FUZZIFICACIÓN: Convertir valores crisp a difusos
        2. EVALUACIÓN DE REGLAS: Aplicar operadores lógicos
        3. AGREGACIÓN: Combinar salidas de todas las reglas
        4. DEFUZZIFICACIÓN: Convertir salida difusa a crisp
        
        MÉTODO DE DEFUZZIFICACIÓN: Centroide
        y* = ∫ μ(y) · y dy / ∫ μ(y) dy
        
        Args:
            temp_actual (float): Temperatura medida en °C
            hum_actual (float): Humedad medida en %
            setpoint (float): Temperatura objetivo en °C
        
        Returns:
            dict: Salidas del controlador + metadatos
        """
        try:
            # 1. CALCULAR DIFERENCIA (CÁLCULO MATEMÁTICO)
            diff = temp_actual - setpoint
            
            # 2. FUZZIFICACIÓN - Asignar entradas
            self.sistema.input['temperatura'] = temp_actual
            self.sistema.input['humedad'] = hum_actual
            self.sistema.input['diff_temp'] = diff
            
            # 3. INFERENCIA Y DEFUZZIFICACIÓN
            self.sistema.compute()
            
            # 4. OBTENER SALIDAS CRISP
            ventilador_out = round(self.sistema.output['ventilador'], 1)
            calefactor_out = round(self.sistema.output['calefactor'], 1)
            humidificador_out = round(self.sistema.output['humidificador'], 1)
            
            # 5. CALCULAR ERROR ABSOLUTO (CÁLCULO MATEMÁTICO)
            # |e(t)| = |Tsetpoint - Tactual|
            error_absoluto = abs(diff)
            
            # 6. CALCULAR ÍNDICE DE DESEMPEÑO (CÁLCULO MATEMÁTICO)
            # ISE = ∫ e²(t) dt (simplificado para una muestra)
            ise = diff ** 2
            
            # 7. DETERMINAR ESTADO DEL SISTEMA
            if error_absoluto <= 1:
                estado_control = "OPTIMO"
            elif error_absoluto <= 2:
                estado_control = "BUENO"
            elif error_absoluto <= 3:
                estado_control = "ACEPTABLE"
            else:
                estado_control = "CRITICO"
            
            resultado = {
                # Entradas
                'temperatura': temp_actual,
                'humedad': hum_actual,
                'setpoint': setpoint,
                'diferencia': round(diff, 2),
                
                # Salidas difusas
                'ventilador': ventilador_out,
                'calefactor': calefactor_out,
                'humidificador': humidificador_out,
                
                # Métricas matemáticas
                'error_absoluto': round(error_absoluto, 2),
                'ise': round(ise, 4),
                'estado_control': estado_control,
                
                # Comandos binarios (ON/OFF)
                'cmd_ventilador': 'ON' if ventilador_out > 30 else 'OFF',
                'cmd_calefactor': 'ON' if calefactor_out > 30 else 'OFF',
                'cmd_humidificador': 'ON' if humidificador_out > 30 else 'OFF',
                
                # Metadatos
                'timestamp': datetime.now().isoformat(),
                'estado': 'OK'
            }
            
            self._imprimir_resultado(resultado)
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error en lógica difusa: {e}")
            return {
                'ventilador': 0,
                'calefactor': 0,
                'humidificador': 0,
                'estado': 'ERROR',
                'error': str(e)
            }
    
    def _imprimir_resultado(self, resultado):
        """Muestra el resultado del cálculo difuso"""
        print(f"\n🧠 LÓGICA DIFUSA [{datetime.now().strftime('%H:%M:%S')}]")
        print(f"   📊 Entradas:")
        print(f"      Temp={resultado['temperatura']:.1f}°C, Setpoint={resultado['setpoint']:.1f}°C")
        print(f"      Humedad={resultado['humedad']:.0f}%")
        print(f"      Diferencia={resultado['diferencia']:+.2f}°C")
        print(f"   📐 Cálculos:")
        print(f"      Error Absoluto: |e| = {resultado['error_absoluto']:.2f}°C")
        print(f"      ISE: e² = {resultado['ise']:.4f}")
        print(f"      Estado: {resultado['estado_control']}")
        print(f"   ➜ Salidas Difusas:")
        print(f"      Ventilador: {resultado['ventilador']:.0f}%")
        print(f"      Calefactor: {resultado['calefactor']:.0f}%")
        print(f"      Humidificador: {resultado['humidificador']:.0f}%")
        print(f"   🔌 Comandos:")
        print(f"      Relay 1 (Ventilador): {resultado['cmd_ventilador']}")
        print(f"      Relay 2 (Calefactor): {resultado['cmd_calefactor']}")
        print(f"      Relay 3 (Humidificador): {resultado['cmd_humidificador']}")

# ========================================
# CONTROLADOR MQTT
# ========================================

class ControladorFuzzyMQTT:
    """Integración del sistema difuso con MQTT"""
    
    def __init__(self):
        self.fuzzy_system = FuzzyControlSystem()
        
        # Cliente MQTT
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.mqtt_client.tls_set()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        # Estado actual
        self.temp_actual = 24.0
        self.hum_actual = 50.0
        self.setpoint = 24.0
        self.modo_activo = True
        
        # Estadísticas
        self.total_calculos = 0
        self.decisiones_enviadas = 0
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ MQTT conectado exitosamente")
            client.subscribe("esp32/sensores")
            client.subscribe("esp32/config")
            client.subscribe("esp32/fuzzy/control")
            print("📡 Suscrito a topics MQTT")
        else:
            print(f"❌ Error de conexión MQTT (rc={rc})")
    
    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            
            if topic == "esp32/sensores":
                data = json.loads(msg.payload.decode())
                self.temp_actual = data.get('temp', self.temp_actual)
                self.hum_actual = data.get('hum', self.hum_actual)
                
                if self.modo_activo:
                    control = self.fuzzy_system.calcular(
                        self.temp_actual,
                        self.hum_actual,
                        self.setpoint
                    )
                    self.total_calculos += 1
                    self.publicar_decisiones(control)
                    self.guardar_en_supabase(control)
                
            elif topic == "esp32/config":
                data = json.loads(msg.payload.decode())
                if 'setpoint' in data:
                    self.setpoint = data['setpoint']
                    print(f"⚙️ Setpoint actualizado: {self.setpoint}°C")
                    
            elif topic == "esp32/fuzzy/control":
                data = json.loads(msg.payload.decode())
                if 'activo' in data:
                    self.modo_activo = data['activo']
                    print(f"🔄 Sistema difuso {'ACTIVADO' if self.modo_activo else 'DESACTIVADO'}")
                
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
    
    def publicar_decisiones(self, control):
        """Publica comandos a los relays"""
        try:
            # Publicar comandos individuales
            for i, cmd in enumerate([control['cmd_ventilador'], 
                                     control['cmd_calefactor'], 
                                     control['cmd_humidificador']], start=1):
                topic = f"esp32/relay/{i}/cmd"
                self.mqtt_client.publish(topic, cmd, qos=1)
            
            # Publicar estado completo
            estado_fuzzy = {
                'timestamp': control['timestamp'],
                'entradas': {
                    'temperatura': control['temperatura'],
                    'humedad': control['humedad'],
                    'setpoint': control['setpoint'],
                    'diferencia': control['diferencia']
                },
                'salidas': {
                    'ventilador': control['ventilador'],
                    'calefactor': control['calefactor'],
                    'humidificador': control['humidificador']
                },
                'metricas': {
                    'error_absoluto': control['error_absoluto'],
                    'ise': control['ise'],
                    'estado_control': control['estado_control']
                },
                'comandos': {
                    'ventilador': control['cmd_ventilador'],
                    'calefactor': control['cmd_calefactor'],
                    'humidificador': control['cmd_humidificador']
                }
            }
            
            self.mqtt_client.publish("esp32/fuzzy/estado", json.dumps(estado_fuzzy), qos=1)
            self.decisiones_enviadas += 1
            
            activos = [k for k, v in estado_fuzzy['comandos'].items() if v == 'ON']
            if activos:
                print(f"   🔌 Dispositivos ON: {', '.join(activos)}")
            else:
                print(f"   🔌 Todos los dispositivos OFF")
                
        except Exception as e:
            print(f"❌ Error publicando decisiones: {e}")
    
    def guardar_en_supabase(self, control):
        """Guarda decisión en Supabase"""
        if not supabase:
            return
        
        try:
            data = {
                "temperatura_actual": control['temperatura'],
                "humedad_actual": control['humedad'],
                "setpoint": control['setpoint'],
                "diferencia_temp": control['diferencia'],
                "error_absoluto": control['error_absoluto'],
                "ise": control['ise'],
                "estado_control": control['estado_control'],
                "potencia_ventilador": control['ventilador'],
                "potencia_calefactor": control['calefactor'],
                "potencia_humidificador": control['humidificador'],
                "comando_ventilador": control['cmd_ventilador'],
                "comando_calefactor": control['cmd_calefactor'],
                "comando_humidificador": control['cmd_humidificador']
            }
            
            supabase.table('fuzzy_decisions').insert(data).execute()
            print("💾 Decisión guardada en Supabase")
            
        except Exception as e:
            print(f"⚠️ No se pudo guardar en Supabase: {e}")
    
    def iniciar(self):
        """Inicia el controlador"""
        try:
            print(f"\n🔌 Conectando a MQTT: {MQTT_HOST}:{MQTT_PORT}")
            self.mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
            
            print("\n" + "="*70)
            print("🧠 CONTROLADOR DE LÓGICA DIFUSA")
            print("="*70)
            print(f"📊 Variables de entrada: 3 (temperatura, humedad, diff_temp)")
            print(f"📊 Variables de salida: 3 (ventilador, calefactor, humidificador)")
            print(f"📋 Reglas difusas: {len(self.fuzzy_system.reglas)}")
            print(f"🎯 Setpoint inicial: {self.setpoint}°C")
            print(f"🔄 Modo: {'AUTOMÁTICO' if self.modo_activo else 'MANUAL'}")
            print("="*70 + "\n")
            
            self.mqtt_client.loop_forever()
            
        except KeyboardInterrupt:
            print(f"\n\n⏹️ Deteniendo controlador...")
            print(f"📊 Estadísticas:")
            print(f"   • Cálculos realizados: {self.total_calculos}")
            print(f"   • Decisiones enviadas: {self.decisiones_enviadas}")
            self.mqtt_client.disconnect()
            print("✅ Desconectado")
            
        except Exception as e:
            print(f"❌ Error: {e}")

# ========================================
# FUNCIÓN DE PRUEBA
# ========================================

def ejecutar_pruebas():
    """Ejecuta pruebas del sistema difuso"""
    print("\n🧪 MODO PRUEBA - LÓGICA DIFUSA")
    print("="*70)
    
    fuzzy = FuzzyControlSystem()
    
    escenarios = [
        {"nombre": "1. Temperatura muy alta", "temp": 32, "hum": 60, "setpoint": 24},
        {"nombre": "2. Temperatura muy baja", "temp": 16, "hum": 40, "setpoint": 24},
        {"nombre": "3. Condiciones confortables", "temp": 24, "hum": 50, "setpoint": 24},
        {"nombre": "4. Calor + humedad alta", "temp": 30, "hum": 80, "setpoint": 24},
        {"nombre": "5. Frío + humedad baja", "temp": 18, "hum": 25, "setpoint": 24},
        {"nombre": "6. Temperatura ligeramente alta", "temp": 26, "hum": 55, "setpoint": 24},
        {"nombre": "7. Temperatura ligeramente baja", "temp": 22, "hum": 45, "setpoint": 24},
    ]
    
    for escenario in escenarios:
        print(f"\n{'='*70}")
        print(f"📍 Escenario: {escenario['nombre']}")
        print(f"{'='*70}")
        control = fuzzy.calcular(escenario['temp'], escenario['hum'], escenario['setpoint'])
        time.sleep(0.5)
    
    print("\n" + "="*70)
    print("✅ Pruebas completadas")
    print("="*70)

# ========================================
# PUNTO DE ENTRADA
# ========================================

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("🧠 SISTEMA DE CONTROL POR LÓGICA DIFUSA")
    print("="*70)
    print("Algoritmo: Lógica Difusa (Fuzzy Logic)")
    print("Método de Defuzzificación: Centroide")
    print("Operadores: AND (min), OR (max)")
    print("="*70 + "\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--prueba":
        ejecutar_pruebas()
    else:
        controlador = ControladorFuzzyMQTT()
        controlador.iniciar()