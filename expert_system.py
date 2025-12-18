#!/usr/bin/env python3
"""
⚙️ SISTEMA EXPERTO - Motor de Reglas
Evalúa condiciones y genera diagnósticos automáticos
"""

import json
from datetime import datetime
from typing import Dict, List, Any

class ExpertSystem:
    """Motor del Sistema Experto basado en reglas"""
    
    def __init__(self):
        self.reglas = self._cargar_reglas()
        self.reglas_activadas = []
        self.diagnostico = {
            'estado_general': 'desconocido',
            'severidad_maxima': 'baja',
            'reglas_activadas': [],
            'recomendaciones': [],
            'problemas': [],
            'timestamp': None
        }
    
    def _cargar_reglas(self) -> List[Dict]:
        """Define todas las reglas del sistema experto"""
        return [
            # ============ REGLAS DE TEMPERATURA ============
            {
                'id': 'R001',
                'nombre': 'Temperatura crítica alta',
                'severidad': 'critica',
                'condicion': lambda d: d['temp'] > d['config']['tempMax'],
                'accion': 'Temperatura peligrosamente alta',
                'recomendacion': 'URGENTE: Activar ventilador y revisar sistema de enfriamiento',
                'tipo': 'temperatura'
            },
            {
                'id': 'R002',
                'nombre': 'Temperatura crítica baja',
                'severidad': 'critica',
                'condicion': lambda d: d['temp'] < d['config']['tempMin'],
                'accion': 'Temperatura peligrosamente baja',
                'recomendacion': 'URGENTE: Activar calefactor inmediatamente',
                'tipo': 'temperatura'
            },
            {
                'id': 'R003',
                'nombre': 'Temperatura alta advertencia',
                'severidad': 'alta',
                'condicion': lambda d: d['temp'] > (d['config']['tempMax'] - 2) and d['temp'] <= d['config']['tempMax'],
                'accion': 'Temperatura cerca del límite superior',
                'recomendacion': 'Considerar activar ventilador preventivamente',
                'tipo': 'temperatura'
            },
            {
                'id': 'R004',
                'nombre': 'Temperatura baja advertencia',
                'severidad': 'alta',
                'condicion': lambda d: d['temp'] < (d['config']['tempMin'] + 2) and d['temp'] >= d['config']['tempMin'],
                'accion': 'Temperatura cerca del límite inferior',
                'recomendacion': 'Considerar activar calefactor preventivamente',
                'tipo': 'temperatura'
            },
            {
                'id': 'R005',
                'nombre': 'Temperatura muy por encima del setpoint',
                'severidad': 'media',
                'condicion': lambda d: d['temp'] > (d['config']['setpoint'] + d['config']['hysteresis'] + 3),
                'accion': 'Temperatura significativamente alta respecto al objetivo',
                'recomendacion': 'Verificar eficiencia del sistema de enfriamiento',
                'tipo': 'temperatura'
            },
            {
                'id': 'R006',
                'nombre': 'Temperatura muy por debajo del setpoint',
                'severidad': 'media',
                'condicion': lambda d: d['temp'] < (d['config']['setpoint'] - d['config']['hysteresis'] - 3),
                'accion': 'Temperatura significativamente baja respecto al objetivo',
                'recomendacion': 'Verificar eficiencia del sistema de calefacción',
                'tipo': 'temperatura'
            },
            {
                'id': 'R007',
                'nombre': 'Temperatura en rango óptimo',
                'severidad': 'baja',
                'condicion': lambda d: abs(d['temp'] - d['config']['setpoint']) <= d['config']['hysteresis'],
                'accion': 'Temperatura dentro del rango objetivo',
                'recomendacion': 'Mantener monitoreo regular',
                'tipo': 'temperatura'
            },
            
            # ============ REGLAS DE HUMEDAD ============
            {
                'id': 'R101',
                'nombre': 'Humedad crítica alta',
                'severidad': 'critica',
                'condicion': lambda d: d['hum'] > 85,
                'accion': 'Humedad peligrosamente alta',
                'recomendacion': 'URGENTE: Activar ventilación y deshumidificación',
                'tipo': 'humedad'
            },
            {
                'id': 'R102',
                'nombre': 'Humedad crítica baja',
                'severidad': 'critica',
                'condicion': lambda d: d['hum'] < 20,
                'accion': 'Humedad peligrosamente baja',
                'recomendacion': 'URGENTE: Activar humidificador',
                'tipo': 'humedad'
            },
            {
                'id': 'R103',
                'nombre': 'Humedad alta',
                'severidad': 'media',
                'condicion': lambda d: 70 < d['hum'] <= 85,
                'accion': 'Humedad elevada',
                'recomendacion': 'Considerar activar ventilación',
                'tipo': 'humedad'
            },
            {
                'id': 'R104',
                'nombre': 'Humedad baja',
                'severidad': 'media',
                'condicion': lambda d: 20 <= d['hum'] < 30,
                'accion': 'Humedad baja',
                'recomendacion': 'Considerar activar humidificador',
                'tipo': 'humedad'
            },
            {
                'id': 'R105',
                'nombre': 'Humedad óptima',
                'severidad': 'baja',
                'condicion': lambda d: 40 <= d['hum'] <= 60,
                'accion': 'Humedad en rango óptimo',
                'recomendacion': 'Condiciones ideales de humedad',
                'tipo': 'humedad'
            },
            
            # ============ REGLAS DE DISPOSITIVOS ============
            {
                'id': 'R201',
                'nombre': 'Ventilador y calefactor simultáneos',
                'severidad': 'alta',
                'condicion': lambda d: d['relays'].get('r1', {}).get('state', False) and d['relays'].get('r2', {}).get('state', False),
                'accion': 'Conflicto: ventilador y calefactor encendidos simultáneamente',
                'recomendacion': 'ADVERTENCIA: Operación ineficiente detectada. Apagar uno de los dispositivos',
                'tipo': 'dispositivos'
            },
            {
                'id': 'R202',
                'nombre': 'Todos los dispositivos apagados con temperatura fuera de rango',
                'severidad': 'alta',
                'condicion': lambda d: (
                    not any(d['relays'].get(f'r{i}', {}).get('state', False) for i in range(1, 5)) and
                    (d['temp'] > d['config']['setpoint'] + d['config']['hysteresis'] or 
                     d['temp'] < d['config']['setpoint'] - d['config']['hysteresis'])
                ),
                'accion': 'Ningún dispositivo activo con temperatura fuera de rango',
                'recomendacion': 'Verificar por qué el sistema no está respondiendo automáticamente',
                'tipo': 'dispositivos'
            },
            {
                'id': 'R203',
                'nombre': 'Ventilador prolongado sin cambio de temperatura',
                'severidad': 'media',
                'condicion': lambda d: (
                    d['relays'].get('r1', {}).get('state', False) and 
                    d['temp'] > d['config']['setpoint'] + d['config']['hysteresis']
                ),
                'accion': 'Ventilador activo pero temperatura no disminuye adecuadamente',
                'recomendacion': 'Posible falla en ventilador o necesidad de mantenimiento',
                'tipo': 'dispositivos'
            },
            {
                'id': 'R204',
                'nombre': 'Calefactor prolongado sin cambio de temperatura',
                'severidad': 'media',
                'condicion': lambda d: (
                    d['relays'].get('r2', {}).get('state', False) and 
                    d['temp'] < d['config']['setpoint'] - d['config']['hysteresis']
                ),
                'accion': 'Calefactor activo pero temperatura no aumenta adecuadamente',
                'recomendacion': 'Posible falla en calefactor o necesidad de mantenimiento',
                'tipo': 'dispositivos'
            },
            {
                'id': 'R205',
                'nombre': 'Sistema en modo manual con condiciones críticas',
                'severidad': 'alta',
                'condicion': lambda d: (
                    any(d['relays'].get(f'r{i}', {}).get('mode', 0) == 3 for i in range(1, 5)) and
                    (d['temp'] > d['config']['tempMax'] or d['temp'] < d['config']['tempMin'])
                ),
                'accion': 'Dispositivos en modo manual con temperatura crítica',
                'recomendacion': 'Cambiar a modo automático urgentemente',
                'tipo': 'dispositivos'
            },
            
            # ============ REGLAS DE EFICIENCIA ============
            {
                'id': 'R301',
                'nombre': 'Operación eficiente',
                'severidad': 'baja',
                'condicion': lambda d: (
                    abs(d['temp'] - d['config']['setpoint']) <= d['config']['hysteresis'] and
                    40 <= d['hum'] <= 60
                ),
                'accion': 'Sistema operando eficientemente',
                'recomendacion': 'Mantener configuración actual',
                'tipo': 'eficiencia'
            },
            {
                'id': 'R302',
                'nombre': 'Histéresis muy pequeña',
                'severidad': 'media',
                'condicion': lambda d: d['config']['hysteresis'] < 1,
                'accion': 'Histéresis configurada demasiado pequeña',
                'recomendacion': 'Aumentar histéresis a 1-2°C para reducir ciclos de encendido/apagado',
                'tipo': 'configuracion'
            },
            {
                'id': 'R303',
                'nombre': 'Histéresis muy grande',
                'severidad': 'media',
                'condicion': lambda d: d['config']['hysteresis'] > 4,
                'accion': 'Histéresis configurada demasiado grande',
                'recomendacion': 'Reducir histéresis para mejor control de temperatura',
                'tipo': 'configuracion'
            },
            
            # ============ REGLAS DE ALERTAS ============
            {
                'id': 'R401',
                'nombre': 'Múltiples alertas activas',
                'severidad': 'critica',
                'condicion': lambda d: len([r for r in self.reglas_activadas if r['severidad'] in ['critica', 'alta']]) >= 3,
                'accion': 'Sistema en estado crítico múltiple',
                'recomendacion': 'URGENTE: Revisión inmediata del sistema completo',
                'tipo': 'sistema'
            },
            {
                'id': 'R402',
                'nombre': 'Rango de alertas muy estrecho',
                'severidad': 'baja',
                'condicion': lambda d: (d['config']['tempMax'] - d['config']['tempMin']) < 10,
                'accion': 'Rango de temperatura de alertas muy estrecho',
                'recomendacion': 'Considerar ampliar rango para reducir falsas alarmas',
                'tipo': 'configuracion'
            }
        ]
    
    def evaluar(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa todas las reglas con los datos actuales
        
        Args:
            datos: Diccionario con 'temp', 'hum', 'config', 'relays'
        
        Returns:
            Diagnóstico completo del sistema
        """
        self.reglas_activadas = []
        
        # Evaluar cada regla
        for regla in self.reglas:
            try:
                if regla['condicion'](datos):
                    self.reglas_activadas.append({
                        'id': regla['id'],
                        'nombre': regla['nombre'],
                        'severidad': regla['severidad'],
                        'accion': regla['accion'],
                        'recomendacion': regla['recomendacion'],
                        'tipo': regla['tipo']
                    })
            except Exception as e:
                print(f"⚠️ Error evaluando regla {regla['id']}: {e}")
        
        # Generar diagnóstico
        self.diagnostico = self._generar_diagnostico()
        return self.diagnostico
    
    def _generar_diagnostico(self) -> Dict[str, Any]:
        """Genera diagnóstico completo basado en reglas activadas"""
        
        # Determinar severidad máxima
        severidades = [r['severidad'] for r in self.reglas_activadas]
        if 'critica' in severidades:
            severidad_maxima = 'critica'
            estado_general = 'critico'
        elif 'alta' in severidades:
            severidad_maxima = 'alta'
            estado_general = 'problematico'
        elif 'media' in severidades:
            severidad_maxima = 'media'
            estado_general = 'aceptable'
        else:
            severidad_maxima = 'baja'
            estado_general = 'optimo'
        
        # Extraer problemas y recomendaciones
        problemas = []
        recomendaciones = []
        
        for regla in self.reglas_activadas:
            if regla['severidad'] in ['critica', 'alta']:
                problemas.append(regla['accion'])
            
            if regla['recomendacion'] not in recomendaciones:
                recomendaciones.append(regla['recomendacion'])
        
        # Agrupar reglas por tipo
        reglas_por_tipo = {}
        for regla in self.reglas_activadas:
            tipo = regla['tipo']
            if tipo not in reglas_por_tipo:
                reglas_por_tipo[tipo] = []
            reglas_por_tipo[tipo].append(regla)
        
        return {
            'estado_general': estado_general,
            'severidad_maxima': severidad_maxima,
            'total_reglas_activadas': len(self.reglas_activadas),
            'reglas_activadas': self.reglas_activadas,
            'reglas_por_tipo': reglas_por_tipo,
            'problemas': problemas,
            'recomendaciones': recomendaciones[:5],  # Top 5 recomendaciones
            'timestamp': datetime.now().isoformat(),
            'resumen': self._generar_resumen(estado_general, severidad_maxima)
        }
    
    def _generar_resumen(self, estado: str, severidad: str) -> str:
        """Genera resumen en texto del diagnóstico"""
        if estado == 'critico':
            return "⚠️ SISTEMA EN ESTADO CRÍTICO - Se requiere atención inmediata"
        elif estado == 'problematico':
            return "⚡ Sistema con problemas detectados - Revisar recomendaciones"
        elif estado == 'aceptable':
            return "⚙️ Sistema operando con advertencias menores"
        else:
            return "✅ Sistema operando de manera óptima"
    
    def obtener_reglas_por_severidad(self, severidad: str) -> List[Dict]:
        """Filtra reglas activadas por severidad"""
        return [r for r in self.reglas_activadas if r['severidad'] == severidad]
    
    def obtener_reglas_por_tipo(self, tipo: str) -> List[Dict]:
        """Filtra reglas activadas por tipo"""
        return [r for r in self.reglas_activadas if r['tipo'] == tipo]
    
    def exportar_json(self) -> str:
        """Exporta el diagnóstico completo como JSON"""
        return json.dumps(self.diagnostico, indent=2, ensure_ascii=False)


# ===== FUNCIÓN DE PRUEBA =====
if __name__ == '__main__':
    # Datos de ejemplo
    datos_test = {
        'temp': 32,
        'hum': 65,
        'config': {
            'setpoint': 24,
            'hysteresis': 2,
            'tempMax': 30,
            'tempMin': 18
        },
        'relays': {
            'r1': {'state': True, 'mode': 2, 'name': 'Ventilador'},
            'r2': {'state': False, 'mode': 2, 'name': 'Calefactor'},
            'r3': {'state': False, 'mode': 2, 'name': 'Humidificador'},
            'r4': {'state': False, 'mode': 2, 'name': 'Luz'}
        }
    }
    
    # Crear sistema experto y evaluar
    experto = ExpertSystem()
    diagnostico = experto.evaluar(datos_test)
    
    print("\n" + "="*70)
    print("⚙️ SISTEMA EXPERTO - DIAGNÓSTICO")
    print("="*70)
    print(f"\n📊 Estado General: {diagnostico['estado_general'].upper()}")
    print(f"🔴 Severidad Máxima: {diagnostico['severidad_maxima'].upper()}")
    print(f"📋 Reglas Activadas: {diagnostico['total_reglas_activadas']}")
    print(f"\n{diagnostico['resumen']}")
    
    if diagnostico['problemas']:
        print(f"\n⚠️ PROBLEMAS DETECTADOS ({len(diagnostico['problemas'])}):")
        for i, problema in enumerate(diagnostico['problemas'], 1):
            print(f"  {i}. {problema}")
    
    if diagnostico['recomendaciones']:
        print(f"\n💡 RECOMENDACIONES ({len(diagnostico['recomendaciones'])}):")
        for i, rec in enumerate(diagnostico['recomendaciones'], 1):
            print(f"  {i}. {rec}")
    
    print("\n" + "="*70)
    print("✅ Evaluación completada")
    print("="*70 + "\n")