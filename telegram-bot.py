#!/usr/bin/env python3
"""
🤖 BOT DE TELEGRAM COMPLETO - CONTROL TOTAL ESP32
Responde con: Texto + Audio Telegram + Audio Parlante ESP32
Incluye control de temperatura máxima y mínima
"""

import os
import json
import base64
import tempfile
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import paho.mqtt.client as mqtt
from gtts import gTTS
from io import BytesIO
import speech_recognition as sr
from pydub import AudioSegment

# ========================================
# CONFIGURACIÓN
# ========================================

TELEGRAM_TOKEN = "8491255978:AAFfDy6smKSAhkcGjtX8HxHh6cXe9RB4Y44"

MQTT_HOST = "e311193c90544b20aa5e2fc9b1c06df5.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "esp32user"
MQTT_PASS = "Esp32pass123"

# ========================================
# INICIALIZAR MQTT
# ========================================

print("🚀 Iniciando Bot Completo con Control Total...")

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.tls_set()

latest_sensor_data = {"temp": 0, "hum": 0, "alert": "OK", "setpoint": 24}
relay_states = {}
current_config = {"setpoint": 24, "hysteresis": 2, "tempMax": 30, "tempMin": 18}

def on_mqtt_connect(client, userdata, flags, rc):
    print(f"✅ MQTT conectado (rc={rc})")
    client.subscribe("esp32/sensores")
    client.subscribe("esp32/relay/status")
    client.subscribe("esp32/config")

def on_mqtt_message(client, userdata, msg):
    global latest_sensor_data, relay_states, current_config
    try:
        data = json.loads(msg.payload.decode())
        
        if msg.topic == "esp32/sensores":
            latest_sensor_data = data
            print(f"📊 Temp: {data.get('temp', 0):.1f}°C | Hum: {data.get('hum', 0):.0f}%")
        elif msg.topic == "esp32/relay/status":
            relay_states = data
        elif msg.topic == "esp32/config":
            current_config.update(data)
            latest_sensor_data['setpoint'] = data.get('setpoint', 24)
    except Exception as e:
        print(f"❌ Error MQTT: {e}")

mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message

try:
    mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
    mqtt_client.loop_start()
    print("✅ MQTT conectado")
except Exception as e:
    print(f"⚠️ MQTT: {e}")

# ========================================
# FUNCIONES DE AUDIO
# ========================================

def text_to_speech_telegram(text: str) -> BytesIO:
    """Audio MP3 para Telegram"""
    try:
        tts = gTTS(text=text, lang='es', slow=False)
        buffer = BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"❌ Error TTS Telegram: {e}")
        return None

def send_audio_to_esp32_speaker(text: str):
    """Genera audio WAV y lo envía al parlante ESP32"""
    try:
        print(f"🔊 Generando audio para parlante: {text[:60]}...")
        
        tts = gTTS(text=text, lang='es', slow=False)
        mp3_buffer = BytesIO()
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)
        
        audio = AudioSegment.from_file(mp3_buffer, format="mp3")
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(1)
        
        wav_buffer = BytesIO()
        audio.export(wav_buffer, format="wav")
        wav_bytes = wav_buffer.getvalue()
        
        b64_data = base64.b64encode(wav_bytes).decode('utf-8')
        chunk_size = 1000
        
        mqtt_client.publish("esp32/tts/audio/start", "")
        
        for i in range(0, len(b64_data), chunk_size):
            chunk = b64_data[i:i+chunk_size]
            mqtt_client.publish("esp32/tts/audio/chunk", chunk)
        
        mqtt_client.publish("esp32/tts/audio/end", "")
        print("✅ Audio enviado al parlante ESP32")
        
    except Exception as e:
        print(f"❌ Error enviando audio: {e}")

def speech_to_text(audio_file_path: str) -> str:
    """Convierte nota de voz a texto"""
    recognizer = sr.Recognizer()
    
    try:
        print("🎤 Procesando nota de voz...")
        
        audio = AudioSegment.from_file(audio_file_path)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
            wav_path = wav_file.name
            audio.export(wav_path, format='wav')
        
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='es-ES')
            print(f"✅ Reconocido: {text}")
            
        try:
            os.unlink(wav_path)
        except:
            pass
            
        return text
        
    except sr.UnknownValueError:
        return None
    except Exception as e:
        print(f"❌ Error procesando audio: {e}")
        return None

