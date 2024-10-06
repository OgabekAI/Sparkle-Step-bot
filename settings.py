from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("TOKEN")  
ADMINS = env.list("ADMIN_ID")
DB_LITE = env.str("DB_LITE")  
ADMIN_CHAT_ID = env.str("ADMIN_CHAT_ID")  
API_KEY_MAPS = env.str("API_KEY_MAPS")  
CHAT_ID = env.str("CHAT_ID")  
