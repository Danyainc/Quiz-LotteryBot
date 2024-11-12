import os
from datetime import datetime
from random import choice

import re

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
quizzes_button = KeyboardButton("Создать и отправить викторину",
                                request_poll=KeyboardButtonPollType('quiz'))

lotteries_button = KeyboardButton("Управление розыгрышами")
add_lotteries_button = KeyboardButton('Добавить розыгрыш')
list_lotteries_button = KeyboardButton('Список розыгрышей')

channel_list_button = KeyboardButton('Список добавленных каналов')

add_channel_button = KeyboardButton("Добавить канал",
                                    request_chat=KeyboardButtonRequestChat(1, True))
back_to_lottery_list_button = InlineKeyboardButton('К списку розыгрышей', callback_data='back_to_lottery_list')
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(quizzes_button, channels_button, lotteries_button, )

channels_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(add_channel_button, channel_list_button).add(
    main_menu_button)
lotteries_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(add_lotteries_button, list_lotteries_button).add(
    main_menu_button
)


@bot.message_handler(commands=['start'])
def start(message):
    print(message)
    if not is_user(message.from_user.id):
        add_user(message.from_user.id, message.from_user.username)
    bot.send_message(message.chat.id,
                     text="Добро пожаловать! (про бота) (как работать с ним)",
                     reply_markup=main_keyboard
                     )


@bot.message_handler(content_types=['poll'])
def add_poll(message):
    question = message.poll.question
    options = message.poll.options
    correct_option_id = message.poll.correct_option_id
    explanation = message.poll.explanation
    bot.send_poll(message.chat.id,
                  question=question,
                  options=options,
                  correct_option_id=correct_option_id,
                  explanation=explanation)


@bot.message_handler(func=lambda message: message.text == channels_button.text)
def channels_menu(message):
    bot.send_message(message.chat.id, 'Меню управления каналами, можно добавить канал или просмотреть уже существующие',
                     reply_markup=channels_keyboard)


@bot.message_handler(func=lambda message: message.text == main_menu_button.text)
def back_to_main_menu(message):
    bot.send_message(message.chat.id, 'главное меню',
                     reply_markup=main_keyboard)


@bot.message_handler(func=lambda message: message.text == lotteries_button.text)
def lotteries_menu(message):
    bot.send_message(message.chat.id, 'Управление розыгрыщами',
                     reply_markup=lotteries_keyboard)


@bot.message_handler(func=lambda message: message.text == add_lotteries_button.text)
def add_lottery(message):
    bot.send_message(message.chat.id,
                     'Добавление розыгрыша. Также укажите дату окончания розыгрыша DD.MM.YYYY HH:MM')
    bot.register_next_step_handler(message, process_lottery_info)


def process_lottery_info(message):
    try:
        text = message.text
        date_pattern = r'(d{2}.d{2}.d{4}(?: d{2}:d{2})?)'
        end_time = re.search(date_pattern, text).group(0)
        if len(end_time) > 10:
            end_time = datetime.strptime(end_time, '%d.%m.%Y %H:%M').timestamp()
        else:
            end_time = datetime.strptime(end_time, '%d.%m.%Y').timestamp()
        add_lottery_to_db(text, message.from_user.id, end_time)
        lottery_id = get_lotteries(message.from_user.id)[-1][0]
        send_button = InlineKeyboardButton('Отправить в канал', callback_data=f'send {lottery_id}')
        lottery_action_keyboard = InlineKeyboardMarkup().add(send_button)
        bot.send_message(message.chat.id, 'Розыгрш создан!', reply_markup=lottery_action_keyboard)
    except Exception as e:
        print(e)


@bot.message_handler(func=lambda message: message.text == list_lotteries_button.text)
def list_lottery(message, chat=None):
    lotteries = get_lotteries(message.from_user.id) if not chat else get_lotteries(chat.id)
    inline_keyboard = InlineKeyboardMarkup()
    for lottery in lotteries:
        inline_keyboard.add(InlineKeyboardButton(f'{lottery[1][:50]}...', callback_data=f'get_lottery {lottery[0]}'))
    if not chat:
        bot.send_message(message.chat.id, 'Список созданных розыгрышей',
                         reply_markup=inline_keyboard)
    else:
        bot.send_message(chat.id, 'Список созданных розыгрышей',
                         reply_markup=inline_keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('back_to_lottery_list'))
def back_to_lottery_list(callback):
    bot.delete_message(callback.message.chat.id, callback.message.id)
    list_lottery(callback.message, callback.message.chat)


def get_channel_list_keyboard(message, type_callback, chat=None, item=None):
    channels = get_channels(message.from_user.id) if not chat else get_channels(chat.id)
    item_id = item if item else None
    channels_list_inline_markup = InlineKeyboardMarkup()
    for channel_id in channels:
        channel = bot.get_chat(channel_id[0])
        callback_data = f'{type_callback} channel {channel.id} {item_id}' if item else f'{type_callback} channel {channel.id}'
        button = InlineKeyboardButton(channel.username, callback_data=callback_data)
        channels_list_inline_markup.add(button)
    return channels_list_inline_markup


def get_winner_in_lottery(lottery_id):
    users = get_users_in_lottery(lottery_id)
    if users:
        winner = choice(users)
        return winner


