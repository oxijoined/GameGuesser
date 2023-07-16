from dotenv import load_dotenv
import os
import telebot
import random
from dataclasses import dataclass
import json

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

users = {}


@dataclass
class Game:
    id: int
    name: str
    background_image: str


def choose_games(num_games=8):
    games_list = []

    # Чтение данных из файла games.json
    with open("games.json", "r") as file:
        games_data = json.load(file)

    # Создание экземпляров класса Game на основе данных из файла
    for game_data in games_data:
        game_obj = Game(
            id=game_data["id"],
            name=game_data["name"],
            background_image=game_data["background_image"],
        )
        games_list.append(game_obj)

    # Проверка на количество требуемых игр
    num_games = min(num_games, len(games_list))

    # Выбор уникальных случайных игр из списка
    random_games = random.sample(games_list, num_games)

    return random_games


def load_scores():
    if os.path.exists("scores.json"):
        with open("scores.json", "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}  # Return an empty dictionary if the file is empty or invalid
    else:
        return {}



def save_scores(scores):
    with open("scores.json", "w") as file:
        json.dump(scores, file)

@bot.message_handler(commands=["top"])
def top_handler(message):
    scores = load_scores()  # Load scores from file
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)  # Sort scores in descending order

    # Generate a formatted leaderboard string
    leaderboard = "🏆 Топ игроков:\n"
    for i, (user_id, score) in enumerate(sorted_scores[:10], start=1):
        user = bot.get_chat_member(message.chat.id, user_id)
        username = user.user.username if user.user.username else user.user.first_name
        leaderboard += f"{i}. @{username}: {score}\n"

    bot.reply_to(message, leaderboard)


@bot.message_handler(commands=["me"])
def me_handler(message):
    if message.from_user.id not in users:
        users[message.from_user.id] = {"score": 0}

    scores = load_scores()  # Load scores from file

    if str(message.from_user.id) in scores:
        users[message.from_user.id]["score"] = scores[str(message.from_user.id)]
    else:
        scores[str(message.from_user.id)] = users[message.from_user.id]["score"]

    # Update the score in the user's dictionary
    users[message.from_user.id]["score"] = scores[str(message.from_user.id)]

    save_scores(scores)  # Save the updated scores to scores.json

    bot.reply_to(
        message, f'Ваш счет: <code>{users[message.from_user.id]["score"]}</code>'
    )


@bot.message_handler(commands=["start"])
def start_handler(message):
    if message.from_user.id not in users:
        users[message.from_user.id] = {"score": 0}
    games = choose_games()
    valid_game = games[random.randint(0, len(games) - 1)]
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    for game in games:
        if game == valid_game:
            markup.add(
                telebot.types.InlineKeyboardButton(
                    game.name, callback_data=f"true|{valid_game.name[:58]}"
                )
            )
        else:
            markup.add(
                telebot.types.InlineKeyboardButton(
                    game.name, callback_data=f"false|{valid_game.name[:58]}"
                )
            )
    bot.send_photo(
        chat_id=message.chat.id,
        caption="Угадайте игру по скриншоту",
        photo=valid_game.background_image,
        reply_to_message_id=message.id,
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id not in users:
        users[call.from_user.id] = {"score": 0}

    call.data = call.data.split("|")
    game = call.data[1]
    game_ = game
    valid = call.data[0]
    if valid == "true":
        users[call.from_user.id]["score"] += 1
        scores = load_scores()
        scores[str(call.from_user.id)] = users[call.from_user.id]["score"]
        save_scores(scores)

    games = choose_games()
    valid_game = games[random.randint(0, len(games) - 1)]
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    for game in games:
        if game == valid_game:
            markup.add(
                telebot.types.InlineKeyboardButton(
                    game.name, callback_data=f"true|{valid_game.name[:58]}"
                )
            )
        else:
            markup.add(
                telebot.types.InlineKeyboardButton(
                    game.name, callback_data=f"false|{valid_game.name[:58]}"
                )
            )
    bot.edit_message_media(
        media=telebot.types.InputMediaPhoto(media=valid_game.background_image),
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        reply_markup=markup,
    )
    bot.answer_callback_query(
        call.id,
        f"✅ Вы угадали, это {game_}"
        if valid == "true"
        else f"❌ Вы не угадали, это {game_}",
    )


bot.infinity_polling()
