import json

import httpx

from app.core.config import settings


async def openai_chat_completion(system: str, user_content: str) -> str:
    if not settings.openai_api_key:
        return ""
    url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}
    body = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()


async def classify_user_category_from_messages(messages: list[dict[str, str]]) -> str:
    """
    Returns one of: IT, Искусство, История (aligned with Android routes flow).
    """
    if not settings.openai_api_key:
        # deterministic fallback
        blob = " ".join(m.get("content", "") for m in messages).lower()
        if "истор" in blob or "музей" in blob:
            return "История"
        if "искус" in blob or "театр" in blob:
            return "Искусство"
        return "IT"

    user_blob = json.dumps(messages, ensure_ascii=False)
    system = (
        "Ты классификатор. По диалогу пользователя верни РОВНО одно слово-категорию из списка: "
        "IT, Искусство, История. Без пояснений."
    )
    text = await openai_chat_completion(system, user_blob)
    t = text.strip().replace(".", "")
    if t in ("IT", "Искусство", "История"):
        return t
    return "IT"


async def assistant_reply(conversation_summary: str) -> str:
    if not settings.openai_api_key:
        return "Сервер чата не настроен (нет OPENAI_API_KEY). Добавь ключ на backend."
    system = "Ты помощник по туризму и событиям в городе. Отвечай кратко по-русски."
    return await openai_chat_completion(system, conversation_summary)