# ========================================
# FUNCIONES DE CONSULTA Y CONTROL
# ========================================

def get_sensor_data():
    return latest_sensor_data

def process_command(text: str) -> str:
    """Procesa comandos y retorna respuesta"""
    t = text.lower()
    
    # CONSULTAS
    if any(w in t for w in ['temperatura', 'temp', 'cuánto', 'cuánta', 'grados', 'clima']):
        data = get_sensor_data()
        return f"La temperatura actual es {data['temp']:.1f} grados celsius y la humedad es {data['hum']:.0f} por ciento"
    
    elif any(w in t for w in ['humedad', 'húmedo', 'húmeda']):
        data = get_sensor_data()
        return f"La humedad actual es del {data['hum']:.0f} por ciento"
    
    elif any(w in t for w in ['estado', 'cómo está', 'sistema', 'todo bien']):
        data = get_sensor_data()
        relay_info = ""
        if relay_states:
            on_count = sum(1 for r in relay_states.values() if isinstance(r, dict) and r.get('state', False))
            relay_info = f" Dispositivos activos: {on_count} de 4."
        
        if data['alert'] == 'OK':
            return f"Todo está bien. Temperatura {data['temp']:.1f} grados, Humedad {data['hum']:.0f} por ciento.{relay_info}"
        else:
            return f"Alerta: {data['alert']}. Temperatura {data['temp']:.1f} grados.{relay_info}"
    
    elif 'dispositivos' in t or 'relays' in t or 'qué está encendido' in t:
        if not relay_states:
            return "No tengo información de los dispositivos"
        
        status = []
        for i in range(1, 5):
            relay = relay_states.get(f'r{i}')
            if relay:
                state_text = "encendido" if relay['state'] else "apagado"
                status.append(f"{relay['name']}: {state_text}")
        
        return "Estado actual: " + ", ".join(status)
    
    elif 'configuración' in t or 'config' in t:
        return f"Configuración actual: Temperatura objetivo {current_config['setpoint']}°C, Histéresis {current_config['hysteresis']}°C, Temperatura máxima {current_config['tempMax']}°C, Temperatura mínima {current_config['tempMin']}°C"
    
    # CONTROL DE DISPOSITIVOS
    elif 'enciende' in t or 'prende' in t or 'activa' in t or 'encender' in t:
        if 'ventilador' in t or '1' in t:
            mqtt_client.publish("esp32/relay/1/cmd", "ON")
            return "He encendido el ventilador correctamente"
        elif 'calefactor' in t or 'calor' in t or '2' in t:
            mqtt_client.publish("esp32/relay/2/cmd", "ON")
            return "He encendido el calefactor correctamente"
        elif 'humidificador' in t or '3' in t:
            mqtt_client.publish("esp32/relay/3/cmd", "ON")
            return "He encendido el humidificador correctamente"
        elif 'luz' in t or 'foco' in t or 'lámpara' in t or '4' in t:
            mqtt_client.publish("esp32/relay/4/cmd", "ON")
            return "He encendido la luz correctamente"
        elif 'todo' in t or 'todos' in t:
            for i in range(1, 5):
                mqtt_client.publish(f"esp32/relay/{i}/cmd", "ON")
            return "He encendido todos los dispositivos"
        return "No entendí qué dispositivo encender. Di: ventilador, calefactor, humidificador o luz"
    
    elif 'apaga' in t or 'desactiva' in t or 'apagar' in t:
        if 'ventilador' in t or '1' in t:
            mqtt_client.publish("esp32/relay/1/cmd", "OFF")
            return "He apagado el ventilador"
        elif 'calefactor' in t or 'calor' in t or '2' in t:
            mqtt_client.publish("esp32/relay/2/cmd", "OFF")
            return "He apagado el calefactor"
        elif 'humidificador' in t or '3' in t:
            mqtt_client.publish("esp32/relay/3/cmd", "OFF")
            return "He apagado el humidificador"
        elif 'luz' in t or 'foco' in t or 'lámpara' in t or '4' in t:
            mqtt_client.publish("esp32/relay/4/cmd", "OFF")
            return "He apagado la luz"
        elif 'todo' in t or 'todos' in t:
            for i in range(1, 5):
                mqtt_client.publish(f"esp32/relay/{i}/cmd", "OFF")
            return "He apagado todos los dispositivos"
        return "No entendí qué dispositivo apagar. Di: ventilador, calefactor, humidificador o luz"
    
    # CAMBIO DE MODOS
    elif 'modo' in t:
        relay_num = None
        mode_name = None
        
        # Identificar relay
        if 'ventilador' in t or '1' in t:
            relay_num = 1
        elif 'calefactor' in t or '2' in t:
            relay_num = 2
        elif 'humidificador' in t or '3' in t:
            relay_num = 3
        elif 'luz' in t or '4' in t:
            relay_num = 4
        
        # Identificar modo
        if 'automático' in t or 'auto' in t:
            mode_name = 'automático'
            mode_val = 2
        elif 'manual' in t:
            mode_name = 'manual'
            mode_val = 3
        elif 'siempre encendido' in t or 'forzado on' in t:
            mode_name = 'siempre encendido'
            mode_val = 1
        elif 'siempre apagado' in t or 'forzado off' in t:
            mode_name = 'siempre apagado'
            mode_val = 0
        else:
            return "Modos disponibles: automático, manual, siempre encendido, siempre apagado"
        
        if relay_num:
            mqtt_client.publish(f"esp32/relay/{relay_num}/mode", str(mode_val))
            relay_name = ['ventilador', 'calefactor', 'humidificador', 'luz'][relay_num-1]
            return f"He cambiado el {relay_name} a modo {mode_name}"
        
        return "Especifica el dispositivo: ventilador, calefactor, humidificador o luz"
    
    # ✅ CAMBIO DE CONFIGURACIÓN - MEJORADO
    elif any(word in t for word in ['cambia', 'ajusta', 'modifica', 'pon', 'configura', 'configuración']):
        words = t.split()
        
        # Buscar número en el comando
        temp_value = None
        for word in words:
            try:
                # Intentar convertir a número (maneja comas y puntos)
                temp_value = float(word.replace(',', '.'))
                break
            except:
                continue
        
        if temp_value is None:
            return "No entendí el valor. Di un número. Ejemplo: temperatura mínima 18"
        
        # TEMPERATURA OBJETIVO (SETPOINT)
        if any(w in t for w in ['setpoint', 'objetivo', 'temperatura objetivo']):
            if 15 <= temp_value <= 35:
                mqtt_client.publish("esp32/config/set", json.dumps({"setpoint": temp_value}))
                current_config['setpoint'] = temp_value
                return f"He cambiado la temperatura objetivo a {temp_value} grados celsius"
            return "El setpoint debe estar entre 15 y 35 grados"
        
        # HISTÉRESIS
        elif any(w in t for w in ['histéresis', 'histeresis', 'margen']):
            if 0.5 <= temp_value <= 5:
                mqtt_client.publish("esp32/config/set", json.dumps({"hysteresis": temp_value}))
                current_config['hysteresis'] = temp_value
                return f"He cambiado la histéresis a {temp_value} grados"
            return "La histéresis debe estar entre 0.5 y 5 grados"
        
        # ✅ TEMPERATURA MÁXIMA
        elif any(w in t for w in ['máxima', 'maxima', 'max', 'alta', 'máx']):
            if 20 <= temp_value <= 50:
                mqtt_client.publish("esp32/config/set", json.dumps({"tempMax": int(temp_value)}))
                current_config['tempMax'] = int(temp_value)
                return f"Temperatura máxima configurada en {int(temp_value)} grados celsius. Te avisaré si la temperatura supera este valor"
            return "La temperatura máxima debe estar entre 20 y 50 grados"
        
        # ✅ TEMPERATURA MÍNIMA
        elif any(w in t for w in ['mínima', 'minima', 'min', 'baja', 'mín']):
            if 5 <= temp_value <= 25:
                mqtt_client.publish("esp32/config/set", json.dumps({"tempMin": int(temp_value)}))
                current_config['tempMin'] = int(temp_value)
                return f"Temperatura mínima configurada en {int(temp_value)} grados celsius. Te avisaré si la temperatura baja de este valor"
            return "La temperatura mínima debe estar entre 5 y 25 grados"
        
        # Si llegó aquí, no detectó qué cambiar
        return "Especifica qué quieres cambiar: temperatura mínima, temperatura máxima, setpoint o histéresis"
    
    # AYUDA
    elif 'ayuda' in t or 'comandos' in t or 'qué puedes hacer' in t:
        return """Puedo ayudarte con:

📊 CONSULTAS:
• temperatura / humedad / estado / dispositivos

🎛️ CONTROL:
• enciende/apaga ventilador, calefactor, humidificador, luz

⚙️ CONFIGURACIÓN:
• "cambia setpoint a 25"
• "temperatura mínima 18"
• "temperatura máxima 30"
• "configuración mínima 15"

🔄 MODOS:
• modo ventilador automático / manual"""
    
    return "No entendí tu comando. Escribe 'ayuda' para ver todos los comandos disponibles"

