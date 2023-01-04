#!/usr/bin/env python3
import time
from telegram import Update
from os import getenv
from dotenv import load_dotenv, dotenv_values
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext
from wherearethemonkeys.wherearethemonkeys import Locator
import sqlite3


conn = sqlite3.connect('wherearethemonkeys.db')

cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER UNIQUE
                                              )""")


cur.execute("""
    CREATE TABLE IF NOT EXISTS friends(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        login TEXT NOT NULL
        )
          """)
conn.commit()
#cur.execute("INSERT INTO users(chat_id) VALUES(?)", (int(121)))









def give_format(list: dict) -> str:
    location = "Here are your friends:\n"
    for user in list:
        if list[user]:
            location += f"""• {user} -> {list[user]}\n"""
    return location

class Location:
    def __init__(self):
        self.cursor = conn.cursor()
        self.logins = {}
        self.locator = Locator()

class DataTimer:
    def __init__(self):
        self.timer = 35 * 60
        self.time_init = time.monotonic()
        self.dead = None
        self.alert = None

class Bot:
    def __init__(self):
        self.location = Location()
        self.log_out_time = 42 * 60
        self.timer = {}
        self.messages = dotenv_values("messages_templates.txt")



    async def help_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(self.messages["HELP_PANEL"])


    def list(self, chat_id):
        self.location.cursor.execute("SELECT id FROM users WHERE chat_id=?", (chat_id,))
        id = self.location.cursor.fetchone()
        users = ""
        if id and id[0]:
            self.location.cursor.execute("SELECT login FROM friends WHERE owner_id=?", (id[0],))
            userslist = self.location.cursor.fetchall()
            for user in userslist:
                users += user[0] + ','
        return users

    async def list_show(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_message.chat_id
        list = self.list(chat_id).split(',')
        userlist = ""
        for element in list[:-1]:
            userlist += "• " + element + '\n'
        if userlist == "":
            await update.effective_message.reply_text("ERROR No friends list")
            return
        await update.effective_message.reply_text(f"""Your friends list:\n{userlist}""")


    async def wherearethemonkeys(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_message.chat_id
        users = self.list(chat_id)
        if not users:
            await update.effective_message.reply_text("ERROR No friends list")
            return
        self.location.locator.set_payload(users_input=users)
        locations = self.location.locator.dict_list()
        await update.effective_message.reply_text(give_format(locations))


    async def add_monkey(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_message.chat_id
        self.location.cursor.execute("SELECT id FROM users WHERE chat_id=?", (chat_id,))
        id = self.location.cursor.fetchone()
        if not id or not id[0]:
            self.location.cursor.execute("INSERT INTO users(chat_id) VALUES(?)", (chat_id,))
            conn.commit()
            self.location.cursor.execute("SELECT id FROM users WHERE chat_id=?", (chat_id,))
            id = self.location.cursor.fetchone()
        if context.args:
            for userlogin in context.args:
                self.location.cursor.executemany("INSERT INTO friends(login, owner_id) VALUES(?, ?)", [(userlogin, id[0])])
            conn.commit()
            await update.effective_message.reply_text("Users added correctly")
            return
        await update.effective_message.reply_text("ERROR Something went wrong")

    async def delete_monkey(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_message.chat_id
        if not context.args:
            await update.effective_message.reply_text("ERROR You need to provide a valid login")
            return

        self.location.cursor.execute("SELECT id FROM users WHERE chat_id=?", (chat_id,))
        id = self.location.cursor.fetchone()
        if not id or not id[0]:
            await update.effective_message.reply_text("ERROR You don't have a friends list")
        for user in context.args:
            self.location.cursor.execute("SELECT login FROM friends WHERE owner_id=? AND login=?", (id[0], user))
            rmuser = self.location.cursor.fetchone()
            if not rmuser:
                await update.effective_message.reply_text("ERROR You need to provide a valid login")
                return
            self.location.cursor.executemany("DELETE FROM friends WHERE owner_id=? AND login=?", [(id[0], user,)])
        conn.commit()
        await update.effective_message.reply_text("User deleted correctly")


    async def alarm(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        job = context.job
        log_out_minutes = self.log_out_time - (job.data / 60)
        self.timer[job.chat_id].alert = None
        await context.bot.send_message(job.chat_id, text=f"Ey! You have {log_out_minutes} minutes untill I die\nGive me bananas please")


    async def timeout(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        job = context.job
        self.timer[job.chat_id].dead = None
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
            if self.timer[chat_id].alert:
                self.timer[chat_id].alert.schedule_removal()
            if self.timer[chat_id].dead:
                self.timer[chat_id].dead.schedule_removal()
            self.timer.pop(chat_id)
        except (IndexError, AttributeError, KeyError):
            await update.effective_message.reply_text("ERROR\nSorry, you have nothing to stop")

    async def stop_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.timer = {}
        await context.job_queue.stop()







load_dotenv()

bot = Bot()
key = getenv("BOT_TOKEN")


app = ApplicationBuilder().token(key).build()

#
#---------- HELP PANEL HANDLER ------------------
#
app.add_handler(CommandHandler(["h", "help"], bot.help_panel))
#
#---------- LOGIN HANDLERS ----------------------
#
app.add_handler(CommandHandler(["start", "s"], bot.start))
app.add_handler(CommandHandler(["timerstatus", "ts"], bot.status))
app.add_handler(CommandHandler(["stop", "o"], bot.stop))
app.add_handler(CommandHandler("kill", bot.stop_all))



#
#---------- WHERE ARE THE MONKEYS HANDLERS ------
#
app.add_handler(CommandHandler(["addmonkey", "a"], bot.add_monkey))
app.add_handler(CommandHandler(["deletemonkey", "d"], bot.delete_monkey))
app.add_handler(CommandHandler(["wherearethemonkeys", "w"], bot.wherearethemonkeys))
app.add_handler(CommandHandler(["list", "ls"], bot.list_show))
#app.add_error_handler()

app.run_polling()

conn.close()
