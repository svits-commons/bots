import re
import asyncio
import sqlite3
import logging
import sys
from datetime import datetime
from telethon import TelegramClient

api_id = int(input("Telegram API ID: "))
api_hash = input("Telegram API hash: ")
chat_id = int(input("Telegram Chat ID: "))
chat_thread_id = int(input("Telegram Chat Thread ID: "))

# --- 2. Create the client and connect ---
client = TelegramClient('session_name', api_id, api_hash)

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def fetch_reports():

    now = datetime.now()
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    hashtag = '#report'
    print(f"Fetching messages from {first_of_month.isoformat()} onward containing '{hashtag}'…\n")
    con = sqlite3.connect('database.db')
    cursor = con.cursor()

    async for message in client.iter_messages(
            entity=chat_id,
            reverse=True,
            offset_date=first_of_month,
            limit=None
    ):
        text = message.message or ""
        thread_id = getattr(message.reply_to, 'reply_to_msg_id', None)

        if thread_id == chat_thread_id and hashtag in text:
            user = await message.get_sender()
            regex = re.compile(
                r'(\b\d{1,4}\.\d{1,4}\.\d{1,4}\b\s*#report)|(#report\s*\b\d{1,4}\.\d{1,4}\.\d{1,4}\b)',
                re.IGNORECASE)
            is_match = regex.search(text)
            if not is_match:
                continue

            date_match = re.search(r'\d{1,4}\.\d{1,4}\.\d{1,4}', is_match.group(0))
            if not date_match:
                continue
            date = date_match.group(0)
            if len(date_match.group(0).split('.')[-1]) == 2:
                date = f"{date_match.group(0).split('.')[0]}.{date_match.group(0).split('.')[1]}.20{date_match.group(0).split('.')[2]}"

            date_timestamp = datetime.strptime(date, '%d.%m.%Y').timestamp()
            logging.info(f'Adding: {(user.id, user.username, date_timestamp)} to database')
            cursor.execute('''INSERT INTO report (user_id, username, created_at)
SELECT ?, ?, ?
WHERE NOT EXISTS (
    SELECT 1 FROM report
    WHERE user_id = ? AND username = ? AND created_at = ?
);''',
                           [user.id, user.username, date_timestamp, user.id, user.username, date_timestamp])
            con.commit()
    con.close()


async def main():
    await client.start()
    await fetch_reports()
    await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
