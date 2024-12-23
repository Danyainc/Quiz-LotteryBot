from telebot.states import StatesGroup, State

from db_sql_alchemy import *
import telebot

from handlers import channels_handlers, lotteries_handlers, quizzes_handlers
from markups import main_keyboard, main_menu_button
from settings import bot

logger = telebot.logger
user_data = {}


class QuizForm(StatesGroup):
    add_question = State()
    add_answer = State()


@bot.message_handler(commands=['start'])
def start(message):
    if not is_user(message.from_user.id):
        add_user(message.from_user.id, message.from_user.username)
    bot.send_message(message.chat.id,
                     text="Добро пожаловать!",
                     reply_markup=main_keyboard
                     )


@bot.message_handler(func=lambda message: message.text == main_menu_button.text)
def back_to_main_menu(message):
    bot.send_message(message.chat.id, 'главное меню',
                     reply_markup=main_keyboard)


channels_handlers.register_handlers(bot)
quizzes_handlers.register_handlers(bot)
lotteries_handlers.register_handlers(bot)


bot.polling()
