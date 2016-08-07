 #!/usr/bin/python
 # -*- coding: utf-8 -*-

import telegram
from telegram import Bot
from telegram.ext import Updater, CommandHandler, RegexHandler
import logging
import os.path
from os import chdir
import cPickle as pickle
from strelka_user import StrelkaUser

from credentials import ADMIN_ID, TELEGRAM_TOKEN

class StrelkaBot(object):
    def __init__(self):
        if os.path.isfile('STRELKA_DB.dump') :
            print 'Resoring old'
            self.strelka_db = pickle.load(open('STRELKA_DB.dump'))
        else:
            print 'Creating new'
            self.strelka_db = {}
            
        # Telegram Bot Authorization Token
        self.bot = Bot(TELEGRAM_TOKEN)

    def start(self, bot, update):
        from_id   = update.message.chat.id
        from_name = update.message.chat.first_name
        # Insert into database
        self.strelka_db[from_id] = StrelkaUser(from_id)
        # Work with it
        answer = u'''Привет, %s! Я — робот карты Стрелка. Меня сделал @feriat, и я умею проверять баланс карты «Стрелка».
Напиши мне, пожалуйста, 10-значный номер твоей карты, и я смогу проверять твой баланс.''' % from_name
        reply_markup = telegram.ReplyKeyboardHide()
        bot.sendMessage(
            chat_id=from_id,
            text=answer,
            reply_markup=reply_markup
        )
    
    def process_admin_update(self, bot, update):
        chat_id = update.message.chat_id

        if ('/admin quit' in update.message.text or '/admin stop' in update.message.text) :
            if chat_id == ADMIN_ID:
                answer = 'Stopping service'
                bot.sendMessage(chat_id=chat_id, text=answer)
                print 'Stopping'
                self.updater.stop()
            else:
                answer = u'Прости, ты не мой босс :-(. Обратись к @feriat!'
                answer = answer.encode('utf-8')
                self.bot.sendMessage(chat_id=chat_id, text=answer)

        if '/admin kill all' in update.message.text:
            if chat_id == ADMIN_ID:
                answer = 'Killing DB service'
                self.bot.sendMessage(chat_id=chat_id, text=answer)
                print 'Killing self.strelka_db = {}'
                self.strelka_db = {}
            else:
                answer = u'Прости, ты не мой босс :-(. Обратись к @feriat!'
                answer = answer.encode('utf-8')
                self.bot.sendMessage(chat_id=chat_id, text=answer)


        if (u'/forget_me' in update.message.text):
            answer = u'Твой аккаунт удален!'
            answer = answer.encode('utf-8')
            self.bot.sendMessage(chat_id=chat_id, text=answer)
            _ = self.strelka_db.pop( update.message.chat_id  , None)
            pickle.dump(self.strelka_db, open('STRELKA_DB.dump', 'wb') )


    def process_card_number(self, bot, update):
        from_id   = update.message.chat.id
        from_name = update.message.chat.first_name
        if from_id not in self.strelka_db:
            self.strelka_db[from_id] = StrelkaUser(from_id)
        strelka_user = self.strelka_db[from_id]

        # Some initial number preparation
        try:
            message = update.message.text
            card_num = long( message.replace(' ', '').replace('-','').strip() )
        except:
            answer = u'В номере карты допущена ошибка. Проверь его, пожалуйста!'
            reply_markup = telegram.ReplyKeyboardHide()
            self.bot.sendMessage(chat_id=from_id,
                                text=answer,
                                reply_markup=reply_markup)
            return

        # Real check of card number
        if strelka_user.is_valid_number( card_num ):
            strelka_user.update_number( card_num )
            answer = (
                u'%s, я запомнил номер твоей карты. Теперь можешь использовать команду /strelka, '
                u'чтобы проверять баланс! Если ты захочешь удалить этот номер, используй '
                u'команду /forget_me.' % from_name
            )
            reply_markup = self._get_reply_markup(from_id)
            self.bot.sendMessage(chat_id=from_id,
                            text=answer,
                            reply_markup=reply_markup )
            pickle.dump(self.strelka_db, open('STRELKA_DB.dump', 'wb') )

        else:
            answer = u'С полученным сообщением что-то не так. Отправь номер карты ещё раз, пожалуйста!'
            reply_markup = telegram.ReplyKeyboardHide()
            self.bot.sendMessage(chat_id=from_id,
                                text=answer,
                                reply_markup=reply_markup)

    def process_strelka_update(self, bot, update):
        from_id   = update.message.chat_id
        from_name = update.message.chat.first_name
        if from_id not in self.strelka_db:
            self.strelka_db[from_id] = StrelkaUser(from_id)

        strelka_user = self.strelka_db[from_id]
        if not strelka_user.has_strelka_number():
            # New user without card number
            answer = (
                u'У меня нет твоего номера карты!'
                u'Жду 10-значный номер твоей карты'
            )
            reply_markup = telegram.ReplyKeyboardHide()
            self.bot.sendMessage(chat_id=from_id,
                                text=answer,
                                reply_markup=reply_markup)
        else:
            # Known user with card number
            self.bot.sendChatAction(action = 'typing', chat_id = from_id )
            balance = strelka_user.get_updated_balance()
            answer = u'%s, баланс твоей карты Стрелка %.2f₽!'%(from_name, balance)
            reply_markup = self._get_reply_markup(from_id)
            self.bot.sendMessage(chat_id=from_id,
                            text=answer,
                            reply_markup=reply_markup )
    
    @staticmethod
    def _get_reply_markup(chat_id):
        if chat_id == ADMIN_ID: 
            custom_keyboard = [[ "/strelka" ], ["/forget_me", '/admin kill all'] ]
        else: 
            custom_keyboard = [[ "/strelka" ], ["/forget_me"] ]

        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)

        return reply_markup

    def run(self):
        # Create the EventHandler and pass it your bot's token.
    
        # updater = Updater(TELEGRAM_TOKEN, workers=5) 
        updater = Updater(TELEGRAM_TOKEN)
        self.updater = updater

        # Get the dispatcher to register handlers
        dp = updater.dispatcher

        # dp.add_handler(Handler(self.process_strelka_update))
        dp.add_handler(CommandHandler('start', self.start))
        dp.add_handler(CommandHandler('admin', self.process_admin_update))
        dp.add_handler(CommandHandler('forget_me', self.process_admin_update))
        dp.add_handler(RegexHandler(r'^[0-9 -]{10,}$', self.process_card_number))
        dp.add_handler(CommandHandler('strelka', self.process_strelka_update))


        # log all errors
        # dp.add_error_handler(error) 

        # Start the Bot
        updater.start_polling()

        # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()


def main():
    chdir('/root/FeriatBot/')

    bt = StrelkaBot()
    bt.run()


if __name__ == '__main__':
    # Enable logging
    logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO)

    # fuck off InsecurePlatformWarning
    import urllib3
    urllib3.disable_warnings()

    main()
