from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from settings import bot, user_data
from db_sql_alchemy import add_quiz_to_db, get_last_user_quiz, check_quiz_in_channel, add_quiz_to_channel, get_quiz, \
    add_user, check_user_in_quiz, add_user_quiz_answer, get_channels, get_user_with_most_correct_answers, get_user, \
    reset_correct_answers
from handlers.channels_handlers import get_channel_list_keyboard
from markups import main_keyboard, quizzes_button, quizzes_menu_keyboard, add_quizzes_button, get_quiz_keyboard, \
    back_to_main_menu_inline, best_in_quizz


def question_handler(message):
    question = message.text
    bot.send_message(message.chat.id, f"Вопрос '{question}' сохранен. Теперь напиши ответ на него.")
    user_data[message.from_user.id] = {'question': question, 'answers': []}
    bot.register_next_step_handler(message, answers_handler)


def answers_handler(message):
    if message.text != "Собрать викторину":
        answer = message.text
        bot.send_message(message.chat.id,
                         f"Вариант ответа {answer} записан.\n "
                         f"Можно добавить ещё один вариант, либо нажать кнопку 'собрать викторину'",
                         reply_markup=get_quiz_keyboard)
        user_data.get(message.from_user.id).get('answers').append(answer)
        bot.register_next_step_handler(message, answers_handler)
    else:
        markup = InlineKeyboardMarkup()
        i = 0
        for answer in user_data.get(message.from_user.id).get('answers'):
            markup.add(InlineKeyboardButton(f"{answer}", callback_data=f"answer {i}"))
            i += 1
        bot.send_message(message.from_user.id, f"Выберите правильный вариант ответа:", reply_markup=markup)


def register_handlers(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('back_to_main_menu'))
    def add_correct_answer(callback):
        bot.delete_message(callback.message.chat.id, callback.message.id)
        bot.send_message(callback.message.chat.id,
                         text="Главное меню",
                         reply_markup=main_keyboard
                         )

    @bot.message_handler(func=lambda message: message.text == quizzes_button.text)
    def quiz_menu_handler(message):
        bot.send_message(message.chat.id, "Меню управления викторинами", reply_markup=quizzes_menu_keyboard)

    @bot.message_handler(func=lambda message: message.text == add_quizzes_button.text)
    def create_quiz(message):
        bot.send_message(message.chat.id, "Введите вопрос для викторины:")
        bot.register_next_step_handler(message, question_handler)

    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('answer'))
    def add_correct_answer(callback):
        data = user_data.get(callback.from_user.id)
        data['right_answer_number'] = callback.data.split()[1]
        add_quiz_to_db(callback.from_user.id, data.get('question'), data.get('answers'),
                       data.get('right_answer_number'))
        quiz = get_last_user_quiz(callback.from_user.id)
        bot.delete_message(callback.message.chat.id, callback.message.id)
        markup = get_channel_list_keyboard(callback.message,
                                           'send_quiz',
                                           chat=callback.message.chat,
                                           item=quiz.id)
        markup.add(back_to_main_menu_inline)
        bot.send_message(callback.message.chat.id, "В какие каналы отправить викторину?",
                         reply_markup=markup)
        user_data[callback.from_user.id] = None

    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('send_quiz'))
    def send_quiz_to_channel(callback):
        quiz = get_quiz(callback.data.split()[3])
        channel_id = callback.data.split()[2]
        answers = quiz.answers.replace('[', '').replace(']', '').split(', ')
        print(quiz.right_answer_ind)
        if check_quiz_in_channel(quiz.id, channel_id):
            bot.answer_callback_query(callback.id, "Эта викторина уже отправлена в этот канал")
            return
        markup = InlineKeyboardMarkup()
        i = 0
        for answer in answers:
            if i == quiz.right_answer_ind:
                print(i)
                markup.add(InlineKeyboardButton(f'{answer}', callback_data=f'user_answer {quiz.id} 1'))
            else:
                markup.add(InlineKeyboardButton(f'{answer}', callback_data=f'user_answer {quiz.id}'))
            i += 1
        bot.send_message(channel_id, quiz.question, reply_markup=markup)
        add_quiz_to_channel(quiz.id, channel_id)

    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('user_answer'))
    def send_quiz_to_channel(callback):
        user_id = callback.from_user.id
        quiz = get_quiz(callback.data.split()[1])
        if not get_user(user_id):
            add_user(user_id, callback.from_user.username)
        if not check_user_in_quiz(quiz.id, callback.from_user.id):
            bot.answer_callback_query(callback.id, "Ваш ответ записан!")
            add_user_quiz_answer(quiz.id, callback.from_user.id, callback.message.chat.id,
                                 right_answer=(len(callback.data.split()) == 3))
        else:
            bot.answer_callback_query(callback.id, "Вы уже отвечали на этот вопрос!")

    @bot.message_handler(func=lambda message: message.text == best_in_quizz.text)
    def channels_menu(message):
        channels = get_channels(message.from_user.id)
        channels_list_inline_markup = InlineKeyboardMarkup()
        for channel in channels:
            channel = bot.get_chat(channel.id)
            callback_data = f'get_best_in_channel {channel.id}'
            button = InlineKeyboardButton(channel.username, callback_data=callback_data)
            channels_list_inline_markup.add(button)
        bot.send_message(message.chat.id, 'Выберите канал для выявление лучшего участника викторин:',
                         reply_markup=channels_list_inline_markup)

    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('get_best_in_channel'))
    def back_to_lottery_list(callback):
        channel_id = callback.data.split()[1]
        user_id, right_answers_count = get_user_with_most_correct_answers(channel_id)
        if user_id:
            user = get_user(user_id)
            bot.send_message(channel_id, f'Победитель викторин этого канала - @{user.username}. \n'
                                         f'Колличество правильных ответов {right_answers_count}')
            reset_correct_answers(channel_id)
        else:
            bot.answer_callback_query(callback.id, "Никто не принимал участие в викторинах в последнее время(")
