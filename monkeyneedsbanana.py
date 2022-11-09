#!/usr/bin/env python3
import time
from telegram import Update
from os import getenv
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext


class Bot:
    def __init__(self):
        self.log_out_time = 42
        self.timer = 35
        self.time_init = {}
        self.dead = None
        self.alert = None

    async def alarm(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        job = context.job
        await context.bot.send_message(job.chat_id, text=f"Ey! You have {self.log_out_time - (job.data / 60)} minutes untill I die\nGive me bananas please")


    async def timeout(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        job = context.job
        await context.bot.send_message(job.chat_id, text=f"Your monkey has died, be carefull next time\n#monkeylifematters")


    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

        chat_id = update.effective_message.chat_id
        self.time_init[chat_id] = time.monotonic()
        self.dead = context.job_queue.run_once(self.timeout, self.log_out_time, chat_id=chat_id, name=str(chat_id))
        self.alert = context.job_queue.run_once(self.alarm, self.timer, chat_id=chat_id, name=str(chat_id), data=self.timer)
        await update.message.reply_text(f'Hello {update.effective_user.first_name}, you start the script.\nTimer: {self.time_init[chat_id]}')


    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_message.chat_id
 

        if chat_id in self.time_init and self.time_init[chat_id] != 0:
            timer = time.monotonic() - self.time_init[chat_id]
            await update.message.reply_text(f'Timer: {timer}')
        else:
            self.time_init[chat_id] = time.monotonic()
            await update.message.reply_text(f'Initialiting time\nTimer: 0')


    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if self.alert and self.dead:
            self.alert.schedule_removal()
            self.dead.schedule_removal()

    async def stop_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
        await context.job_queue.stop()





bot = Bot()

load_dotenv()


key = getenv("BOT_TOKEN")
app = ApplicationBuilder().token(key).build()
app.add_handler(CommandHandler("start", bot.start))
app.add_handler(CommandHandler("timerstatus", bot.status))
app.add_handler(CommandHandler("stop", bot.stop))
app.add_handler(CommandHandler("kill", bot.stop_all))

app.run_polling()