# ========================================
# HANDLERS DE TELEGRAM
# ========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Estado", callback_data='status')],
        [InlineKeyboardButton("🌡️ Temperatura", callback_data='temp')],
        [InlineKeyboardButton("🔌 Dispositivos", callback_data='devices')],
        [InlineKeyboardButton("⚙️ Configuración", callback_data='config')],
        [InlineKeyboardButton("❓ Ayuda", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
🤖 *Bot ESP32 - Control Total*

*🎤 ENVÍA NOTA DE VOZ:*
• "¿Qué temperatura hay?"
• "Enciende el ventilador"
• "Temperatura mínima 18"
• "Configuración máxima 30"

*💬 O ESCRIBE TEXTO:*
• temperatura
• enciende luz
• configuración mínima 15
• cambia temp máxima a 32

*🔊 RESPUESTA TRIPLE:*
1️⃣ 📱 Texto en Telegram
2️⃣ 🎵 Audio en Telegram
3️⃣ 🔊 Voz en Parlante ESP32

Escribe *ayuda* para ver todos los comandos 🚀
    """
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
📚 *COMANDOS DISPONIBLES*

*📊 CONSULTAS:*
• `/temp` - Ver temperatura
• `/status` - Estado del sistema
• "humedad" / "dispositivos"

*🎛️ CONTROL:*
• "enciende ventilador"
• "apaga calefactor"
• "enciende todo" / "apaga todo"

*🔄 MODOS:*
• "modo ventilador automático"
• "modo luz manual"

*⚙️ CONFIGURACIÓN:*
• "cambia setpoint a 25"
• "temperatura mínima 18"
• "temperatura máxima 30"
• "configuración mínima 15"
• "pon temp max en 32"

*🎤 NOTA DE VOZ:*
Envía cualquier comando por voz
    """
    await update.message.reply_text(text, parse_mode='Markdown')

async def temp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_sensor_data()
    
    text_msg = f"""
🌡️ *TEMPERATURA*

Temperatura: *{data['temp']:.1f}°C*
Humedad: *{data['hum']:.0f}%*
Setpoint: *{data['setpoint']:.1f}°C*
Alerta: *{data['alert']}*

Límites de Alerta:
📈 Máxima: *{current_config['tempMax']}°C*
📉 Mínima: *{current_config['tempMin']}°C*
    """
    await update.message.reply_text(text_msg, parse_mode='Markdown')
    
    audio_text = f"La temperatura es {data['temp']:.1f} grados celsius y la humedad es {data['hum']:.0f} por ciento"
    audio = text_to_speech_telegram(audio_text)
    if audio:
        await update.message.reply_voice(voice=audio)
    
    send_audio_to_esp32_speaker(audio_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_sensor_data()
    emoji = "✅" if data['alert'] == 'OK' else "⚠️"
    
    devices = ""
    if relay_states:
        for i in range(1, 5):
            r = relay_states.get(f'r{i}')
            if r:
                state = "🟢" if r['state'] else "🔴"
                devices += f"\n{state} {r['name']}"
    
    text_msg = f"""
{emoji} *ESTADO DEL SISTEMA*

🌡️ Temp: {data['temp']:.1f}°C
💧 Hum: {data['hum']:.0f}%
🎯 Setpoint: {data['setpoint']:.1f}°C

*Límites:*
📈 Max: {current_config['tempMax']}°C
📉 Min: {current_config['tempMin']}°C

*Dispositivos:*{devices}
    """
    await update.message.reply_text(text_msg, parse_mode='Markdown')
    
    audio_text = f"Sistema funcionando. Temperatura {data['temp']:.1f} grados"
    audio = text_to_speech_telegram(audio_text)
    if audio:
        await update.message.reply_voice(voice=audio)
    
    send_audio_to_esp32_speaker(audio_text)

async def devices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not relay_states:
        await update.message.reply_text("No hay información de dispositivos")
        return
    
    text = "*🔌 ESTADO DE DISPOSITIVOS*\n\n"
    
    modes = ["🔴 OFF", "🟢 ON", "🤖 AUTO", "✋ MANUAL"]
    
    for i in range(1, 5):
        r = relay_states.get(f'r{i}')
        if r:
            state = "🟢 Encendido" if r['state'] else "🔴 Apagado"
            mode = modes[r['mode']] if r['mode'] < len(modes) else "?"
            text += f"*{r['name']}*\n"
            text += f"  Estado: {state}\n"
            text += f"  Modo: {mode}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
⚙️ *CONFIGURACIÓN ACTUAL*

🎯 Temperatura Objetivo: *{current_config['setpoint']}°C*
📊 Histéresis: *{current_config['hysteresis']}°C*
🔥 Temp Máxima Alerta: *{current_config['tempMax']}°C*
❄️ Temp Mínima Alerta: *{current_config['tempMin']}°C*

*Para cambiar:*
• "temperatura mínima 18"
• "temperatura máxima 30"
• "cambia setpoint a 25"
    """
    await update.message.reply_text(text, parse_mode='Markdown')

async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para NOTAS DE VOZ"""
    await update.message.reply_text("🎤 Procesando tu nota de voz...")
    
    try:
        voice_file = await update.message.voice.get_file()
        
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            temp_path = temp_file.name
            await voice_file.download_to_drive(temp_path)
        
        text = speech_to_text(temp_path)
        
        try:
            os.unlink(temp_path)
        except:
            pass
        
        if text:
            await update.message.reply_text(f"📝 Entendí: *\"{text}\"*", parse_mode='Markdown')
            
            response = process_command(text)
            
            await update.message.reply_text(f"💬 {response}")
            
            audio = text_to_speech_telegram(response)
            if audio:
                await update.message.reply_voice(voice=audio)
            
            send_audio_to_esp32_speaker(response)
            
            print("✅ Respuesta TRIPLE enviada (Voz)")
            
        else:
            await update.message.reply_text("❌ No pude entender tu nota de voz. Habla más claro.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para MENSAJES DE TEXTO"""
    text = update.message.text
    
    if text.startswith('/'):
        return
    
    response = process_command(text)
    
    await update.message.reply_text(f"💬 {response}")
    
    audio = text_to_speech_telegram(response)
    if audio:
        await update.message.reply_voice(voice=audio)
    
    send_audio_to_esp32_speaker(response)
    
    print("✅ Respuesta TRIPLE enviada (Texto)")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    fake_update = Update(update.update_id)
    fake_update._effective_message = query.message
    
    if query.data == 'status':
        await status_command(fake_update, context)
    elif query.data == 'temp':
        await temp_command(fake_update, context)
    elif query.data == 'devices':
        await devices_command(fake_update, context)
    elif query.data == 'config':
        await config_command(fake_update, context)
    elif query.data == 'help':
        await help_command(fake_update, context)

# ========================================
# MAIN
# ========================================

def main():
    print("\n" + "="*70)
    print("🎤 BOT ESP32 - CONTROL TOTAL COMPLETO")
    print("="*70)
    print("✅ Control completo de dispositivos")
    print("✅ Cambio de configuración por voz")
    print("✅ Control de temperatura máxima/mínima")
    print("✅ Respuesta triple (Texto + Audio Telegram + Parlante)")
    print("="*70 + "\n")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("temp", temp_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("devices", devices_command))
    app.add_handler(CommandHandler("config", config_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ayuda", help_command))
    
    # Mensajes
    app.add_handler(MessageHandler(filters.VOICE, voice_message_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ Bot listo y corriendo")
    print("\n📱 Comandos disponibles:")
    print("   /start - Iniciar")
    print("   /temp - Temperatura")
    print("   /status - Estado")
    print("   /devices - Dispositivos")
    print("   /config - Configuración")
    print("   /help - Ayuda")
    print("\n🎤 Comandos por voz o texto:")
    print("   • 'temperatura mínima 18'")
    print("   • 'configuración máxima 30'")
    print("   • 'enciende ventilador'")
    print("   • 'cambia setpoint a 25'")
    print("\n" + "="*70)
    print("🤖 BOT CORRIENDO (Ctrl+C para detener)")
    print("="*70 + "\n")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__ == '__main__':
    main()