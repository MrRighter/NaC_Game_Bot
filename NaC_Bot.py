import random
import asyncio
import sqlite3

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import RetryAfter


user_games_bot = {}
db = sqlite3.connect("NaCGame.db")
cursor = db.cursor()


class NaCGameBot:
    def __init__(self, player_id, chat_id):
        self.player_id = player_id
        self.chat_id = chat_id
        self.game_message_id = None  # сообщение с игровым полем
        self.start_message_id = None  # сообщение с выбором уровня сложности
        self.player_turn = random.choice([True, False])
        self.player_symbol, self.bot_symbol = random.sample(["❌", "⭕️"], k=2)
        self.difficulty = None
        self.game_area = self._create_board()
        self.is_processing = False  # переменная необходимая для правильного чередования ходов бота и игрока

    @staticmethod
    def _create_board():
        game_area = InlineKeyboardMarkup(row_width=3)
        game_area.add(*[
            InlineKeyboardButton("⬜️", callback_data=f"bot_{i}") for i in range(1, 10)
        ])
        return game_area

    @staticmethod
    def get_difficulty_keyboard():
        return InlineKeyboardMarkup(row_width=3).add(
            InlineKeyboardButton("Легкий (1 🪙)", callback_data="difficulty_easy"),
            InlineKeyboardButton("Средний (2 🪙)", callback_data="difficulty_medium"),
            InlineKeyboardButton("Сложный (3 🪙)", callback_data="difficulty_hard"),
            InlineKeyboardButton("Непобедимый (4 🪙)", callback_data="difficulty_impossible")
        )

    def check_winner(self):
        """
        Возвращает:
            - (True, True) - победил игрок
            - (True, False) - победил бот
            - (False, True) - игра продолжается
            - (False, False) - ничья
        """
        board = [button.text for row in self.game_area.inline_keyboard for button in row]

        win_combinations = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]

        # Проверка победы
        for a, b, c in win_combinations:
            if board[a] == board[b] == board[c] != "⬜️":
                return True, board[a] == self.player_symbol

        # Проверка ничьи
        if "⬜️" not in board:
            return False, False  # Ничья
        return False, True  # Игра продолжается

    @staticmethod
    def _check_win(board, symbol):
        """
        метод необходимый для _would_win и _hard_bot_move
        """
        win_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]

        return any(
            all(board[pos] == symbol for pos in combo)
            for combo in win_combinations
        )

    @staticmethod
    def _check_win_result(board):
        """
        метод необходимый для логики minimax в "непобедимой" сложности
        """
        win_combinations = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]

        for a, b, c in win_combinations:
            if board[a] == board[b] == board[c] != "⬜️":
                return board[a]

        return "draw" if "⬜️" not in board else None

    def _would_win(self, board, position, symbol):
        """
        метод необходимый для _medium_bot_move
        """
        temp = board.copy()
        temp[position] = symbol
        return self._check_win(temp, symbol)

    async def make_bot_move(self):
        board = [
            btn.text
            for row in self.game_area.inline_keyboard
            for btn in row
        ]

        if self.difficulty == "easy":
            await self._easy_bot_move()
        elif self.difficulty == "medium":
            await self._medium_bot_move()
        elif self.difficulty == "hard":
            await self._hard_bot_move()
        elif self.difficulty == "impossible":
            await self._impossible_bot_move(board)

    async def _easy_bot_move(self):
        await asyncio.sleep(1)

        available_tiles = [
            (i, button)
            for i, row in enumerate(self.game_area.inline_keyboard)
            for _, button in enumerate(row)
            if button.text == "⬜️"
        ]
        if available_tiles:
            _, button = random.choice(available_tiles)
            button.text = self.bot_symbol

    async def _medium_bot_move(self):
        await asyncio.sleep(1)

        board = [btn.text for row in self.game_area.inline_keyboard for btn in row]

        if board[4] == "⬜️":
            self.game_area.inline_keyboard[1][1].text = self.bot_symbol
            return

        corners = [0, 2, 6, 8]
        empty_corners = [i for i in corners if board[i] == "⬜️"]
        if empty_corners:
            for corner in empty_corners:
                temp_board = board.copy()
                temp_board[corner] = self.bot_symbol
                if sum(1 for i in range(9) if temp_board[i] == "⬜️" and
                self._would_win(temp_board, i, self.bot_symbol)) >= 2:
                    row, col = divmod(corner, 3)
                    self.game_area.inline_keyboard[row][col].text = self.bot_symbol
                    return

            idx = random.choice(empty_corners)
            row, col = divmod(idx, 3)
            self.game_area.inline_keyboard[row][col].text = self.bot_symbol
            return

        await self._easy_bot_move()  # с некоторой долей вероятности может произойти ход на уровень проще

    async def _hard_bot_move(self):
        await asyncio.sleep(1)

        board = [btn.text for row in self.game_area.inline_keyboard for btn in row]

        for i in range(9):
            if board[i] == "⬜️":
                board[i] = self.bot_symbol
                if self._check_win(board, self.bot_symbol):
                    row, col = divmod(i, 3)
                    self.game_area.inline_keyboard[row][col].text = self.bot_symbol
                    return
                board[i] = "⬜️"

        for i in range(9):
            if board[i] == "⬜️":
                board[i] = self.player_symbol
                if self._check_win(board, self.player_symbol):
                    board[i] = self.bot_symbol
                    row, col = divmod(i, 3)
                    self.game_area.inline_keyboard[row][col].text = self.bot_symbol
                    return
                board[i] = "⬜️"

        await self._medium_bot_move()  # с некоторой долей вероятности может произойти ход на уровень проще

    async def _impossible_bot_move(self, board):
        await asyncio.sleep(1)

        if random.random() < 0.1:
            await self._hard_bot_move()  # с некоторой долей вероятности может произойти ход на уровень проще
            return

        best_score = -float('inf')
        best_move = None

        for i in range(9):
            if board[i] == "⬜️":
                board[i] = self.bot_symbol
                score = self._minimax(board, 0, False)
                board[i] = "⬜️"

                if score > best_score:
                    best_score = score
                    best_move = i

        if best_move is not None:
            row, col = divmod(best_move, 3)
            self.game_area.inline_keyboard[row][col].text = self.bot_symbol

    def _minimax(self, board, depth, is_maximizing):
        result = self._check_win_result(board)

        if result == self.bot_symbol:
            return 10 - depth
        elif result == self.player_symbol:
            return depth - 10
        elif result == "draw":
            return 0

        if is_maximizing:
            best_score = -float('inf')
            for i in range(9):
                if board[i] == "⬜️":
                    board[i] = self.bot_symbol
                    score = self._minimax(board, depth + 1, False)
                    board[i] = "⬜️"
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == "⬜️":
                    board[i] = self.player_symbol
                    score = self._minimax(board, depth + 1, True)
                    board[i] = "⬜️"
                    best_score = min(score, best_score)
            return best_score

    def __repr__(self):
        """
        метод для вывода информации для отладки
        """
        return (f"NaCGameBot(player_id={self.player_id}, "
                f"player_turn={self.player_turn}, "
                f"player_symbol='{self.player_symbol}', "
                f"start_message_id='{self.start_message_id}', "
                f"game_message_id='{self.game_message_id}', "
                f"bot_symbol='{self.bot_symbol}', "
                f"difficulty='{self.difficulty}', "
                f"chat_id='{self.chat_id}')")


