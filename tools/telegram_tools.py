from crewai.tools import tool
from config import settings
from utils import log
from utils.translation import translate_text_sync
from pymongo import MongoClient
import requests

_mongo_client = MongoClient(settings.MONGODB_URL)
_mongo_db = _mongo_client[settings.MONGODB_DB_NAME]
_users_collection = _mongo_db["users"]


def _get_user_language(chat_id: str) -> str:
    try:
        doc = _users_collection.find_one({"telegram_id": str(chat_id)}, {"preferred_language": 1})
        lang = doc.get("preferred_language") if doc else None
        if lang in ("en", "hi", "mr"):
            return lang
    except Exception as db_err:
        log.warning("Unable to fetch language for %s: %s", chat_id, db_err)
    return "en"


@tool("Send Telegram Message")
def send_telegram_message(chat_id: str, message: str, parse_mode: str = "HTML") -> str:
    """
    Send a message to a user via Telegram.
    """
    try:
        # Detect user language
        language = _get_user_language(chat_id)
        snippet = message[:200].replace("\n", " ")
        log.info("🧠 Gemini response for %s (lang=%s): %s", chat_id, language, snippet)

        # ALWAYS translate BEFORE sending
        if language != "en":
            translated = translate_text_sync(message, language)
            text_to_send = translated if translated else message
        else:
            text_to_send = message

        log.info("🌐 Sending in %s language", language)

        # Send message to Telegram
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text_to_send,
            "parse_mode": parse_mode
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        log.info(f"✅ Message sent to {chat_id}")
        return f"Message sent successfully to {chat_id}"

    except Exception as e:
        log.error(f"❌ Error sending Telegram message: {str(e)}")
        return f"Error sending message: {str(e)}"


@tool("Broadcast Telegram Message")
def broadcast_telegram_message(chat_ids: list, message: str) -> str:
    """
    Broadcast a message to multiple users via Telegram.
    """
    try:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        success_count = 0

        for chat_id in chat_ids:
            try:
                language = _get_user_language(chat_id)

                # Same translation logic with fallback
                if language != "en":
                    translated = translate_text_sync(message, language)
                    text_to_send = translated if translated else message
                else:
                    text_to_send = message

                payload = {
                    "chat_id": chat_id,
                    "text": text_to_send,
                    "parse_mode": "HTML"
                }

                response = requests.post(url, json=payload)
                response.raise_for_status()
                success_count += 1

            except Exception as e:
                log.error(f"Failed to send to {chat_id}: {str(e)}")
                continue

        log.info(f"Broadcast completed: {success_count}/{len(chat_ids)} successful")
        return f"Broadcast completed: {success_count}/{len(chat_ids)} messages sent successfully"

    except Exception as e:
        log.error(f"Error broadcasting messages: {str(e)}")
        return f"Error broadcasting messages: {str(e)}"
