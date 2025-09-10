from amocrm.v2 import Contact as _Contact
from amocrm.v2 import Lead as _Lead
from amocrm.v2 import custom_field
from amocrm.v2 import tokens
from config import *
from config import amocrm_token
import requests
import json


tokens.default_token_manager(
        client_id=client_id,
        client_secret=client_secret,
        subdomain=subdomain,
        redirect_url="https://ya.ru/",
        storage=tokens.FileTokensStorage(),
    )


class Contact(_Contact):
    empl = custom_field.TextCustomField("рабочие")
    num_employees = custom_field.TextCustomField("num_emploeyes")
    turnover = custom_field.TextCustomField("оборот")
    role = custom_field.TextCustomField("роль")
    number = custom_field.ContactPhoneField(name="Телефон")


class Lead(_Lead):
    phone = custom_field.TextCustomField("phone")


def create_contact(name: str, number: str):
    contact = Contact.objects.create(
        name=name
    )
    contact.number = number
    contact.save()


def contact_save(num_emploeyes: str, turnover: str, role: str, number: str):
    contact = Contact.objects.get(query=number)
    contact.num_emploeyes = num_emploeyes
    contact.empl = num_emploeyes
    contact.turnover = turnover
    contact.role = role
    contact.save()


def lead_create_without_landing(phone_number, name):
    lead = Lead.objects.create(
        name=name,
        pipeline_id=int(voronka_id),
    )
    contact = Contact.objects.get(query=name)
    # print(name)
    lead.contacts.add(contact)
    lead.save()


# leads = Lead.objects.create(
#     name="Новая сделка 111",
#     price=500,
#     pipeline_id=voronka_id,
# )
# c = Contact.objects.get(query="+998999999990")
# leads.contacts.add(c)
# leads.save()

# contact = Contact.objects.get(query="+998999909999")
# print(contact)


headers = {
    "Authorization": f"Bearer {amocrm_token}",
    "Content-Type": "application/json"
}


def create_lead(full_name: str, number):
    con_url = "https://uzbekistangroup2024.amocrm.ru/api/v4/contacts"
    con_params = {

    }

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

    response = requests.post(con_url, headers=headers, data=json.dumps(data))
    # print(response.status_code)
    data = response.json()
    # print(data)
    con_id = data['_embedded']['contacts'][0]['id']

    url = "https://uzbekistangroup2024.amocrm.ru/api/v4/leads"
    lead_data = [
        {
            "name": full_name,
            "pipeline_id": 10046545,
            "_embedded": {"contacts": [{"id": con_id}]}
        }
    ]

    response = requests.post(url, headers=headers, data=json.dumps(lead_data))
    # print(response.status_code)

    return data['_embedded']['contacts'][0]['id']


def contact_new_data(contact_id, num_emploeyes, turnover, role):
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

    response = requests.patch(url, headers=headers, data=json.dumps(data))

    # print(response.status_code)
    # print(response.json())

