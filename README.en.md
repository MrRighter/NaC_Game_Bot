# Noughts and Crosses ❌⭕

[![Русский](https://img.shields.io/badge/README-Русский-red?logo=google-translate)](README.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

### This is a simple bot on Aiogram for fun and a little programming practice 👨‍💻

You can play with the Bot, which has 4 difficulty levels: from easy to impossible. All results are stored in the `sqlite3` database. The bot can also be added to a group, where it organizes game battles between willing participants.

---

## How to play and what commands are available 🎮
There are two main commands to play the game: `/game_with_bot` and `/game_with_friend`. The first one works without arguments - send it and the game starts. However, using the second command you need to specify your opponent with a space. For example, `/game_with_friend @Vasya_Pupkin` if there is **@username**, and `/game_with_friend Vasya Pupkin` if there is no **@username**.

> [!Note]  
> In any case you should start specifying your opponent with `@`. Telegram itself will substitute the necessary value when you select and click on a person from the drop-down list.

By itself there is a basic `/start` function, which you can customize as you like. It's split into two different messages: one for ls and one for group.
An important function is `/leaderbord` to display the top of the list. Also you can select any number of places. For convenience, at the very bottom of this message the information about the current user is displayed to make it easier to find yourself.

---

## Using ⚙️
Install the required libraries   
```
pip install -r requirements.txt
```
After that you need to create a database by running the `create_db.py` file. Then write your bot token in `.env`. Finally you can run the `main.py` file and play at your pleasure)

---

## FIXIT 👾
I can assume that this small project has its flaws and illogical lines of code that could be reduced and optimized. I would be very happy to see suggestions for improvement, if there are any.
