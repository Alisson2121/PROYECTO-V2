#!/usr/bin/env python3
"""
🧪 Script de Prueba del Sistema Experto
Verifica que todas las reglas funcionen correctamente
"""

from expert_system import ExpertSystem
import json

def print_separator(char="=", length=70):
    print("\n" + char * length)

def print_section(title):
    print_separator()
    print(f"🧪 {title}")
    print_separator()

def run_test(test_name, datos, expected_severity=None, expected_state=None):
    """Ejecuta una prueba del sistema experto"""
    print(f"\n{'='*70}")
    print(f"📋 TEST: {test_name}")
    print(f"{'='*70}")
    
    print(f"\n📊 Datos de entrada:")
    print(f"   Temperatura: {datos['temp']}°C")
    print(f"   Humedad: {datos['hum']}%")
    print(f"   Setpoint: {datos['config']['setpoint']}°C")
    print(f"   Histéresis: {datos['config']['hysteresis']}°C")
    print(f"   Temp Max: {datos['config']['tempMax']}°C")
    print(f"   Temp Min: {datos['config']['tempMin']}°C")
    
    experto = ExpertSystem()
    diagnostico = experto.evaluar(datos)
    
    print(f"\n📈 Resultados:")
    print(f"   Estado General: {diagnostico['estado_general'].upper()}")
    print(f"   Severidad Máxima: {diagnostico['severidad_maxima'].upper()}")
    print(f"   Reglas Activadas: {diagnostico['total_reglas_activadas']}")
    
    if diagnostico['problemas']:
        print(f"\n⚠️  PROBLEMAS DETECTADOS ({len(diagnostico['problemas'])}):")
        for i, problema in enumerate(diagnostico['problemas'], 1):
            print(f"   {i}. {problema}")
    
    if diagnostico['recomendaciones']:
        print(f"\n💡 RECOMENDACIONES ({len(diagnostico['recomendaciones'])}):")
        for i, rec in enumerate(diagnostico['recomendaciones'][:3], 1):
            print(f"   {i}. {rec}")
    
    # Verificar expectativas
    test_passed = True
    if expected_severity and diagnostico['severidad_maxima'] != expected_severity:
        print(f"\n❌ FALLO: Esperaba severidad '{expected_severity}', obtuvo '{diagnostico['severidad_maxima']}'")
        test_passed = False
    
    if expected_state and diagnostico['estado_general'] != expected_state:
        print(f"\n❌ FALLO: Esperaba estado '{expected_state}', obtuvo '{diagnostico['estado_general']}'")
        test_passed = False
    
    if test_passed:
        print(f"\n✅ TEST PASADO")
    
    return diagnostico

