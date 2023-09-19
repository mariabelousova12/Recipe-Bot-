from typing import Callable, Any

import telebot
from telebot.types import Message


def target_of(bot: telebot.TeleBot) -> Callable[[Message], Any]:
    return lambda message: \
        bot.get_state(user_id=message.from_user.id, chat_id=message.chat.id)


def is_state(target: Callable[[Message], Any], state: Any) -> Callable[[Message], bool]:
    return lambda message: str(target(message)) == str(state)


def no_state(target: Callable[[Message], Any]) -> Callable[[Message], bool]:
    return lambda message: target(message) is None
