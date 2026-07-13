import telebot
from telebot import types
import os
import requests
import json
from dotenv import load_dotenv
from pathlib import Path

# Загрузка токена
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    print(" Токен не найден!")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)
amount = 0
base_currency = "USD"
target_currency = "EUR"

# API ключ для ExchangeRate (бесплатный, регистрация не нужна)
API_URL = "https://api.exchangerate-api.com/v4/latest/"

@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    btn_usd = types.KeyboardButton("USD ➡️ EUR")
    btn_eur = types.KeyboardButton("EUR ➡️ USD")
    btn_usd_gbp = types.KeyboardButton("USD ➡️ GBP")
    btn_eur_gbp = types.KeyboardButton("EUR ➡️ GBP")
    btn_other = types.KeyboardButton(" Другая пара")
    btn_help = types.KeyboardButton("ℹ Помощь")
    
    markup.add(btn_usd, btn_eur, btn_usd_gbp, btn_eur_gbp, btn_other, btn_help)
    
    bot.send_message(
        message.chat.id,
        "💱 Привет! Я конвертер валют!\n\n"
        "Введите сумму и выберите валютную пару.\n"
        "Например: 100 USD/EUR",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, get_amount)

def get_amount(message):
    global amount
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            bot.send_message(message.chat.id, " Сумма должна быть больше 0!")
            bot.register_next_step_handler(message, get_amount)
            return
        bot.send_message(
            message.chat.id, 
            f" Сумма: {amount}\nТеперь выберите валютную пару"
        )
    except ValueError:
        bot.send_message(message.chat.id, " Введите число!")
        bot.register_next_step_handler(message, get_amount)

@bot.message_handler(func=lambda message: message.text in ["USD ➡️ EUR", "EUR ➡️ USD", "USD ➡️ GBP", "EUR ➡️ GBP"])
def currency_buttons(message):
    global base_currency, target_currency
    
    if message.text == "USD  EUR":
        base_currency, target_currency = "USD", "EUR"
    elif message.text == "EUR  USD":
        base_currency, target_currency = "EUR", "USD"
    elif message.text == "USD  GBP":
        base_currency, target_currency = "USD", "GBP"
    elif message.text == "EUR  GBP":
        base_currency, target_currency = "EUR", "GBP"
    
    convert_currency(message)

def convert_currency(message):
    global amount, base_currency, target_currency
    
    try:
        # Получаем курс
        response = requests.get(f"{API_URL}{base_currency}")
        
        if response.status_code == 200:
            data = response.json()
            rate = data['rates'][target_currency]
            result = amount * rate
            
            bot.send_message(
                message.chat.id,
                f" {amount} {base_currency} = {result:.2f} {target_currency}\n\n"
                f" Курс: 1 {base_currency} = {rate:.4f} {target_currency}\n"
                f" Чтобы начать заново, введите /start"
            )
        else:
            bot.send_message(message.chat.id, " Ошибка получения курса валют. Попробуйте позже.")
            
    except Exception as e:
        bot.send_message(message.chat.id, f" Ошибка: {str(e)}")

@bot.message_handler(func=lambda message: message.text == "🔄 Другая пара")
def other_pair(message):
    bot.send_message(
        message.chat.id,
        "Введите валютную пару в формате:\n"
        "USD/EUR\n"
        "EUR/USD\n"
        "GBP/USD\n"
        "и т.д."
    )
    bot.register_next_step_handler(message, custom_currency)

def custom_currency(message):
    global base_currency, target_currency, amount
    
    try:
        text = message.text.upper().strip()
        if "/" not in text:
            bot.send_message(message.chat.id, " Используйте формат: USD/EUR")
            bot.register_next_step_handler(message, custom_currency)
            return
        
        base, target = text.split("/")
        
        if len(base) != 3 or len(target) != 3:
            bot.send_message(message.chat.id, "Используйте 3-буквенные коды валют")
            bot.register_next_step_handler(message, custom_currency)
            return
        
        base_currency, target_currency = base, target
        convert_currency(message)
        
    except Exception as e:
        bot.send_message(message.chat.id, f" Ошибка: {str(e)}")
        bot.register_next_step_handler(message, custom_currency)

@bot.message_handler(func=lambda message: message.text == "ℹ️ Помощь")
def help_command(message):
    bot.send_message(
        message.chat.id,
        " Как пользоваться ботом:\n\n"
        "1️ Введите сумму\n"
        "2️ Выберите валютную пару\n"
        "3️ Получите результат!\n\n"
        " Доступные валюты: USD, EUR, GBP, JPY, CNY, RUB и др.\n"
        " Пример: 100 USD/EUR\n\n"
        " Для начала заново - /start"
    )

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    # Если пользователь вводит сумму напрямую
    try:
        float(message.text)
        get_amount(message)
    except ValueError:
        bot.send_message(message.chat.id, " Неизвестная команда. Используйте /start")

if __name__ == "__main__":
    print(" Бот-конвертер запущен!")
    bot.infinity_polling()