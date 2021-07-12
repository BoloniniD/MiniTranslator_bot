import pickle
import sys
import os.path
import googletrans
import telebot


class TranslatorBot:
    def __init__(self):
        self.all_langs = str(googletrans.LANGUAGES).replace(', ', '\n').replace("'", "")[1:-1]
        self.configuring = False
        self.deleting = False
        cfg = open('token.txt', 'r')
        try:
            # read the token from cfg file
            token = cfg.readline()
            self.bot = telebot.TeleBot(token, parse_mode=None)

            # read the translator parameters from cfg file
            # "src:dest"
            self.translator = googletrans.Translator()
            self.groups = {}
        except:
            print("Cannot open configs")
            cfg.close()
            sys.exit()
        finally:
            cfg.close()

        if (not os.path.exists("chat_cfg.cfg")):
            file = open("chat_cfg.cfg", "wb") 
            file.close()

        self.loadConfig()

        @self.bot.message_handler(commands=['start'])
        def startBot(message):
            print("Received help message")
            self.bot.reply_to(message, "This bot will translate all user messages in this chat.\nYou can configure which languages need to be translated and what the target language should be with /add_config command.\nUse /help to see other commands.")

        @self.bot.message_handler(commands=['help'])
        def startBot(message):
            print("Received help message")
            self.bot.reply_to(message, '''This bot has the following commands:
/start - starting message
/help - this help page
/add_config - add a langauge pair src:dest, where src - is source language and dest is target language. For src and dest you should use language codes, which can be aquired with /all_langs command.
/all_langs - bot will send you a PM with all supported languages
/rm_config - this command will list all present configuration pairs and will wait a src:dest pair, which will be deleted from config''')
           
        @self.bot.message_handler(commands=['add_config'])
        def addConfigBot(message):
            print("Received add_config message")
            self.configuring = True
            self.bot.reply_to(message, "Choose a source language and destination language.\nNow you can write messages with 'src:dest' to add new translation configs, where src is source language and dest is target language.\nFor example, en:fr.")

        @self.bot.message_handler(commands=['all_langs'])
        def showLangsBot(message):
            print("Received all_langs message")
            self.bot.reply_to(message, "I will send you all supported languages")
            try:
                self.bot.send_message(message.from_user.id, self.all_langs)
            except:
                print("Failed to send the message to used", message.from_user.id)
                self.bot.reply_to(message, "Failed to send you a PM. Please, check if you have blocked the bot.")

        @self.bot.message_handler(commands=['show_config'])
        def showConfigBot(message):
            print("Received show_config message")
            if not message.chat.id in self.groups:
                self.bot.reply_to(message, "No configuration pairs in this chat. Nothing to delete.")
                return
            if not bool(self.groups[message.chat.id]):
                self.bot.reply_to(message, "No configuration pairs in this chat. Nothing to delete.")
                return
            s = ', '.join([':'.join((k, str(self.groups[message.chat.id][k]))) for k in sorted(self.groups[message.chat.id], key=self.groups[message.chat.id]. get, reverse=True)])
            self.bot.reply_to(message, "All configuration pairs: " + s + ".")

        @self.bot.message_handler(commands=['rm_config'])
        def delConfigBot(message):
            print("Received rm_config message")
            if not message.chat.id in self.groups:
                self.bot.reply_to(message, "No configuration pairs in this chat. Nothing to delete.")
                return
            if not bool(self.groups[message.chat.id]):
                self.bot.reply_to(message, "No configuration pairs in this chat. Nothing to delete.")
                return
            self.deleting = True
            s = ', '.join([':'.join((k, str(self.groups[message.chat.id][k]))) for k in sorted(self.groups[message.chat.id], key=self.groups[message.chat.id]. get, reverse=True)])
            self.bot.reply_to(message, "All configuration pairs: " + s + ".\nChoose one and write a message with it. This pair will be removed from config.")

        @self.bot.message_handler(func=lambda message: True)
        def getMessages(message):
            print("New user message")
            if self.configuring:
                print("Received text message while configuring")
                self.addConfigPair(message)
                self.configuring = False
            elif self.deleting:
                print("Received text message while deleting cfg pair")
                self.delConfigPair(message)
                self.deleting = False
            else:
                print("Received text message")
                try:
                    result = self.translator.translate(message.text, dest=self.groups[message.chat.id][self.translator.detect(message.text).lang])
                    self.bot.reply_to(message, result.text)
                    print("Translated the message successfully")
                except:
                    print("Skipping unknown language", self.translator.detect(message.text).lang)

    def addConfigPair(self, message):
        try:
            langs = message.text.split(':')
            langs[0] = langs[0].lower()
            langs[1] = langs[1].lower()
            if not (langs[0] in googletrans.LANGUAGES):
                self.bot.reply_to(message, "Incorrect language " + langs[0])
                return
            if not (langs[1] in googletrans.LANGUAGES):
                self.bot.reply_to(message, "Incorrect language " + langs[1])
                return
            if not message.chat.id in self.groups:
                self.groups[message.chat.id] = {}
            self.groups[message.chat.id][langs[0]] = langs[1]
            self.bot.reply_to(message, "Added new source/target pair.")
            print("Added new src/dest pair")
            self.saveConfig()
        except:
            self.bot.reply_to(message, "String format is incorrect, please try again")
            print("Failed to add new src/dest pair")

    def saveConfig(self):
        print("Trying to save config to file")
        pickle.dump(self.groups, open("chat_cfg.cfg", "wb"))
        print("Saved config to file")

    def loadConfig(self):
        print("Trying to load config from file")
        try:
            self.groups = pickle.load(open("chat_cfg.cfg", "rb"))
            print("Loaded config from file")
        except:
            print("Cannot load or find saved config for chats")

    def delConfigPair(self, message):
        try:
            langs = message.text.split(':')
            self.groups[message.chat.id].pop(langs[0])
            self.bot.reply_to(message, "Removed a source/target pair.")
            print("Removed src/dest pair")
        except:
            self.bot.reply_to(message, "String format is incorrect, please try again")
            print("Failed to remove src/dest pair")
            
    def launchBot(self):
        print("Launching bot...")
        self.bot.polling()

tbot = TranslatorBot()
tbot.launchBot()
