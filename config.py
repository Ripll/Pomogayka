from telebot import TeleBot

API_KEY = "745940012:AAFUqSm0vxu8bLcOsqWlzRvXnuRZZTPxqI0"

ADMIN_CHAT = -334061694

CHANNELS = {
    "": -1001168829061,
    "1": -1001375758569,
    "3": -1001387451254,
    "4": -1001252184285,
    "6": -1001488678147,
    "7": -1001352174176,
    "8": -1001353268231,
    "9": -1001458246450,
    "10": -1001248293966,
    "11": -1001357602486,
    "12": -1001483247823,
    "13": -1001408652105,
    "14": -1001272701189,
    "15": -1001348608302,
    "16": -1001380528088,
    "17": -1001195639666,
    "18": -1001359051512,
    "19": -1001284031401,
    "20": -1001283201112,
    "21": -1001369422411,
    "22": -1001361481497
}

bot = TeleBot(API_KEY)


WEBHOOK_HOST = '80.211.161.225'
WEBHOOK_PORT = 88  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '80.211.161.225'  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (API_KEY)

