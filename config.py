from environs import Env

env = Env()
env.read_env()

token = env.str("TOKEN")
client_id = env.str("CLIENT_ID")
client_secret = env.str("CLIENT_SECRET")
subdomain = env.str("SUBDOMAIN")
voronka_id = env.str("VORONKA_ID")
amocrm_token = env.str("AMOCRM_TOKEN")
