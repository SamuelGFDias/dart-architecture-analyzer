#!/bin/bash
# Script de desinstalação do Dart Architecture Analyzer
# Uso: ./uninstall.sh

set -e

echo "🗑️  Desinstalando Dart Architecture Analyzer..."
echo ""

# Determina diretório de instalação
if [ "$(uname)" == "Darwin" ]; then
    INSTALL_DIR="/usr/local/bin"
else
    INSTALL_DIR="$HOME/.local/bin"
fi

FILES=("dart-analyse" "dart-analyse.py")
REMOVED=0

for file in "${FILES[@]}"; do
    FILE_PATH="$INSTALL_DIR/$file"
    if [ -f "$FILE_PATH" ]; then
        rm -f "$FILE_PATH"
        echo "✓ Removido: $file"
        REMOVED=$((REMOVED + 1))
    fi
done

echo ""

if [ $REMOVED -eq 0 ]; then
    echo "ℹ️  Nenhum arquivo encontrado para remover"
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Desinstalação concluída! ($REMOVED arquivo(s) removido(s))"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

echo ""
