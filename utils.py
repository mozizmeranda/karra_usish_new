from config import *
import requests
import httpx
import json
import traceback


def notify_admin(function_name: str, message_error: str, **kwargs):
    try:

        json_data = json.dumps(kwargs, ensure_ascii=False, separators=(',\n', ':'))

        text = (f"Function:\n ```function\n{function_name}```\n\nError:\n```Error\n{message_error}``` \n "
                f"\nParams:```json\n{json_data}```")

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': 827950639,
            'text': text,
            'parse_mode': 'MarkdownV2'
        }

        requests.post(url, data=payload)

    except Exception as exp:
        print("Notify_admin_error: ", exp)


# ✅ Создаем единый httpx клиент
http_client = httpx.AsyncClient(
    timeout=10.0,
    limits=httpx.Limits(
        max_keepalive_connections=50,
        max_connections=100,
        keepalive_expiry=20
    )
)

headers = {
    "Authorization": f"Bearer {amocrm_token}",
    "Content-Type": "application/json"
}


# ✅ АСИНХРОННАЯ ВЕРСИЯ create_lead
async def create_lead(full_name: str, number: str, username: str):
    """Создание контакта и лида через API"""
    con_url = "https://uzbekistangroup2024.amocrm.ru/api/v4/contacts"

    data = [
        {
            "name": full_name,
            "custom_fields_values": [
                {
                    "field_id": 897225,
                    "values": [
                        {
                            "value": number,
                        }
                    ]
                },
                {
                    "field_id": 949583,
                    "values": [
                        {
                            "value": username,
                        }
                    ]
                }
            ]
        }
    ]

    try:
        # Создаем контакт
        response = await http_client.post(con_url, headers=headers, json=data)
        response.raise_for_status()
        contact_data = response.json()
        con_id = contact_data['_embedded']['contacts'][0]['id']

        # Создаем лид
        url = "https://uzbekistangroup2024.amocrm.ru/api/v4/leads"
        lead_data = [
            {
                "name": full_name,
                "pipeline_id": PIPELINE_ID,
                "_embedded": {
                    "contacts": [{"id": con_id}],
                    "tags": [{"name": "lending"}]
                }
            }
        ]

        lead_response = await http_client.post(url, headers=headers, json=lead_data)
        lead_response.raise_for_status()

        return con_id

    except httpx.HTTPError as e:
        print(f"❌ Ошибка create_lead: {e}")
        notify_admin(create_lead.__name__, str(e), full_name=full_name, number=number)
        return None


async def contact_new_data(contact_id: int, turnover: str, role: str):
    """Обновление данных контакта"""
    url = f"https://uzbekistangroup2024.amocrm.ru/api/v4/contacts/{contact_id}"

    data = {
        "custom_fields_values": [
            {
                "field_id": 950547,  # поле "роль"
                "values": [
                    {
                        "value": role
                    }
                ]
            },
            {
                "field_id": 950549,  # поле "оборот"
                "values": [
                    {
                        "value": turnover
                    }
                ]
            }
        ]
    }

    try:
        response = await http_client.patch(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPError as e:
        print(f"❌ Ошибка contact_new_data: {e}")
        notify_admin(create_lead.__name__, str(e), traceback=traceback.format_exc(), contact_id=contact_id,
                     num_emploeyes=num_emploeyes, turnover=turnover, role=role)
        return None


# ✅ АСИНХРОННАЯ ВЕРСИЯ get_lead
async def get_lead(number: str):
    """Получение лида по номеру телефона"""
    contact_url = "https://uzbekistangroup2024.amocrm.ru/api/v4/contacts"

    contact_params = {
        'query': number,
        'with': "leads"
    }

    try:
        response = await http_client.get(contact_url, headers=headers, params=contact_params)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPError as e:
        print(f"❌ Ошибка get_lead: {e}")
        notify_admin(create_lead.__name__, str(e), traceback=traceback.format_exc(), number=number)
        return None


# ✅ Функция для закрытия клиента при выключении бота
async def close_http_client():
    """Закрываем httpx клиент"""
    await http_client.aclose()


# asyncio.run(get_lead("958300800"))
