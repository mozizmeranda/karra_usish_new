from config import *
import httpx
import asyncio


PIPELINE_ID = 10578617

# ✅ Создаем единый httpx клиент
http_client = httpx.AsyncClient(
    timeout=10.0,
    limits=httpx.Limits(
        max_keepalive_connections=50,
        max_connections=100,
        keepalive_expiry=30
    )
)

headers = {
    "Authorization": f"Bearer {amocrm_token}",
    "Content-Type": "application/json"
}


# ✅ АСИНХРОННАЯ ВЕРСИЯ create_lead
async def create_lead(full_name: str, number: str):
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
                "_embedded": {"contacts": [{"id": con_id}]}
            }
        ]

        lead_response = await http_client.post(url, headers=headers, json=lead_data)
        lead_response.raise_for_status()

        return con_id

    except httpx.HTTPError as e:
        print(f"❌ Ошибка create_lead: {e}")
        return None


# ✅ АСИНХРОННАЯ ВЕРСИЯ contact_new_data
async def contact_new_data(contact_id: int, num_emploeyes: str, turnover: str, role: str):
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
            },
            {
                "field_id": 950551,  # поле "рабочие"
                "values": [
                    {
                        "value": num_emploeyes
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
        return None


# ✅ Функция для закрытия клиента при выключении бота
async def close_http_client():
    """Закрываем httpx клиент"""
    await http_client.aclose()


# asyncio.run(get_lead("958300800"))
