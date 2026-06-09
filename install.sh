#!/usr/bin/env bash
set -e

PROJECT_DIR="$HOME/private-local-ai-telegram-bot"

mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/ai-bot/prompts"

cp "$PROJECT_DIR/bot.py" "$HOME/bot.py"
cp "$PROJECT_DIR/start-ai-bot" "$HOME/.local/bin/start-ai-bot"
cp "$PROJECT_DIR/prompts/"*.txt "$HOME/ai-bot/prompts/"

chmod +x "$HOME/.local/bin/start-ai-bot"

grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc" || \
echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"

echo "INSTALLED"
echo "Now run:"
echo "export TELEGRAM_BOT_TOKEN='YOUR_TOKEN'"
echo "export TELEGRAM_ALLOWED_USER_ID='YOUR_TELEGRAM_ID'"
echo "start-ai-bot"
