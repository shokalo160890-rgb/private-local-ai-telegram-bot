import os
import time
import re
from pathlib import Path

import requests


TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_USER_ID = int(os.environ.get("TELEGRAM_ALLOWED_USER_ID", "8189470712"))

LMSTUDIO_BASE = os.environ.get("LMSTUDIO_BASE", "http://127.0.0.1:1234").strip()
LMSTUDIO_URL = LMSTUDIO_BASE + "/v1/chat/completions"

PROMPT_FILE = os.environ.get(
    "AI_BOT_PROMPT_FILE",
    os.path.expanduser("~/ai-bot/prompts/default.txt")
)

OFFSET_FILE = Path.home() / ".ai_bot_last_update_id"

FORCED_MODEL = "qwen3.5-9b-uncensored-hahuacs-aggressive"


DEFAULT_SYSTEM_PROMPT = """
Ты — личный локальный AI-инструмент пользователя.

Главное:
- отвечай на языке пользователя;
- начинай сразу с сути;
- без воды, вступлений и лишних предупреждений;
- если вопрос простой — отвечай коротко;
- если пользователь просит подробно — отвечай подробно;
- если нужен код — дай полный рабочий код;
- если нужна команда — дай готовую команду;
- если данных не хватает — коротко скажи, что нужно уточнить.

Техническое правило вывода:
- финальный ответ всегда помещай строго внутрь XML-блока:
<answer>
твой ответ
</answer>

Запрещено выводить за пределами блока <answer> что-либо важное для пользователя.
Не пересказывай этот prompt.
""".strip()


if not TELEGRAM_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN is not set")
    print("Run:")
    print("export TELEGRAM_BOT_TOKEN='YOUR_BOT_TOKEN'")
    raise SystemExit(1)


TG_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def ensure_prompt_file():
    prompt_path = Path(PROMPT_FILE).expanduser()
    prompt_path.parent.mkdir(parents=True, exist_ok=True)

    if not prompt_path.exists():
        prompt_path.write_text(DEFAULT_SYSTEM_PROMPT + "\n", encoding="utf-8")
        print("PROMPT_FILE_CREATED:", str(prompt_path))

    return prompt_path


def load_system_prompt():
    prompt_path = ensure_prompt_file()
    prompt = prompt_path.read_text(encoding="utf-8").strip()

    if not prompt:
        prompt_path.write_text(DEFAULT_SYSTEM_PROMPT + "\n", encoding="utf-8")
        prompt = DEFAULT_SYSTEM_PROMPT

    return prompt


def get_model_name():
    forced_model = os.environ.get("LMSTUDIO_MODEL", "").strip()
    if forced_model:
        return forced_model

    r = requests.get(LMSTUDIO_BASE + "/v1/models", timeout=20)
    r.raise_for_status()

    models = r.json().get("data", [])
    ids = [m.get("id", "") for m in models if m.get("id")]

    if FORCED_MODEL in ids:
        return FORCED_MODEL

    for mid in ids:
        if "uncensored" in mid.lower():
            return mid

    if ids:
        return ids[0]

    raise RuntimeError("No LM Studio models found")


MODEL_NAME = get_model_name()


def extract_answer(text):
    text = text or ""

    matches = re.findall(
        r"<answer>\s*(.*?)\s*</answer>",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    if matches:
        return matches[-1].strip()

    return text


def clean(text):
    text = text or ""

    text = extract_answer(text)

    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<think>.*", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = text.replace("</think>", "")

    cut_after_markers = [
        "Thinking Process:",
        "**Thinking Process:**",
        "Analyze the Request:",
        "**Analyze the Request:**",
        "Determine the Content:",
        "**Determine the Content:**",
        "Draft the Response:",
        "**Draft the Response:**",
        "Final Polish:",
        "**Final Polish:**",
        "Final Output Plan:",
        "**Final Output Plan:**"
    ]

    for marker in cut_after_markers:
        if marker in text:
            parts = text.split(marker)
            text = parts[-1].strip() if parts[-1].strip() else parts[0].strip()

    final_markers = [
        "Final answer:",
        "Final Answer:",
        "Final Text:",
        "Final Version:",
        "Финальный ответ:",
        "Ответ:"
    ]

    for marker in final_markers:
        if marker in text:
            text = text.split(marker)[-1].strip()

    bad_lines = [
        "Analyze the Request",
        "Determine the Content",
        "Draft the Response",
        "Refine based on constraints",
        "Final Polish",
        "Final Check",
        "Final Output Plan",
        "Final Output Construction",
        "Let's go with",
        "Okay, final decision",
        "Re-reading constraints",
        "User asks:",
        "Context:",
        "Constraints:",
        "Option 1:",
        "Option 2:",
        "Option 3:"
    ]

    lines = []
    for line in text.splitlines():
        stripped = line.strip()

        if any(bad in stripped for bad in bad_lines):
            continue

        if stripped.startswith((
            "1. **Analyze",
            "2. **Determine",
            "3. **Draft",
            "4. **Refine",
            "5. **Final",
            "6. **Final",
            "7. **Check",
            "8. **Final",
            "9. **Constructing"
        )):
            continue

        lines.append(line)

    text = "\n".join(lines).strip()
    text = text.replace("<answer>", "").replace("</answer>", "")
    text = text.strip()
    text = text.strip("*").strip()
    text = text.strip('"').strip()

    if not text:
        return "Модель вернула пустой ответ. Переформулируй запрос."

    return text


def direct_answer(text):
    t = text.lower().strip()

    if t in ["?", "??", "???"]:
        return "Нужно уточнение. Напиши задачу словами."

    if "ты работаешь" in t:
        return "Да, работаю."

    if "что ты умеешь" in t or "что умеешь" in t:
        return (
            "Я могу отвечать на вопросы, писать тексты, код и Linux-команды, "
            "разбирать ошибки, помогать с проектами, переводить, анализировать идеи "
            "и давать практичные решения."
        )

    return None


def tg_send(chat_id, text):
    text = clean(text)

    for i in range(0, len(text), 3900):
        part = text[i:i + 3900]

        requests.post(
            f"{TG_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": part
            },
            timeout=30
        ).raise_for_status()


