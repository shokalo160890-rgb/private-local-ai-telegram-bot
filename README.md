# Private Local AI Telegram Bot

Personal Telegram bot for local LLMs through LM Studio.

## Architecture

Telegram -> Python bot.py -> LM Studio API -> Local LLM -> Telegram

## Requirements

- Linux / Ubuntu
- Python 3
- Python package: requests
- Telegram Bot Token from BotFather
- Telegram user ID
- LM Studio with local server enabled
- Local model loaded in LM Studio

## Install

git clone https://github.com/YOUR_USERNAME/private-local-ai-telegram-bot.git
cd private-local-ai-telegram-bot
bash install.sh

## Start LM Studio

Open LM Studio and start local server:

Developer -> Start Server

Default API:

http://127.0.0.1:1234

## Start bot

export TELEGRAM_BOT_TOKEN=YOUR_TOKEN
export TELEGRAM_ALLOWED_USER_ID=YOUR_TELEGRAM_ID
start-ai-bot

## Prompt files

Prompts are stored in:

~/ai-bot/prompts/

Available:

- default.txt
- ruthless.txt
- tech-expert.txt

## Telegram commands

/start
/model
/prompt

## Security

Do not commit your Telegram token.

Use environment variables only:

export TELEGRAM_BOT_TOKEN=YOUR_TOKEN
