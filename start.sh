#!/bin/bash

# 🚀 Script de Inicio Rápido - Sistema ESP32 + IA + Sistema Experto

echo "=========================================="
echo "🤖 Sistema ESP32 - Inicio Rápido"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar Python
echo -n "Verificando Python... "
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Python 3 no encontrado${NC}"
    exit 1
fi

# Verificar variables de entorno
echo ""
echo "Verificando variables de entorno..."

check_env() {
    if [ -z "${!1}" ]; then
        echo -e "${RED}✗ $1 no configurada${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1${NC}"
        return 0
    fi
}

all_ok=true

check_env "TELEGRAM_TOKEN" || all_ok=false
check_env "MQTT_HOST" || all_ok=false
check_env "MQTT_PORT" || all_ok=false
check_env "MQTT_USER" || all_ok=false
check_env "MQTT_PASS" || all_ok=false
check_env "SUPABASE_URL" || all_ok=false
check_env "SUPABASE_KEY" || all_ok=false

if [ "$all_ok" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Algunas variables no están configuradas${NC}"
    echo ""
    echo "Configúralas con:"
    echo "  export TELEGRAM_TOKEN='tu_token'"
    echo "  export MQTT_HOST='broker.hivemq.cloud'"
    echo "  export MQTT_PORT='8883'"
    echo "  export MQTT_USER='tu_usuario'"
    echo "  export MQTT_PASS='tu_password'"
    echo "  export SUPABASE_URL='https://tu-proyecto.supabase.co'"
    echo "  export SUPABASE_KEY='tu_anon_key'"
    echo ""
    exit 1
fi

# Verificar dependencias
echo ""
echo "Verificando dependencias Python..."

check_package() {
    python3 -c "import $1" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
        return 0
    else
        echo -e "${RED}✗ $1${NC}"
        return 1
    fi
}

deps_ok=true

check_package "telegram" || deps_ok=false
check_package "paho.mqtt.client" || deps_ok=false
check_package "supabase" || deps_ok=false
check_package "gtts" || deps_ok=false
check_package "speech_recognition" || deps_ok=false
check_package "pydub" || deps_ok=false

if [ "$deps_ok" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Instalando dependencias...${NC}"
    echo ""
    
    pip install python-telegram-bot --break-system-packages
    pip install paho-mqtt --break-system-packages
    pip install supabase --break-system-packages
    pip install gtts --break-system-packages
    pip install speechrecognition --break-system-packages
    pip install pydub --break-system-packages
    
    echo ""
    echo -e "${GREEN}✓ Dependencias instaladas${NC}"
fi

# Verificar archivos
echo ""
echo "Verificando archivos..."

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓ $1${NC}"
        return 0
    else
        echo -e "${RED}✗ $1 no encontrado${NC}"
        return 1
    fi
}

files_ok=true

check_file "bot_completo.py" || files_ok=false
check_file "expert_system.py" || files_ok=false
check_file "expert_service.py" || files_ok=false
check_file "dashboard_pro.html" || files_ok=false

if [ "$files_ok" = false ]; then
    echo ""
    echo -e "${RED}⚠️  Algunos archivos faltan${NC}"
    echo "Asegúrate de tener todos los archivos en el directorio actual"
    exit 1
fi

# Menú de inicio
echo ""
echo "=========================================="
echo "¿Qué deseas iniciar?"
echo "=========================================="
echo "1) Bot de Telegram"
echo "2) Sistema Experto"
echo "3) Servidor Web (Dashboard)"
echo "4) Todo (tmux requerido)"
echo "5) Salir"
echo ""
read -p "Selecciona una opción (1-5): " option

case $option in
    1)
        echo ""
        echo -e "${GREEN}🤖 Iniciando Bot de Telegram...${NC}"
        echo ""
        python3 bot_completo.py
        ;;
    2)
        echo ""
        echo -e "${GREEN}⚙️  Iniciando Sistema Experto...${NC}"
        echo ""
        python3 expert_service.py
        ;;
    3)
        echo ""
        echo -e "${GREEN}🌐 Iniciando Servidor Web...${NC}"
        echo ""
        echo "Dashboard disponible en: http://localhost:8000/dashboard_pro.html"
        echo ""
        python3 -m http.server 8000
        ;;
    4)
        if command -v tmux &> /dev/null; then
            echo ""
            echo -e "${GREEN}🚀 Iniciando todos los servicios...${NC}"
            echo ""
            
            # Crear sesión tmux
            tmux new-session -d -s esp32 -n 'Bot' 'python3 bot_completo.py'
            tmux new-window -t esp32 -n 'Experto' 'python3 expert_service.py'
            tmux new-window -t esp32 -n 'Web' 'python3 -m http.server 8000'
            
            echo "✓ Servicios iniciados en tmux"
            echo ""
            echo "Comandos útiles:"
            echo "  tmux attach -t esp32    # Conectar a la sesión"
            echo "  tmux ls                 # Listar sesiones"
            echo "  Ctrl+B, D               # Desconectar sin cerrar"
            echo "  tmux kill-session -t esp32  # Detener todo"
            echo ""
            echo "Dashboard: http://localhost:8000/dashboard_pro.html"
            echo ""
            
            # Adjuntar a la sesión
            tmux attach -t esp32
        else
            echo ""
            echo -e "${RED}✗ tmux no está instalado${NC}"
            echo "Instálalo con: sudo apt install tmux"
            echo ""
            echo "O inicia cada servicio manualmente en terminales separadas:"
            echo "  Terminal 1: python3 bot_completo.py"
            echo "  Terminal 2: python3 expert_service.py"
            echo "  Terminal 3: python3 -m http.server 8000"
        fi
        ;;
    5)
        echo ""
        echo "👋 ¡Hasta luego!"
        echo ""
        exit 0
        ;;
    *)
        echo ""
        echo -e "${RED}Opción inválida${NC}"
        exit 1
        ;;
esac