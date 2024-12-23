import telebot
from dotenv import load_dotenv
import os

from telebot import StateMemoryStorage

load_dotenv()
storage = StateMemoryStorage()
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN, state_storage=storage)
user_data = {}
