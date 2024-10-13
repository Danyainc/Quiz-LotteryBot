import os
import random
import logging
from pprint import pprint

from dotenv import load_dotenv
import telebot
from telebot import types
import time
import threading
from telebot.types import Poll
from telebot.apihelper import get_chat
import re

from telebot.types import KeyboardButtonRequestChat, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton, KeyboardButtonPollType

load_dotenv()

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

channels_button = KeyboardButton("Управление каналами",
                                 request_chat=KeyboardButtonRequestChat(1, True))
quizzes_button = KeyboardButton("Управление викторинами",
                                request_poll=KeyboardButtonPollType('quiz'))
lotteries_button = KeyboardButton("Управление розыгрышами")

add_channel_button = InlineKeyboardButton("Начать чат",
                                          callback_data='add_chanel')
add_quiz_button = InlineKeyboardButton("Начать чат",
                                       callback_data='add_group')
add_lottery_button = InlineKeyboardButton("Начать чат",
                                          callback_data='add_group')
del_lottery_button = InlineKeyboardButton("Начать чат",
                                          callback_data='add_group')
del_quiz_button = InlineKeyboardButton("Начать чат",
                                       callback_data='add_group')

main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(quizzes_button, channels_button, lotteries_button, )


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
                     text="Добро пожаловать!",
                     reply_markup=main_keyboard
                     )


@bot.message_handler(content_types=['poll'])
def start(message):
    question = message.poll.question
    options = message.poll.options
    correct_option_id = message.poll.correct_option_id
    explanation = message.poll.explanation
    bot.send_poll(message.chat.id,
                  question=question,
                  options=options,
                  correct_option_id=correct_option_id,
                  explanation=explanation)


@bot.message_handler(commands=['help'])
def help(message):
    ...


@bot.callback_query_handler(func=lambda call_back: call_back.data == 'add_chanel')
def add_chanel(call):
    message = call.message
    print(message)


@bot.message_handler(content_types=['chat_shared'])
def show_chanel_info(message):
    bot.send_message(message.from_user.id, 'успех')


bot.polling()