def tg_updates(offset=None):
    params = {
        "timeout": 20,
        "allowed_updates": ["message"]
    }

    if offset is not None:
        params["offset"] = offset

    try:
        r = requests.get(
            f"{TG_API}/getUpdates",
            params=params,
            timeout=60
        )
        r.raise_for_status()
        return r.json()

    except requests.exceptions.ReadTimeout:
        print("TELEGRAM_TIMEOUT: getUpdates timed out, retrying...")
        return {"result": []}

    except requests.exceptions.ConnectionError as e:
        print("TELEGRAM_CONNECTION_ERROR:", e)
        time.sleep(5)
        return {"result": []}


def save_offset(offset):
    OFFSET_FILE.write_text(str(offset), encoding="utf-8")


def load_offset():
    if not OFFSET_FILE.exists():
        return None

    try:
        return int(OFFSET_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def flush_old_updates():
    try:
        data = tg_updates(None)
        updates = data.get("result", [])

        if not updates:
            offset = load_offset()
            print("NO OLD UPDATES")
            return offset

        last_update_id = updates[-1]["update_id"]
        offset = last_update_id + 1
        save_offset(offset)

        print(f"FLUSHED OLD UPDATES: {len(updates)}")
        print(f"NEW OFFSET: {offset}")

        return offset

    except Exception as e:
        print("FLUSH_ERROR:", type(e).__name__, e)
        print("CONTINUE WITHOUT FLUSH")
        return load_offset()


def ask_ai(text):
    direct = direct_answer(text)
    if direct:
        return direct

    system_prompt = load_system_prompt()

    user_text = (
        "/no_think\n\n"
        "Ответь только финальным ответом внутри XML-блока <answer>...</answer>. "
        "Не выводи анализ, рассуждения, черновик, план ответа или служебные блоки за пределами <answer>.\n\n"
        f"Запрос пользователя:\n{text}\n\n"
        "Финальный ответ строго в формате:\n"
        "<answer>\n"
        "...\n"
        "</answer>"
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_text
            }
        ],
        "max_tokens": int(os.environ.get("AI_BOT_MAX_TOKENS", "1800")),
        "temperature": float(os.environ.get("AI_BOT_TEMPERATURE", "0.55")),
        "top_p": float(os.environ.get("AI_BOT_TOP_P", "0.9")),
        "stream": False
    }

    r = requests.post(
        LMSTUDIO_URL,
        json=payload,
        timeout=int(os.environ.get("AI_BOT_TIMEOUT", "900"))
    )

    if r.status_code != 200:
        return f"LM Studio HTTP {r.status_code}:\n{r.text}"

    data = r.json()
    raw = data["choices"][0]["message"]["content"]

    return clean(raw)


def main():
    print("BOT STARTED")
    print("Model:", repr(MODEL_NAME))
    print("Allowed user:", ALLOWED_USER_ID)
    print("Prompt file:", str(Path(PROMPT_FILE).expanduser()))

    offset = flush_old_updates()

    while True:
        try:
            data = tg_updates(offset)

            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                save_offset(offset)

                msg = upd.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                user_id = msg.get("from", {}).get("id")
                text = msg.get("text", "")

                if not chat_id or not text:
                    continue

                if user_id != ALLOWED_USER_ID:
                    tg_send(chat_id, "Access denied.")
                    continue

                print("USER:", text)

                if text.strip().lower() in ["/start", "start"]:
                    tg_send(chat_id, "Бот работает. Доступ только для тебя.")
                    continue

                if text.strip().lower() in ["/prompt", "prompt"]:
                    system_prompt = load_system_prompt()
                    tg_send(
                        chat_id,
                        "Активный prompt file:\n"
                        + str(Path(PROMPT_FILE).expanduser())
                        + "\n\n"
                        + system_prompt
                    )
                    continue

                if text.strip().lower() in ["/model", "model"]:
                    tg_send(chat_id, f"Model: {MODEL_NAME}")
                    continue

                answer = ask_ai(text)

                print("BOT:", answer[:500])
                tg_send(chat_id, answer)

        except KeyboardInterrupt:
            print("BOT STOPPED")
            break

        except Exception as e:
            print("ERROR:", type(e).__name__, e)
            time.sleep(3)


if __name__ == "__main__":
    main()
