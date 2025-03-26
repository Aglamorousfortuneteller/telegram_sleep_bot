# 💤 Telegram Sleep Bot

This project is a simple Telegram bot that helps users track and manage their sleep. Users can log their sleep times, rate sleep quality, and add personal notes for each session. The bot also allows viewing past sleep records.

---

## 🚀 Features

- **/sleep** – Log bedtime.
- **/wake** – Log wake-up time and see sleep duration.
- **/quality** – Rate sleep quality (0–10).
- **/notes** – Add notes about your sleep session.
- **/view_records** – View all previous sleep sessions.
- **/view_last_record** – View the most recent sleep session.

---

## 🛠 Installation

To use the bot:

1. **Clone the repository**:

```bash
git clone https://github.com/Aglamorousfortuneteller/telegram_sleep_bot.git
cd telegram_sleep_bot
pip install -r requirements.txt
BOT_TOKEN=your_telegram_bot_token
python main.py


🗂 Files
main.py – Bot logic and command handling

database.py – SQLite database structure and connection

.env – Your secret bot token (not committed)

requirements.txt – Python dependencies

📦 Dependencies
python-dotenv

pyTelegramBotAPI

⚠️ License
This project is for educational and personal use. Contributions are welcome!

You can paste this content directly into a file named `README.md` inside your project folder. Let me know if you also want a `requirements.txt` snippet.