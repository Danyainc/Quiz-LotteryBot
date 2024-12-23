from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from settings import bot
from db_sql_alchemy import get_channel, add_channel, del_channel, get_channels
from markups import channel_list_button, channels_keyboard, channels_button


def check_bot_in_channel(channel_id):
    try:
        chat_member = bot.get_chat_member(channel_id, bot.get_me().id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        return False


def get_channel_list_keyboard(message, type_callback, chat=None, item=None):
    channels = get_channels(message.from_user.id) if not chat else get_channels(chat.id)
    item_id = item if item else None
    channels_list_inline_markup = InlineKeyboardMarkup()
    for channel in channels:
        channel = bot.get_chat(channel.id)
        callback_data = f'{type_callback} channel {channel.id} {item_id}' if item else f'{type_callback} channel {channel.id}'
        button = InlineKeyboardButton(channel.username, callback_data=callback_data)
        channels_list_inline_markup.add(button)
    return channels_list_inline_markup


def register_handlers(bot):
    @bot.message_handler(func=lambda message: message.text == channel_list_button.text)
    def channels_list(message):
        bot.send_message(message.chat.id,
                         'Добавленные каналы, если канала нету в списке, убедитесь, что бот добавлен в канал : ',
                         reply_markup=get_channel_list_keyboard(message, 'list'))

    @bot.message_handler(func=lambda message: message.text == channels_button.text)
    def channels_menu(message):
        bot.send_message(message.chat.id,
                         'Меню управления каналами, можно добавить канал или просмотреть уже существующие',
                         reply_markup=channels_keyboard)

    @bot.message_handler(content_types=['chat_shared'])
    def show_chanel_info(message):
        if not get_channel(message.chat_shared.chat_id) and check_bot_in_channel(message.chat_shared.chat_id):
            add_channel(message.chat_shared.chat_id, message.from_user.id)
        else:
            bot.send_message(message.from_user.id, 'уже есть или не добавлен в канал')

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
                              text=f'Был выбран {bot.get_chat(channel).title}',
                              reply_markup=inline_keyboard)
