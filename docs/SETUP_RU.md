# Установка Private Local AI Telegram Bot

## Что это

Личный Telegram-бот, который подключается к локальной AI-модели через LM Studio.

Схема:

Telegram -> bot.py -> LM Studio -> локальная модель -> ответ в Telegram

## Требования

- Linux / Ubuntu
- Python 3
- пакет requests
- Telegram Bot Token от BotFather
- Telegram user ID
- LM Studio
- локальная модель в LM Studio

## Установка

git clone https://github.com/YOUR_USERNAME/private-local-ai-telegram-bot.git
cd private-local-ai-telegram-bot
bash install.sh

## Запуск

1. Открой LM Studio.
2. Включи сервер:

Developer -> Start Server

3. В терминале:

export TELEGRAM_BOT_TOKEN=ТОКЕН_ОТ_BOTFATHER
export TELEGRAM_ALLOWED_USER_ID=ТВОЙ_TELEGRAM_ID
start-ai-bot

## Проверка в Telegram

/start
/model
/prompt
Скажи коротко: ты работаешь?

## Настройка поведения

Редактируй prompt-файл:

nano ~/ai-bot/prompts/default.txt

## Важно

Не сохраняй Telegram token в GitHub.
Токен должен передаваться только через переменную окружения TELEGRAM_BOT_TOKEN.
