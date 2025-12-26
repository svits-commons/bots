import asyncio
import logging
import sys
import pytz
from os import getenv
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from tortoise import Tortoise
from tortoise.functions import Max

from models import Report
from utils import get_work_days, utcnow

TOKEN = getenv('BOT_TOKEN')
CHAT_ID = getenv('CHAT_ID')
THREAD_ID = getenv('THREAD_ID')

dp = Dispatcher()
bot = Bot(token=TOKEN)

scheduler = AsyncIOScheduler()


async def check_reports():
    users = await Report.annotate(
        created_at=Max('created_at')
    ).group_by('user_id', 'username').values(
        'user_id', 'username', 'created_at'
    )
    logging.info(users)
    now = datetime.now(pytz.UTC)
    ts_now = datetime.now(pytz.UTC).timestamp()
    for user in users:
        # 24 hours = 86400 secs
        if user['created_at'] and now.weekday() < 5 and ts_now - user['created_at'] > 86400:
            await bot.send_message(CHAT_ID, f'@{user["username"]}, you haven\'t sent a report for a while',
                                   message_thread_id=THREAD_ID)


# Command handler
@dp.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    await message.answer(f"{message.chat.id, message.message_thread_id}")


@dp.message()
async def handle_message(message: Message) -> None:
    logging.info(message.text)
    logging.info(message.caption)
    logging.info(message.photo)
    if message.text and '#report' in message.text or message.caption and '#report' in message.caption:
        latest_report = await Report.get_or_none(user_id=message.from_user.id).order_by('created_at').first()
        logging.info(f'Got latest report: {repr(latest_report)}')
        report = await Report.create(user_id=message.from_user.id,
                                     username=message.from_user.username,
                                     created_at=utcnow())
        logging.info(f'Created new report {repr(report)}')
        today = datetime.today()
        start_of_month = today.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        next_month = today.replace(day=28, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=4)
        end_of_month = next_month.replace(day=1) - timedelta(seconds=1)
        days_worked = await Report.filter(
            user_id=message.from_user.id,
            created_at__gte=start_of_month.timestamp(),
            created_at__lte=end_of_month.timestamp()
        ).count()
        work_days = get_work_days(start_of_month, end_of_month)
        await message.answer(f'Good job! {days_worked} of {work_days}')


async def send_monthly_report():
    logging.info('Making monthly report')
    users = await Report.annotate(
        created_at=Max('created_at')
    ).group_by('user_id', 'username').values(
        'user_id', 'username'
    )
    if len(users) == 0:
        return
    logging.info(users)

    message = ''
    today = datetime.today()

    start_of_month = today.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    next_month = today.replace(day=28, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=4)
    end_of_month = next_month.replace(day=1) - timedelta(seconds=1)

    # Work days this month
    work_days = get_work_days(start_of_month, end_of_month)
    for user in users:
        days_worked = await Report.filter(
            user_id=user['user_id'],
            created_at__gte=start_of_month.timestamp(),
            created_at__lte=end_of_month.timestamp()
        ).count()
        message += f'@{user["username"]} — {days_worked}/{work_days}\n'
    logging.info(f'Sending monthly report: {message}')
    await bot.send_message(CHAT_ID, message, message_thread_id=THREAD_ID)


async def on_startup():
    logging.info('Starting up...')

    await Tortoise.init(
        db_url='sqlite://database.db',
        modules={'models': ['models']}
    )
    await Tortoise.generate_schemas()

    scheduler.add_job(
        send_monthly_report,
        'cron',
        day='last',
        hour=23,
        minute=59
    )
    scheduler.add_job(
        check_reports,
        'cron',
        hour=23,
        minute=59,
    )
    scheduler.start()


# Run the bot
async def main() -> None:
    dp.startup.register(on_startup)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
