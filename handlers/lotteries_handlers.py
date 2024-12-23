from datetime import datetime
from random import choice

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re

from settings import bot
from db_sql_alchemy import get_users_in_lottery, get_channels, add_lottery_to_db, get_lotteries, get_lottery, \
    delete_lottery, check_lottery_in_channel, change_lottery_status, add_lottery_to_channel, get_user, add_user, \
    check_user_in_lottery, join_user_to_lottery, get_channels_with_lottery
from handlers.channels_handlers import get_channel_list_keyboard
from markups import lotteries_button, lotteries_keyboard, add_lotteries_button, list_lotteries_button, \
    back_to_lottery_list_button


def get_winner_in_lottery(lottery_id):
    users = get_users_in_lottery(lottery_id)
    if users:
        winner = choice(users)
        return winner


def process_lottery_info(message):
    try:
        text = message.text
        date_pattern = r'\d{2}.\d{2}.\d{4}\s\d{2}:\d{2}.*'
        end_time = re.search(date_pattern, text).group()
        end_time = datetime.strptime(end_time, '%d.%m.%Y %H:%M').timestamp()
        add_lottery_to_db(text, message.from_user.id, end_time)
        lottery = get_lotteries(message.from_user.id)[-1]
        send_button = InlineKeyboardButton('Отправить в канал', callback_data=f'send {lottery.id}')
        lottery_action_keyboard = InlineKeyboardMarkup().add(send_button)
        bot.send_message(message.chat.id, text, reply_markup=lottery_action_keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, 'Не указана дата, попробуйте создать розыгрыш еще раз')
        bot.register_next_step_handler(message, process_lottery_info)


def register_handlers(bot):
    @bot.message_handler(func=lambda message: message.text == lotteries_button.text)
    def lotteries_menu(message):
        bot.send_message(message.chat.id, 'Управление розыгрыщами',
                         reply_markup=lotteries_keyboard)

    @bot.message_handler(func=lambda message: message.text == add_lotteries_button.text)
    def add_lottery(message):
        bot.send_message(message.chat.id,
                         'Добавление розыгрыша. Также укажите дату окончания розыгрыша DD.MM.YYYY')
        bot.register_next_step_handler(message, process_lottery_info)

    @bot.message_handler(func=lambda message: message.text == list_lotteries_button.text)
    def list_lottery(message, chat=None):
        lotteries = get_lotteries(message.from_user.id) if not chat else get_lotteries(chat.id)
        inline_keyboard = InlineKeyboardMarkup()
        for lottery in lotteries:
            inline_keyboard.add(
                InlineKeyboardButton(f'{lottery.context_lottery[:50]}...', callback_data=f'get_lottery {lottery.id}'))
        if not chat:
            bot.send_message(message.chat.id, 'Список созданных розыгрышей',
                             reply_markup=inline_keyboard)
        else:
            bot.send_message(chat.id, 'Список созданных розыгрышей',
                             reply_markup=inline_keyboard)

    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('del_lottery'))
    def delete_channel_from_bot(callback):
        lottery_id = int(callback.data.split()[1])
        lottery = get_lottery(lottery_id)
        if lottery.is_active:
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
        end_time = datetime.fromtimestamp(lottery.date_end_of_lot)
        send_button = InlineKeyboardButton('Отправить в канал', callback_data=f'send {lottery_id}')
        del_lottery_button = InlineKeyboardButton('Удалить розыгрыш', callback_data=f'del_lottery {lottery_id}')
        end_lottery_button = InlineKeyboardButton('Подвести итоги розыгрыша', callback_data=f'end_lottery {lottery_id}')
        lottery_action_keyboard = InlineKeyboardMarkup().add(send_button, end_lottery_button).add(
            back_to_lottery_list_button, del_lottery_button)
        bot.send_message(callback.message.chat.id, text=f'{lottery.context_lottery} Дата окончания {end_time}',
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

    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('join'))
    def callback_join_to_lottery(callback):
        user_id = callback.from_user.id
        lottery_id = callback.data.split()[1]
        lottery = get_lottery(lottery_id)
        if not lottery:
            bot.answer_callback_query(callback.id, "Розыгрыш уже закончен!")
            return
        lottery_status = lottery.is_active
        lottery_end_time = lottery.date_end_of_lot
        if not get_user(user_id):
            add_user(user_id, callback.from_user.username)
        if not check_user_in_lottery(lottery_id, user_id) and \
                lottery_end_time >= datetime.now().timestamp() and lottery_status:
            join_user_to_lottery(user_id, lottery_id)
            bot.answer_callback_query(callback.id, "Вы успешно участвуете в розыгрыше!")
        elif lottery_end_time < datetime.now().timestamp():
            bot.answer_callback_query(callback.id, "Розыгрыш уже закончен!")
        else:
            bot.answer_callback_query(callback.id, "Вы уже участвуете в розыгрыше!")

    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('end_lottery'))
    def end_lottery_callback(callback):
        lottery_id = int(callback.data.split()[1])
        lottery = get_lottery(lottery_id)
        if lottery.date_end_of_lot <= datetime.now().timestamp() and lottery.is_active:
            channels = get_channels_with_lottery(lottery_id)
            winner = get_winner_in_lottery(lottery_id)
            if winner and channels:
                winner = get_user(winner.user_id)
                print(channels)
                for channel in channels:
                    bot.send_message(channel, f'Победитель розыгрыша @{winner.username}')
            else:
                bot.answer_callback_query(callback.id, "К сожалению никто не принял участи в розыгрше")
            change_lottery_status(lottery_id, 0)

        else:
            bot.answer_callback_query(callback.id, "Розыгрыш ещё не окончен")

    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('back_to_lottery_list'))
    def back_to_lottery_list(callback):
        bot.delete_message(callback.message.chat.id, callback.message.id)
        list_lottery(callback.message, callback.message.chat)

    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('send'))
    def send_item_to_channel(callback):
        keyboard = get_channel_list_keyboard(callback.message, 'send',
                                             chat=callback.message.chat,
                                             item=callback.data.split()[1])
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.id, reply_markup=keyboard)
