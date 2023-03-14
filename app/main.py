from pprint import pprint
from aiogram import Bot
from fastapi import FastAPI, Request
from furl import furl
from environs import Env
from httpx import Client




env = Env()
app = FastAPI()
env.read_env()
DOMAIN = env("DOMAIN")
ENDPOINT = furl(f"https://{DOMAIN}")
MONOBANK_TOKEN = env("MONOBANK_TOKEN")
TELEGRAM_TOKEN = env("TELEGRAM_TOKEN")
CARD_ID = env("CARD_ID")
GROUP_ID = env.int("GROUP_ID")
OWNER_ID = env.int("OWNER_ID")
mono = Client(
    base_url="https://api.monobank.ua/personal/",
    headers={"X-Token": MONOBANK_TOKEN}
)

bot = Bot(TELEGRAM_TOKEN)


@app.get("/")
def root():
    return {}

@app.get("/swh")
def set_webhook():
    mono.post("webhook", json=dict(webHookUrl=str(ENDPOINT/"wh")))
    print(f"Webhook installed to {ENDPOINT / 'wh'}")
    return {}


@app.post("/wh")
async def wh(request: Request):
    st = await request.json()
    if st.get("type") == "StatementItem":
        if data := st.get("data"):
            if item := data.get("statementItem"):
                amount = item.get("amount")
                desc = item.get("description")
                balance = item.get("balance")
                operation_text = f"{amount/100} грн : {desc}"
                balance_text = f"{balance/100} грн"
                account = data.get("account")
                if account == CARD_ID:
                    await bot.send_message(GROUP_ID, operation_text)
                    await bot.send_message(GROUP_ID, balance_text)

                pprint(data)
    return {}

@app.on_event("shutdown")
async def shutdown():
    await bot.session.close()
    mono.post("webhook", json=dict(webHookUrl=""))
    print("webhook removed")


print(f"Open {ENDPOINT / 'swh'} to install webhook")