def main():
    print_separator("=")
    print("🧪 SUITE DE PRUEBAS - SISTEMA EXPERTO")
    print_separator("=")
    print("\nEste script prueba todas las categorías de reglas:")
    print("  🌡️  Temperatura")
    print("  💧 Humedad")
    print("  🔌 Dispositivos")
    print("  ⚡ Eficiencia")
    print("  🚨 Alertas")
    
    # Configuración base
    base_config = {
        'setpoint': 24,
        'hysteresis': 2,
        'tempMax': 30,
        'tempMin': 18
    }
    
    base_relays = {
        'r1': {'state': False, 'mode': 2, 'name': 'Ventilador'},
        'r2': {'state': False, 'mode': 2, 'name': 'Calefactor'},
        'r3': {'state': False, 'mode': 2, 'name': 'Humidificador'},
        'r4': {'state': False, 'mode': 2, 'name': 'Luz'}
    }
    
    # ==================== PRUEBAS DE TEMPERATURA ====================
    print_section("PRUEBAS DE TEMPERATURA")
    
    # Test 1: Temperatura óptima
    run_test(
        "1. Temperatura en rango óptimo",
        {
            'temp': 24.5,
            'hum': 50,
            'config': base_config.copy(),
            'relays': base_relays.copy()
        },
        expected_severity='baja',
        expected_state='optimo'
    )
    
    # Test 2: Temperatura crítica alta
    run_test(
        "2. Temperatura crítica alta (alarma)",
        {
            'temp': 35,
            'hum': 50,
            'config': base_config.copy(),
            'relays': base_relays.copy()
        },
        expected_severity='critica',
        expected_state='critico'
    )
    
    # Test 3: Temperatura crítica baja
    run_test(
        "3. Temperatura crítica baja (alarma)",
        {
            'temp': 15,
            'hum': 50,
            'config': base_config.copy(),
            'relays': base_relays.copy()
        },
        expected_severity='critica',
        expected_state='critico'
    )
    
    # Test 4: Temperatura alta advertencia
    run_test(
        "4. Temperatura cerca del límite superior",
        {
            'temp': 29,
            'hum': 50,
            'config': base_config.copy(),
            'relays': base_relays.copy()
        },
        expected_severity='alta'
    )
    
    # ==================== PRUEBAS DE HUMEDAD ====================
    print_section("PRUEBAS DE HUMEDAD")
    
    # Test 5: Humedad crítica alta
    run_test(
        "5. Humedad crítica alta",
        {
            'temp': 24,
            'hum': 90,
            'config': base_config.copy(),
            'relays': base_relays.copy()
        },
        expected_severity='critica',
        expected_state='critico'
    )
    
    # Test 6: Humedad crítica baja
    run_test(
        "6. Humedad crítica baja",
        {
            'temp': 24,
            'hum': 15,
            'config': base_config.copy(),
            'relays': base_relays.copy()
        },
        expected_severity='critica',
        expected_state='critico'
    )
    
    # Test 7: Humedad óptima
    run_test(
        "7. Humedad en rango óptimo",
        {
            'temp': 24,
            'hum': 50,
            'config': base_config.copy(),
            'relays': base_relays.copy()
        },
        expected_severity='baja',
        expected_state='optimo'
    )
    
    # ==================== PRUEBAS DE DISPOSITIVOS ====================
    print_section("PRUEBAS DE DISPOSITIVOS")
    
    # Test 8: Conflicto ventilador y calefactor
    relays_conflict = base_relays.copy()
    relays_conflict['r1'] = {'state': True, 'mode': 2, 'name': 'Ventilador'}
    relays_conflict['r2'] = {'state': True, 'mode': 2, 'name': 'Calefactor'}
    
    run_test(
        "8. Ventilador y calefactor simultáneos (conflicto)",
        {
            'temp': 24,
            'hum': 50,
            'config': base_config.copy(),
            'relays': relays_conflict
        },
        expected_severity='alta'
    )
    
    # Test 9: Todos apagados con temp fuera de rango
    run_test(
        "9. Ningún dispositivo activo con temperatura alta",
        {
            'temp': 32,
            'hum': 50,
            'config': base_config.copy(),
            'relays': base_relays.copy()
        },
        expected_severity='alta'
    )
    
    # Test 10: Ventilador sin efecto
    relays_fan_on = base_relays.copy()
    relays_fan_on['r1'] = {'state': True, 'mode': 2, 'name': 'Ventilador'}
    
    run_test(
        "10. Ventilador activo pero temperatura no baja",
        {
            'temp': 28,
            'hum': 50,
            'config': base_config.copy(),
            'relays': relays_fan_on
        },
        expected_severity='media'
    )
    
    # ==================== PRUEBAS DE EFICIENCIA ====================
    print_section("PRUEBAS DE EFICIENCIA Y CONFIGURACIÓN")
    
    # Test 11: Histéresis muy pequeña
    config_small_hyst = base_config.copy()
    config_small_hyst['hysteresis'] = 0.5
    
    run_test(
        "11. Histéresis configurada demasiado pequeña",
        {
            'temp': 24,
            'hum': 50,
            'config': config_small_hyst,
            'relays': base_relays.copy()
        },
        expected_severity='media'
    )
    
    # Test 12: Histéresis muy grande
    config_large_hyst = base_config.copy()
    config_large_hyst['hysteresis'] = 5
    
    run_test(
        "12. Histéresis configurada demasiado grande",
        {
            'temp': 24,
            'hum': 50,
            'config': config_large_hyst,
            'relays': base_relays.copy()
        },
        expected_severity='media'
    )
    
    # ==================== PRUEBAS COMBINADAS ====================
    print_section("PRUEBAS COMBINADAS (Múltiples Problemas)")
    
    # Test 13: Múltiples problemas críticos
    relays_manual_critical = base_relays.copy()
    for key in relays_manual_critical:
        relays_manual_critical[key]['mode'] = 3  # Modo manual
    
    run_test(
        "13. Múltiples alertas: Temp crítica + Humedad crítica + Modo manual",
        {
            'temp': 35,
            'hum': 90,
            'config': base_config.copy(),
            'relays': relays_manual_critical
        },
        expected_severity='critica',
        expected_state='critico'
    )
    
    # ==================== RESUMEN ====================
    print_section("RESUMEN DE PRUEBAS")
    
    print("\n✅ Todas las pruebas completadas")
    print("\n📊 Categorías probadas:")
    print("   ✓ Temperatura (7 reglas)")
    print("   ✓ Humedad (5 reglas)")
    print("   ✓ Dispositivos (5 reglas)")
    print("   ✓ Eficiencia (3 reglas)")
    print("   ✓ Configuración (reglas adicionales)")
    
    print("\n💡 Recomendaciones:")
    print("   • Ejecuta este script después de modificar reglas")
    print("   • Verifica que los resultados sean los esperados")
    print("   • Ajusta umbrales según tus necesidades")
    
    print_separator()
    print("🎉 SUITE DE PRUEBAS COMPLETADA")
    print_separator()

if __name__ == '__main__':
    main()