async def start_game_with_bot(message: types.Message):
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    game = NaCGameBot(user_id, chat_id)
    user_games_bot.setdefault(chat_id, {})[user_id] = game

    sent_message = await message.answer("Выберите уровень сложности:", reply_markup=game.get_difficulty_keyboard())

    game.start_message_id = sent_message.message_id


async def update_game_message(callback: types.CallbackQuery, game: NaCGameBot):
    """
    удобная функция для автоматического обновления текста сообщения "кто сейчас ходит"
    """
    msg = (
            f"👉 {callback.from_user.full_name} - {game.player_symbol}\n      Бот - {game.bot_symbol}"
            if game.player_turn
            else f"      {callback.from_user.full_name} - {game.player_symbol}\n👉 Бот - {game.bot_symbol}"
        )
    return await callback.message.edit_text(
            f"Сейчас ходит:\n{msg}",
            reply_markup=game.game_area,
        )


async def set_difficulty(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    chat_id = str(callback.message.chat.id)

    if chat_id not in user_games_bot or user_id not in user_games_bot[chat_id]:
        await callback.answer("Сначала начните игру!")
        return

    game = user_games_bot[chat_id][user_id]

    if callback.message.message_id != game.start_message_id:
        await callback.answer("Нельзя выбрать данное действие!")  # нельзя нажать на игровое сообщение чужого игрока
        return

    game.difficulty = callback.data.split("_")[1]
    game.is_processing = True

    try:
        sent_message = await update_game_message(callback, game)

        game.game_message_id = sent_message.message_id

        if not game.player_turn:
            await game.make_bot_move()
            game.player_turn = True
            await update_game_message(callback, game)
    except RetryAfter as e:
        await callback.answer(str(e))
        await asyncio.sleep(e.timeout)
        await set_difficulty(callback)
    finally:
        game.is_processing = False


async def process_move_bot(callback: types.CallbackQuery):
    position = int(callback.data.replace("bot_", ""))

    user_id = str(callback.from_user.id)
    chat_id = str(callback.message.chat.id)

    if chat_id not in user_games_bot or user_id not in user_games_bot[chat_id]:
        await callback.answer("Игра не найдена!")  # если последняя игра закончена, а новая не начата
        return

    game = user_games_bot[chat_id][user_id]

    if callback.message.message_id != game.game_message_id:
        await callback.answer("Нельзя ходить на данном поле!")  # нельзя нажать на игровое сообщение чужого игрока
        return

    if not game or game.is_processing or not game.player_turn:
        await callback.answer()  # пустое сообщение, если в момент хода бота нажать на поле
        return

    game.is_processing = True

    try:
        btn_index = position - 1
        row, col = divmod(btn_index, 3)
        btn = game.game_area.inline_keyboard[row][col]

        if btn.text != "⬜️":
            await callback.answer("Клетка уже занята!")
            return

        btn.text = game.player_symbol
        game.player_turn = False
        await update_game_message(callback, game)

        has_winner, is_player = game.check_winner()
        if has_winner:
            await handle_game_over(callback, game, has_winner, is_player)
            return
        elif not is_player:  # Ничья
            await handle_game_over(callback, game, has_winner, is_player)
            return

        await game.make_bot_move()
        game.player_turn = True
        await update_game_message(callback, game)

        has_winner, is_player = game.check_winner()
        if has_winner:
            await handle_game_over(callback, game, has_winner, is_player)
        elif not is_player:  # Ничья
            await handle_game_over(callback, game, has_winner, is_player)
    except RetryAfter as e:
        await callback.answer(str(e))
        await asyncio.sleep(e.timeout)
        await process_move_bot(callback)
    finally:
        game.is_processing = False


async def handle_game_over(callback: types.CallbackQuery, game: NaCGameBot, has_winner:bool, is_player: bool):
    user_id = str(callback.from_user.id)
    chat_id = str(callback.message.chat.id)

    if not has_winner and not is_player:
        result_text = f"Ничья!"
    elif has_winner and is_player:
        result_text = f"Победа!\n{callback.from_user.full_name} {game.player_symbol} выиграл(а)"
    else:
        result_text = f"Поражение!\nБот {game.bot_symbol} выиграл"

    score_update = 0
    if has_winner:
        if game.difficulty == 'easy':
            score_update = 1 if is_player else -1
        elif game.difficulty == 'medium':
            score_update = 2 if is_player else -2
        elif game.difficulty == 'hard':
            score_update = 3 if is_player else -3
        else:
            score_update = 4 if is_player else -4

    # обновляем очки игрока; если сумма получилась меньше 0, то оставляем 0
    cursor.execute(
        "UPDATE users SET score = CASE WHEN score + ? > 0 THEN score + ? ELSE 0 END WHERE id = ?",
        (score_update, score_update, int(user_id))
    )
    db.commit()

    # необходимо для вывода текущего количества очков игрока
    user_score = cursor.execute("SELECT score FROM users WHERE id=?", (int(user_id),)).fetchone()[0]
    # финальный результат доски
    board = "\n".join(
        " ".join(btn.text for btn in row)
        for row in game.game_area.inline_keyboard
    )

    await callback.message.edit_text(
        f"{result_text}\n"
        f"Уровень сложности: {game.difficulty.capitalize()}\n\n"
        f"{board}\n\n"
        f"Ваш новый счет: {user_score} 🪙\n",
    )

    # если в каком-либо чате закончилась текущая игра, то удаляем её из словаря
    if chat_id in user_games_bot and user_id in user_games_bot[chat_id]:
        del user_games_bot[chat_id][user_id]

    # если в каком-либо чате закончились все игры, то удаляем чат из словаря
    if not user_games_bot[chat_id]:
        del user_games_bot[chat_id]
