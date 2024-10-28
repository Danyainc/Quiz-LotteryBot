import os
import logging
from db import *
from dotenv import load_dotenv
import telebot

from telebot.types import KeyboardButtonRequestChat, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton, KeyboardButtonPollType

load_dotenv()

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
logger = telebot.logger

main_menu_button = KeyboardButton("Вернуться в главное меню")
channels_button = KeyboardButton("Управление каналами", )
quizzes_button = KeyboardButton("Управление викторинами",
                                request_poll=KeyboardButtonPollType('quiz'))
lotteries_button = KeyboardButton("Управление розыгрышами")

add_quiz_button = InlineKeyboardButton("Начать чат",
                                       callback_data='add_group')
add_lottery_button = InlineKeyboardButton("Начать чат",
                                          callback_data='add_group')
del_lottery_button = InlineKeyboardButton("Начать чат",
                                          callback_data='add_group')
del_quiz_button = InlineKeyboardButton("Начать чат",
                                       callback_data='add_group')
channel_list = KeyboardButton('Список добавленных каналов')
add_channel_button = KeyboardButton("Добавить канал",
                                    request_chat=KeyboardButtonRequestChat(1, True))

main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(quizzes_button, channels_button, lotteries_button, )

channels_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(add_channel_button, channel_list).add(main_menu_button)


@bot.message_handler(commands=['start'])
def start(message):
    if not is_user(message.from_user.id):
        add_user(message.from_user.id, message.from_user.username)
    bot.send_message(message.chat.id,
                     text="Добро пожаловать! (про бота) (как работать с ним)",
                     reply_markup=main_keyboard
                     )


@bot.message_handler(content_types=['poll'])
def add_poll(message):
    print(message)
    question = message.poll.question
    options = message.poll.options
    correct_option_id = message.poll.correct_option_id
    explanation = message.poll.explanation
    bot.send_poll(message.chat.id,
                  question=question,
                  options=options,
                  correct_option_id=correct_option_id,
                  explanation=explanation)


@bot.message_handler(commands=['start'])
def start(message):
    if not is_user(message.from_user.id):
        add_user(message.from_user.id, message.from_user.username)
    bot.send_message(message.chat.id,
                     text="Добро пожаловать!",
                     reply_markup=main_keyboard
                     )


@bot.message_handler(func=lambda message: message.text == channels_button.text)
def channels_menu(message):
    bot.send_message(message.chat.id, 'Меню управления каналами, можно добавить канал или просмотреть уже существующие',
                     reply_markup=channels_keyboard)


@bot.message_handler(func=lambda message: message.text == main_menu_button.text)
def channels_menu(message):
    bot.send_message(message.chat.id, 'главное меню',
                     reply_markup=main_keyboard)


@bot.message_handler(func=lambda message: message.text == channel_list.text)
def channels_list(message, chat=None):
    channels = get_channels(message.from_user.id) if not chat else get_channels(chat.id)
    channels_list_inline_markup = InlineKeyboardMarkup()
    for channel_id in channels:
        channel = bot.get_chat(channel_id[0])
        button = InlineKeyboardButton(channel.username, callback_data=f'channel {channel.id}')
        channels_list_inline_markup.add(button)
    bot.send_message(message.chat.id,
                     'Добавленные каналы, если канала нету в списке, убедитесь, что бот добавлен в канал : ',
                     reply_markup=channels_list_inline_markup)


@bot.callback_query_handler(func=lambda callback: True)
def check_callback(callback):
    if callback.data.startswith('channel'):
        channel = callback.data.split()[1]
        inline_keyboard = InlineKeyboardMarkup()
        back_to_channel_list_inline_button = InlineKeyboardButton('Назад к списку каналов',
                                                                  callback_data='back_to_channel_list')
        del_channel_inline_button = InlineKeyboardButton('Удалить канал из списка',
                                                         callback_data=f'del_channel {channel}')
        inline_keyboard.add(back_to_channel_list_inline_button, del_channel_inline_button)
        bot.edit_message_text(chat_id=callback.message.chat.id,
                              message_id=callback.message.id,
                              text=f'Был выбран {channel} channel',
                              reply_markup=inline_keyboard)
    if callback.data.startswith('del_channel'):
        del_channel(int(callback.data.split()[1]))
        bot.delete_message(callback.message.chat.id, callback.message.id)
        channels_list(callback.message)
    if callback.data.startswith('back_to_channel_list'):
        bot.delete_message(callback.message.chat.id, callback.message.id)
        channels_list(callback.message, callback.message.chat)


@bot.message_handler(commands=['help'])
def help_nessage(message):
    bot.send_message(message.chat.id, 'Help Text')


@bot.message_handler(content_types=['chat_shared'])
def show_chanel_info(message):
    if not get_channel(message.chat_shared.chat_id) and check_bot_in_channel(message.chat_shared.chat_id):
        add_channel(message.chat_shared.chat_id, message.from_user.id)
    else:
        bot.send_message(message.from_user.id, 'уже есть или не добавлен в канал')


def check_bot_in_channel(channel_id):
    try:
        chat_member = bot.get_chat_member(channel_id, bot.get_me().id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        return False


bot.polling()
