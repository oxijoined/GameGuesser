from dotenv import load_dotenv
import os
import rawg
import json
import asyncio
from dataclasses import dataclass
from tqdm import tqdm

load_dotenv()  # Загрузка переменных окружения

RAWG_KEY = os.getenv("RAWG")  # Получение значения ключа RAWG из переменных окружения

games_list = []  # Создание пустого списка игр


@dataclass
class Game:  # Определение класса Game с помощью декоратора @dataclass
    id: int
    name: str
    background_image: str
    screenshots: list


async def requests():  # Определение асинхронной функции requests
    async with rawg.ApiClient(
        rawg.Configuration(api_key={"key": RAWG_KEY})
    ) as api_client:
        api = rawg.GamesApi(api_client)
        total_pages = 100
        with tqdm(total=total_pages, desc="Обработка страниц") as pbar_pages:
            for page in range(1, total_pages + 1):
                games = await api.games_list(
                    page_size=1000, page=page
                )  # Получение списка игр с использованием API
                for game in games.results:  # Перебор игр в полученном списке
                    screenshots_list = []
                    screenshots = await api.games_screenshots_list(
                        game.id
                    )  # Получение списка скриншотов для текущей игры
                    for screenshot in screenshots.results:  # Перебор скриншотов
                        screenshots_list.append(
                            screenshot.image
                        )  # Добавление ссылки на скриншот в список
                    game_obj = Game(
                        game.id, game.name, game.background_image, screenshots_list
                    )  # Создание объекта Game
                    games_list.append(game_obj)  # Добавление объекта Game в список игр
                pbar_pages.update(1)  # Увеличение значения прогресс-бара
        json_data = json.dumps(
            [game.__dict__ for game in games_list], indent=4
        )  # Преобразование списка игр в JSON-формат
        with open("games.json", "w") as file:
            file.write(json_data)  # Запись JSON-данных в файл 'games.json'


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(
        requests()
    )  # Вызов асинхронной функции requests и запуск цикла событий asyncio
