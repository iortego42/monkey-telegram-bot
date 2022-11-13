#!/usr/bin/env python3
import time
from telegram import Update
from os import getenv
from dotenv import load_dotenv, dotenv_values
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext

class DataTimer:
    def __init__(self):
        self.timer = 35 #* 60
        self.time_init = time.monotonic()
        self.dead = None
        self.alert = None

class Bot:
    def __init__(self):
        self.log_out_time = 42 #* 60
        self.timer = {}
        self.messages = dotenv_values("messages_templates.txt")
#        self.locations = {}
#    def delete_monkey()
#    def list_monkeys()
#    def wherearethemonkeys()
#    def add_monkey() -> None:
#        if chat_id not in self.location:
#            self.location[chat_id] = []
#        self.location[chat_id].append()

    async def alarm(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        job = context.job
        log_out_minutes = self.log_out_time - (job.data / 60)
        self.timer[job.chat_id].alert = None
        await context.bot.send_message(job.chat_id, text=f"Ey! You have {log_out_minutes} minutes untill I die\nGive me bananas please")


    async def timeout(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        job = context.job
        self.timer[job.chat_id].dead= None
        await context.bot.send_message(job.chat_id, text=f"Your monkey has died, be carefull next time\n#monkeylifematters")


    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

        chat_id = update.effective_message.chat_id
        if not chat_id:
            return
        if chat_id in self.timer:
            await self.stop(update, context)
        self.timer[chat_id] = DataTimer()
        if context.args and context.args[0].isnumeric() and float(context.args[0]) > 0:
            self.timer[chat_id].timer = float(context.args[0])
#        try:
#            self.timer[chat_id].timer = float(context.args[0]) * 60
#        except (IndexError, ValueError):
#            self.timer[chat_id].timer = 35 * 60
        first_name = update.effective_user.first_name
        self.timer[chat_id].time_init = time.monotonic()
        timer_clock = self.timer[chat_id].time_init - self.timer[chat_id].time_init
        self.timer[chat_id].dead = context.job_queue.run_once(self.timeout, self.log_out_time, chat_id=chat_id, name=str(chat_id))
        self.timer[chat_id].alert = context.job_queue.run_once(self.alarm, self.timer[chat_id].timer, chat_id=chat_id, name=str(chat_id), data=self.timer[chat_id].timer)
        await update.message.reply_text(f'Hello {first_name}, you\'ve started the script.\nTimer: {timer_clock}')


    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_message.chat_id

        if not chat_id in self.timer:
            await update.message.reply_text('ERROR you dont have a monkey, please execute /start')
        elif self.timer[chat_id].time_init != 0:
            timer = time.monotonic() - self.timer[chat_id].time_init
            await update.message.reply_text(f'Timer: {timer}')

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_message.chat_id
        #if self.timer[chat_id].alert and self.timer[chat_id].dead:
        try:
#            if self.timer[chat_id].alert:
                self.timer[chat_id].alert.schedule_removal()
#            if self.timer[chat_id].dead:
                self.timer[chat_id].dead.schedule_removal()
                self.timer.pop(chat_id)
        except (IndexError, AttributeError, KeyError):
            await update.effective_message.reply_text("ERROR\nSorry, you have nothing to stop")

    async def stop_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
        self.timer = {}
        await context.job_queue.stop()







bot = Bot()

load_dotenv()


key = getenv("BOT_TOKEN")
app = ApplicationBuilder().token(key).build()
app.add_handler(CommandHandler(["start", "s"], bot.start))
app.add_handler(CommandHandler(["timerstatus", "ts"], bot.status))
app.add_handler(CommandHandler(["stop", "o"], bot.stop))
app.add_handler(CommandHandler("kill", bot.stop_all))

app.run_polling()