@bot.message_handler(func=lambda message: message.text == channel_list_button.text)
def channels_list(message):
    bot.send_message(message.chat.id,
                     'Добавленные каналы, если канала нету в списке, убедитесь, что бот добавлен в канал : ',
                     reply_markup=get_channel_list_keyboard(message, 'list'))


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('end_lottery'))
def end_lottery_callback(callback):
    lottery_id = int(callback.data.split()[1])
    lottery = get_lottery(lottery_id)
    if lottery[3] <= datetime.now().timestamp() and lottery[4]:
        channels = get_channels_with_lottery(lottery_id)
        winner = get_winner_in_lottery(lottery_id)
        if winner and channels:
            username = get_user(winner[0])
            for channel in channels:
                bot.send_message(channel[0], f'Победитель розыгрыша @{username[1]}')
        else:
            bot.answer_callback_query(callback.id, "К сожалению никто не принял участи в розыгрше")
        change_lottery_status(lottery_id, 0)

    else:
        bot.answer_callback_query(callback.id, "Розыгрыш ещё не окончен")


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('list channel'))
def send_channel(callback):
    channel = callback.data.split()[2]
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


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('back_to_channel_list'))
def back_to_channel_list(callback):
    bot.delete_message(callback.message.chat.id, callback.message.id)
    bot.send_message(callback.message.chat.id,
                     'Добавленные каналы, если канала нету в списке, убедитесь, что бот добавлен в канал : ',
                     reply_markup=get_channel_list_keyboard(callback.message, 'list', chat=callback.message.chat))


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('del_channel'))
def delete_channel_from_bot(callback):
    del_channel(int(callback.data.split()[1]))
    bot.delete_message(callback.message.chat.id, callback.message.id)
    bot.answer_callback_query(callback.id, "Вы успешно удалили канал из списка!")
    channels_list(callback.message)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('del_lottery'))
def delete_channel_from_bot(callback):
    lottery_id = int(callback.data.split()[1])
    lottery = get_lottery(lottery_id)
    if lottery[4]:
        bot.answer_callback_query(callback.id, "Нельзя удалить активный розыгрыш!")
    else:
        delete_lottery(lottery_id)
        bot.answer_callback_query(callback.id, "розыгрыш успешно удален!")
    back_to_lottery_list(callback)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('get_lottery'))
def send_lottery_in_select_channel(callback):
    lottery_id = int(callback.data.split()[1])
    bot.delete_message(callback.message.chat.id, callback.message.id)
    lottery = get_lottery(lottery_id)
    end_time = datetime.fromtimestamp(lottery[3])
    send_button = InlineKeyboardButton('Отправить в канал', callback_data=f'send {lottery_id}')
    del_lottery_button = InlineKeyboardButton('Удалить розыгрыш', callback_data=f'del_lottery {lottery_id}')
    end_lottery_button = InlineKeyboardButton('Подвести итоги розыгрыша', callback_data=f'end_lottery {lottery_id}')
    lottery_action_keyboard = InlineKeyboardMarkup().add(send_button, end_lottery_button).add(
        back_to_lottery_list_button, del_lottery_button)
    bot.send_message(callback.message.chat.id, text=f'{lottery[1]} Дата окончания {end_time}',
                     reply_markup=lottery_action_keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('send channel'))
def send_lottery_in_select_channel(callback):
    lottery_id = int(callback.data.split()[3])
    channel_id = int(callback.data.split()[2])
    if not check_lottery_in_channel(lottery_id, channel_id):
        callback_data = f'join {lottery_id}'
        participants_button = InlineKeyboardButton('Участвовать', callback_data=callback_data)
        participants_keyboad = InlineKeyboardMarkup().add(participants_button)
        bot.send_message(channel_id, callback.message.text, reply_markup=participants_keyboad)
        change_lottery_status(lottery_id, 1)
        add_lottery_to_channel(lottery_id, channel_id)
    else:
        bot.answer_callback_query(callback.id, "Вы уже отправили этот розыгрыш в канал")
    back_to_lottery_list(callback)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('send'))
def send_item_to_channel(callback):
    keyboard = get_channel_list_keyboard(callback.message, 'send',
                                         chat=callback.message.chat,
                                         item=callback.data.split()[1])
    bot.edit_message_reply_markup(callback.message.chat.id, callback.message.id, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('join'))
def callback_join_to_lottery(callback):
    user_id = callback.from_user.id
    lottery_id = callback.data.split()[1]
    lottery = get_lottery(lottery_id)
    lottery_status = lottery[4]
    lottery_end_time = lottery[3]
    print(lottery)
    if not check_user_in_lottery(lottery_id, user_id) and \
            lottery_end_time >= datetime.now().timestamp() and lottery_status:
        join_user_to_lottery(user_id, lottery_id)
        bot.answer_callback_query(callback.id, "Вы успешно участвуете в розыгрыше!")
    elif lottery_end_time < datetime.now().timestamp():
        bot.answer_callback_query(callback.id, "Розыгрыш уже закончен!")
    else:
        bot.answer_callback_query(callback.id, "Вы уже участвуете в розыгрыше!")


@bot.message_handler(commands=['help'])
def help_message(message):
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
