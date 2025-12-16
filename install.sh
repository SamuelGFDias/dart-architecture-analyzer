#!/bin/bash
# Script de instalação global do Dart Architecture Analyzer
# Uso: ./install.sh

set -e

echo "📊 Instalando Dart Architecture Analyzer..."
echo ""

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "✗ Python3 não encontrado. Instale Python 3.7+ primeiro."
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  Mac: brew install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python encontrado: $(python3 --version)"

# Verifica versão mínima
REQUIRED_VERSION="3.7"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "✗ Python 3.7+ é necessário. Versão atual: $PYTHON_VERSION"
    exit 1
fi

# Obtém diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ANALYSE_SCRIPT="$SCRIPT_DIR/analyse.py"

if [ ! -f "$ANALYSE_SCRIPT" ]; then
    echo "✗ arquivo analyse.py não encontrado em $SCRIPT_DIR"
    exit 1
fi

# Diretório de instalação
if [ "$(uname)" == "Darwin" ]; then
    # macOS
    INSTALL_DIR="/usr/local/bin"
else
    # Linux
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
fi

echo "📁 Instalando em: $INSTALL_DIR"
echo ""

# Copia analyse.py
DEST_SCRIPT="$INSTALL_DIR/dart-analyse.py"
cp "$ANALYSE_SCRIPT" "$DEST_SCRIPT"
echo "✓ dart-analyse.py copiado"

# Cria wrapper executável
WRAPPER_SCRIPT="$INSTALL_DIR/dart-analyse"
cat > "$WRAPPER_SCRIPT" << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Obtém o caminho do script
script_dir = os.path.dirname(os.path.abspath(__file__))
analyse_script = os.path.join(script_dir, 'dart-analyse.py')

# Executa o script
if os.path.exists(analyse_script):
    with open(analyse_script, 'r') as f:
        code = f.read()
    exec(code)
else:
    print(f"Erro: {analyse_script} não encontrado", file=sys.stderr)
    sys.exit(1)
EOF

chmod +x "$WRAPPER_SCRIPT"
echo "✓ wrapper 'dart-analyse' criado"

# Verifica se está no PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo "⚠️  O diretório $INSTALL_DIR não está no PATH!"
    echo ""
    echo "   Adicione ao seu shell profile (~/.bashrc, ~/.zshrc, etc):"
    echo "   export PATH=\"\$PATH:$INSTALL_DIR\""
    echo ""
    
    read -p "   Adicionar ao ~/.bashrc automaticamente? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[SsYy]$ ]]; then
        echo "" >> ~/.bashrc
        echo "# Dart Architecture Analyzer" >> ~/.bashrc
        echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> ~/.bashrc
        echo ""
        echo "✓ Adicionado ao ~/.bashrc"
        echo "  Execute: source ~/.bashrc"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Instalação concluída!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Testa se jq está instalado
if command -v jq &> /dev/null; then
    echo "✓ jq detectado - filtros coloridos habilitados"
else
    echo "ℹ️  jq não encontrado - instale para habilitar colorização:"
    if [ "$(uname)" == "Darwin" ]; then
        echo "   brew install jq"
    else
        echo "   sudo apt install jq  (Ubuntu/Debian)"
        echo "   sudo yum install jq  (CentOS/RHEL)"
    fi
fi

echo ""
echo "📖 Uso:"
echo "  dart-analyse --help"
echo "  dart-analyse --output stdout | jq '.summary_kpis'"
echo "  dart-analyse --files lib/main.dart --output stdout"
echo ""
