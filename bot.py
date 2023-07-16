from dotenv import load_dotenv
import os
import telebot
import random
from dataclasses import dataclass
import json

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

scores = []


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
                return []  # Return an empty list if the file is empty or invalid
    else:
        return []


def save_scores(scores):
    with open("scores.json", "w") as file:
        json.dump(scores, file)


def update_user(message):
    user_id = str(message.from_user.id)
    if not any(user["id"] == user_id for user in scores):
        scores.append({"id": user_id, "score": 0})


scores = load_scores()  # Load scores from file


@bot.message_handler(commands=["top"])
def top_handler(message):
    sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)  # Sort scores in descending order

    # Generate a formatted leaderboard string
    leaderboard = "🏆 Топ игроков:\n"
    for i, user in enumerate(sorted_scores[:10], start=1):
        user_id = user["id"]
        score = user["score"]
        user_info = bot.get_chat_member(message.chat.id, user_id)
        username = user_info.user.username if user_info.user.username else user_info.user.first_name
        leaderboard += f"{i}. @{username}: {score}\n"

    bot.reply_to(message, leaderboard)


@bot.message_handler(commands=["me"])
def me_handler(message):
    update_user(message)  # Update user information

    user_id = str(message.from_user.id)

    # Retrieve the current user's score
    user = next((user for user in scores if user["id"] == user_id), None)
    score = user["score"] if user else 0

    bot.reply_to(
        message, f'Ваш счет: <code>{score}</code>'
    )


@bot.message_handler(commands=["start"])
def start_handler(message):
    update_user(message)  # Update user information

    user_id = str(message.from_user.id)
    if not any(user["id"] == user_id for user in scores):
        scores.append({"id": user_id, "score": 0})
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
    update_user(call.message)  # Update user information

    user_id = str(call.from_user.id)
    user = next((user for user in scores if user["id"] == user_id), None)

    call.data = call.data.split("|")
    game = call.data[1]
    game_ = game
    valid = call.data[0]
    if valid == "true":
        if user:
            # Update the user's score
            user["score"] += 1
        else:
            # Add a new user with a score of 1
            scores.append({"id": user_id, "score": 1})

        # Save the updated scores list
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
        f"✅ Вы угадали, это {game_}, ваш счет {user['score']}"
        if valid == "true"
        else f"❌ Вы не угадали, это {game_}",
    )


bot.infinity_polling()
