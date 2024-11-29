from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, and_, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# Создаем базу данных и сессию
DATABASE_URL = 'sqlite:///my_database.db'
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


# Определяем модели
class User(Base):
    __tablename__ = 'Users'

    telegram_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)

    quizzes = relationship("Quiz", back_populates="author")
    lotteries = relationship("Lottery", back_populates="author")
    channels = relationship("Channel", back_populates="admin")


class Quiz(Base):
    __tablename__ = 'Quizzes'

    id = Column(Integer, primary_key=True)
    author_quiz = Column(Integer, ForeignKey('Users.telegram_id'))
    question = Column(String, nullable=False)
    answers = Column(String, nullable=False)
    right_answer_ind = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    author = relationship("User", back_populates="quizzes")


class Lottery(Base):
    __tablename__ = 'Lotteries'

    id = Column(Integer, primary_key=True)
    context_lottery = Column(String)
    author_lot = Column(Integer, ForeignKey('Users.telegram_id'))
    date_end_of_lot = Column(Float, nullable=False)
    is_active = Column(Boolean, default=False)

    author = relationship("User", back_populates="lotteries")
    users = relationship("UserLottery", back_populates="lottery")
    channels = relationship("ChannelLottery", back_populates="lottery")


class UserLottery(Base):
    __tablename__ = 'UsersLotteries'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('Users.telegram_id'))
    lottery_id = Column(Integer, ForeignKey('Lotteries.id'))

    user = relationship("User")
    lottery = relationship("Lottery", back_populates="users")


class UserQuizzes(Base):
    __tablename__ = 'UsersQuizzes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('Users.telegram_id'))
    quiz_id = Column(Integer, ForeignKey('Quizzes.id'))
    right_answer = Column(Boolean, nullable=False)
    user = relationship("User")
    quiz = relationship("Quiz")


class Channel(Base):
    __tablename__ = 'Channels'

    id = Column(Integer, primary_key=True)
    channel_admin = Column(Integer, ForeignKey('Users.telegram_id'))

    admin = relationship("User", back_populates="channels")
    lotteries = relationship("ChannelLottery", back_populates="channel")


class ChannelLottery(Base):
    __tablename__ = 'ChannelsLotteries'

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('Channels.id'))
    lottery_id = Column(Integer, ForeignKey('Lotteries.id'))

    channel = relationship("Channel", back_populates="lotteries")
    lottery = relationship("Lottery", back_populates="channels")


class ChannelQuiz(Base):
    __tablename__ = 'ChannelsQuizzes'

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('Channels.id'))
    quiz_id = Column(Integer, ForeignKey('Quizzes.id'))

    quiz = relationship("Quiz")
    channel = relationship("Channel")


# Создаем таблицы
Base.metadata.create_all(engine)


# Функции для работы с базой данных
def add_user(tg_id, username):
    user = User(telegram_id=tg_id, username=username)
    session.add(user)
    session.commit()


def is_user(tg_id):
    return session.query(User).filter_by(telegram_id=tg_id).count() > 0


def get_user(tg_id):
    return session.query(User).filter_by(telegram_id=tg_id).first()


def add_channel(channel_id, tg_id):
    if is_user(tg_id):
        user = get_user(tg_id)
        channel = Channel(id=channel_id, channel_admin=user.telegram_id)
        session.add(channel)
        session.commit()


def get_channel(channel_id):
    return session.query(Channel).filter_by(id=channel_id).first()


def get_channels(tg_id):
    return session.query(Channel).filter_by(channel_admin=tg_id).all()


def del_channel(channel_id):
    channel = get_channel(channel_id)
    if channel:
        session.delete(channel)
        session.commit()


def add_lottery_to_db(text, author_id, date_end):
    lottery = Lottery(context_lottery=text, author_lot=author_id, date_end_of_lot=date_end)
    session.add(lottery)
    session.commit()


def get_lotteries(author_id):
    return session.query(Lottery).filter_by(author_lot=author_id).all()


def get_lottery(lottery_id):
    return session.query(Lottery).filter_by(id=lottery_id).first()


def join_user_to_lottery(user_id, lottery_id):
    user_lottery = UserLottery(user_id=user_id, lottery_id=lottery_id)
    session.add(user_lottery)
    session.commit()


def add_lottery_to_channel(lottery_id, channel_id):
    channel_lottery = ChannelLottery(channel_id=channel_id, lottery_id=lottery_id)
    session.add(channel_lottery)
    session.commit()


def check_lottery_in_channel(lottery_id, channel_id):
    return session.query(ChannelLottery).filter_by(channel_id=channel_id, lottery_id=lottery_id).count() > 0


def check_user_in_lottery(lottery_id, user_id):
    count = session.query(UserLottery).filter(
        and_(UserLottery.user_id == user_id, UserLottery.lottery_id == lottery_id)
    ).count()
    return count > 0


def get_channels_with_lottery(lottery_id):
    channels = session.query(ChannelLottery.channel_id).filter(
        ChannelLottery.lottery_id == lottery_id
    ).all()
    return [channel.channel_id for channel in channels]


def get_users_in_lottery(lottery_id):
    users = session.query(UserLottery.user_id).filter(
        UserLottery.lottery_id == lottery_id
    ).all()
    return [user.user_id for user in users]


def delete_lottery(lottery_id):
    session.query(Lottery).filter(Lottery.id == lottery_id).delete()
    session.query(UserLottery).filter(UserLottery.lottery_id == lottery_id).delete()
    session.query(ChannelLottery).filter(ChannelLottery.lottery_id == lottery_id).delete()
    session.commit()


def change_lottery_status(lottery_id, status):
    lottery = session.query(Lottery).filter(Lottery.id == lottery_id).first()
    if lottery:
        lottery.is_active = status
        session.commit()


def add_quiz_to_db(author_id, question, answers, right_answer):
    quiz = Quiz(author_quiz=author_id, question=question, answers=str(answers), right_answer_ind=right_answer)
    session.add(quiz)
    session.commit()


def get_last_user_quiz(author_id):
    quiz = session.query(Quiz).filter(Quiz.author_quiz == author_id).order_by(Quiz.created_at.desc()).first()
    return quiz


def get_quiz(id):
    quiz = session.query(Quiz).filter(Quiz.id == id).first()
    return quiz


def add_quiz_to_channel(quiz_id, channel_id):
    channel_quiz = ChannelQuiz(channel_id=channel_id, quiz_id=quiz_id)
    session.add(channel_quiz)
    session.commit()


def add_user_quiz_answer(quiz_id, user_id, right_answer):
    user_quiz = UserQuizzes(user_id=user_id, quiz_id=quiz_id, right_answer=right_answer)
    session.add(user_quiz)
    session.commit()


def check_user_in_quiz(quiz_id, user_id):
    count = session.query(UserQuizzes).filter(
        and_(UserQuizzes.user_id == user_id, UserQuizzes.quiz_id == quiz_id)
    ).count()
    return count > 0


def check_quiz_in_channel(quiz_id, channel_id):
    count = session.query(ChannelQuiz).filter(
        and_(ChannelQuiz.quiz_id == quiz_id, ChannelQuiz.channel_id == channel_id)
    ).count()
    return count > 0
