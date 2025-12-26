import sys
import os
import logging
import asyncio

import requests
import sqlite3

from aiogram import Dispatcher, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

dp = Dispatcher()
bot = Bot(token=os.environ.get('TOKEN'))
chat_id = os.environ.get('CHAT_ID')
thread_id = os.environ.get('THREAD_ID')

if chat_id is None or thread_id is None:
    logging.warning(
        'Take chat id and thread id from /start command and provide them in environment variables CHAT_ID and ' +
        'THREAD_ID respectively'
    )


async def ping():
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('SELECT id, url, failed FROM hosts')
    hosts = cur.fetchall()
    logging.info(f'fetched {len(hosts)}')
    for host in hosts:
        arguments = {'chat_id': chat_id}
        if thread_id is not None and thread_id != '':
            arguments['message_thread_id'] = thread_id
        logging.info(f'Arguments: {arguments}')
        try:
            req = requests.get(host[1])
        except Exception as e:
            if not host[2]:
                cur.execute('UPDATE hosts SET failed = ? WHERE id = ?', (1, host[0]))
                logging.info(f'updated {host[1]}')
                await bot.send_message(
                    **arguments,
                    text=f'🔴 service {host[1]} is unavailable'
                )
            con.commit()
            continue
        if not req.ok and not host[2]:
            cur.execute('UPDATE hosts SET failed = ? WHERE id = ?', (1, host[0]))
            logging.info(f'updated {host[1]}')
            await bot.send_message(
                **arguments,
                text=f'🔴 service {host[1]} is unavailable'
            )
        elif req.ok and host[2]:
            cur.execute('UPDATE hosts SET failed = ? WHERE id = ?', (0, host[0]))
            logging.info(f'updated {host[1]}')
            await bot.send_message(
                **arguments,
                text=f'🔵 service {host[1]} is now available'
            )
        con.commit()
    con.close()


@dp.message(Command('start'))
async def start(message: Message):
    await message.answer(f"Chat id and thread id:\n{message.chat.id, message.message_thread_id}")


@dp.message(Command('add'))
async def add_host(message: Message):
    url = message.text[4:].strip()
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('''INSERT INTO hosts (url) VALUES (?)''', (url,))
    con.commit()
    con.close()
    logging.info(f'added {url}')
    await message.reply(f'Host {url} has been added to the list')


@dp.message(Command('remove'))
async def remove_host(message: Message):
    url = message.text[7:].strip()
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('SELECT * FROM hosts WHERE url = ?', (url,))
    host = cur.fetchone()
    if host is None:
        await message.reply(f'Host {url} does not exist')
        con.close()
        return
    cur.execute('''DELETE FROM hosts WHERE url = ?''', (url,))
    con.commit()
    con.close()
    logging.info(f'removed {url}')
    await message.reply(f'Host {url} has been removed')


@dp.message(Command('list'))
async def get_hosts(message: Message):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('SELECT id, url, failed FROM hosts')
    hosts = cur.fetchall()
    logging.info(f'fetched {len(hosts)} hosts')
    con.commit()
    con.close()
    text = 'Hosts:\n'
    for host in hosts:
        text += f' - {host[1]} {"failed 🔴" if host[2] else ""}\n'
    await message.reply(text)


async def main():
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS hosts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT,
        failed INTEGER DEFAULT 0
    )''')
    con.commit()
    con.close()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(ping, 'interval', seconds=10)
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
