from telebot.types import KeyboardButton, ReplyKeyboardMarkup, KeyboardButtonRequestChat, InlineKeyboardButton

main_menu_button = KeyboardButton("Вернуться в главное меню")

channels_button = KeyboardButton("Управление каналами")
quizzes_button = KeyboardButton("Управление викторинами")
add_quizzes_button = KeyboardButton("Создать и отправить викторину")
lotteries_button = KeyboardButton("Управление розыгрышами")

main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(quizzes_button, channels_button, lotteries_button)
best_in_quizz = KeyboardButton('Вывести лучших участников викторин')
add_lotteries_button = KeyboardButton('Добавить розыгрыш')
list_lotteries_button = KeyboardButton('Список розыгрышей')

quizzes_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(add_quizzes_button, best_in_quizz).add(
    main_menu_button)
channel_list_button = KeyboardButton('Список добавленных каналов')

add_channel_button = KeyboardButton("Добавить канал",
                                    request_chat=KeyboardButtonRequestChat(1, True))
back_to_lottery_list_button = InlineKeyboardButton('К списку розыгрышей', callback_data='back_to_lottery_list')

channels_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(add_channel_button, channel_list_button).add(
    main_menu_button)
lotteries_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(add_lotteries_button, list_lotteries_button).add(
    main_menu_button
)
get_quiz_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(
    KeyboardButton('Собрать викторину'))
back_to_main_menu_inline = InlineKeyboardButton('Вернуться в главное меню', callback_data='back_to_main_menu')
