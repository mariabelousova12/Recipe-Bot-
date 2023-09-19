import os.path
from os import environ

import telebot
from telebot.handler_backends import StatesGroup, State
from telebot.storage import StateMemoryStorage
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message

import db
from category import category_with_title, has_recipes, exists_category_with_name
from func_types import Recipe
from recipe import first_recipe_in_category, left_or_target_recipe, right_or_target_recipe, recipe_text, recipe_name
from state import target_of, no_state, is_state

bot = telebot.TeleBot(environ['TOKEN'], state_storage=StateMemoryStorage())
db = db.CachedConnection(
    db.InitedDatabase(
        db.SqliteDatabase(environ['DB_NAME']),
        [
            '''
            CREATE TABLE IF NOT EXISTS category(
                id      INTEGER PRIMARY KEY,
                name    TEXT NOT NULL
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS recipe(
                id          INTEGER PRIMARY KEY,
                name        TEXT    NOT NULL,
                category    INTEGER NOT NULL,
                recipe      TEXT    NOT NULL,
                FOREIGN KEY(category) REFERENCES category(id)
            )
            '''
        ]))


class ChatState(StatesGroup):
    input_name = State()
    input_text = State()
    input_category = State()
    input_image = State()


def menu(left: Recipe, target: Recipe, right: Recipe) -> InlineKeyboardMarkup:
    arrows = []
    if left() != target():
        arrows.append(button('<', f'switch {left()}'))
    if right() != target():
        arrows.append(button('>', f'switch {right()}'))
    return (InlineKeyboardMarkup()
            .row(button('Show recipe', f'recipe {target()}'))
            .row(*arrows))


def button(text, callback_data) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def image_for(recipe: Recipe) -> str:
    custom = f'images.db/{recipe()}.jpg'
    return custom if os.path.isfile(custom) else 'images.db/default.jpg'


def has_image(recipe: Recipe) -> bool:
    return os.path.isfile(f'images.db/{recipe()}.jpg')


def state_id(message: Message):
    return {
        'chat_id': message.chat.id,
        'user_id': message.from_user.id
    }


def add_recipe_text():
    return '📝 Add recipe'


@bot.message_handler(commands=['start'])
def start(message: Message):
    categories = db.connection().execute('SELECT name FROM category').fetchall()
    markup = (telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
              .add(*[KeyboardButton(x[0]) for x in categories], row_width=3)
              .row(KeyboardButton(add_recipe_text())))
    bot.send_message(message.chat.id,
                     'Hello. I am a recipe book. '
                     'Give me a dish category and I take you recipes that I know', reply_markup=markup)


@bot.message_handler(commands=['cancel'])
def cancel(message: Message):
    if bot.get_state(message.from_user.id, message.chat.id):
        bot.delete_state(**state_id(message))
        bot.send_message(message.chat.id, 'Okay. The operation was canceled')
    else:
        bot.send_message(message.chat.id, 'There\'s nothing to cancel')


@bot.message_handler(func=no_state(target_of(bot)))
def choose_category(message: Message):
    if message.text == add_recipe_text():
        bot.set_state(**state_id(message), state=ChatState.input_name)
        bot.reset_data(**state_id(message))
        bot.send_message(message.chat.id,
                         'Fine. The recipe entry is divided into several messages.'
                         ' To get started, send the name of the recipe\n\n'
                         'If you change your mind about adding a recipe, then use the command /cancel')
        return

    if not exists_category_with_name(db, message.text)():
        bot.send_message(message.chat.id, 'This category does not exists')
        return

    category = category_with_title(db, message.text)

    if not has_recipes(db, category)():
        bot.send_message(message.chat.id, 'This category is empty yet')
        return

    target = first_recipe_in_category(db, category_with_title(db, message.text))
    name = recipe_name(db, target)
    markup = menu(left_or_target_recipe(db, target), target, right_or_target_recipe(db, target))

    with open(image_for(target), 'rb') as f:
        bot.send_photo(message.chat.id, photo=f, caption=name(), reply_markup=markup)


@bot.message_handler(func=is_state(target_of(bot), ChatState.input_name))
def input_name(message: Message):
    bot.add_data(**state_id(message), name=message.text)
    bot.set_state(**state_id(message), state=ChatState.input_text)
    bot.send_message(message.chat.id, 'Now send the recipe text')


@bot.message_handler(func=is_state(target_of(bot), ChatState.input_text))
def input_text(message: Message):
    bot.add_data(**state_id(message), text=message.text)
    bot.set_state(**state_id(message), state=ChatState.input_category)
    bot.send_message(message.chat.id,
                     'Great! Select the category on the keyboard in which the recipe will be placed')


@bot.message_handler(func=is_state(target_of(bot), ChatState.input_category))
def input_category(message: Message):
    if not exists_category_with_name(db, message.text)():
        bot.send_message(message.chat.id, 'This category does not exists')
        return
    bot.add_data(**state_id(message), category=category_with_title(db, message.text)())
    bot.set_state(**state_id(message), state=ChatState.input_image)
    bot.send_message(message.chat.id,
                     'The finish line! Submit a picture for this recipe')


@bot.message_handler(content_types=['photo'], func=is_state(target_of(bot), ChatState.input_image))
def input_image(message: Message):
    photo = bot.download_file(bot.get_file(message.photo[0].file_id).file_path)

    with bot.retrieve_data(**state_id(message)) as data:
        connection = db.connection()
        connection.execute('INSERT INTO recipe(name, category, recipe) VALUES (?, ?, ?)',
                           (data['name'], data['category'], data['text']))
        connection.commit()

        recipe_id = connection.execute('SELECT id FROM recipe WHERE name=? AND recipe=?',
                                       (data['name'], data['text'])).fetchone()[0]

    path = f'images.db/{recipe_id}.jpg'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(photo)

    bot.delete_state(**state_id(message))
    bot.send_message(message.chat.id, 'Your recipe has been added')


@bot.callback_query_handler(func=lambda call: call.data.startswith('recipe'))
def show_recipe(call: telebot.types.CallbackQuery):
    recipe = lambda: int(call.data.split()[1])
    if has_image(recipe):
        with open(image_for(recipe), 'rb') as f:
            bot.send_photo(call.message.chat.id, photo=f)
    bot.send_message(call.message.chat.id, text=f'{recipe_name(db, recipe)()}\n\n{recipe_text(db, recipe)()}')


@bot.callback_query_handler(func=lambda call: call.data.startswith('switch'))
def switch_recipe(call: telebot.types.CallbackQuery):
    recipe = lambda: int(call.data.split()[1])
    with open(image_for(recipe), 'rb') as f:
        media = telebot.types.InputMedia(type='photo', media=f, caption=recipe_name(db, recipe)())
        bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.id,
                               media=media, reply_markup=menu(left_or_target_recipe(db, recipe), recipe,
                                                              right_or_target_recipe(db, recipe)))


print('Bot is running!')
bot.infinity_polling()
