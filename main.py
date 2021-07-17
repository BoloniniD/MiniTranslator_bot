import os.path
import pickle
import sys

import googletrans
import telebot


class TranslatorBot:
    def __init__(self):
        # launching bot
        self.all_langs = (
            str(googletrans.LANGUAGES).replace(", ", "\n").replace("'", "")[1:-1]
        )

        # open bot token file
        cfg = open("token.txt", "r")
        try:
            # read the token from cfg file
            token = cfg.readline()
            self.bot = telebot.TeleBot(token, parse_mode=None)
        except:
            print("Cannot open configs")
            cfg.close()
            sys.exit()
        finally:
            cfg.close()

        # read the translator parameters from cfg file
        # in "src:dest" format
        self.translator = googletrans.Translator()
        self.groups = {}

        # if config is missing, create new one
        if not os.path.exists("cfg/langs_cfg.cfg"):
            file = open("cfg/langs_cfg.cfg", "wb")
            file.close()

        self.enabled = {}

        if not os.path.exists("cfg/enabled_cfg.cfg"):
            file = open("cfg/enabled_cfg.cfg", "wb")
            file.close()

        self.configuring = {}

        if not os.path.exists("cfg/confstate_cfg.cfg"):
            file = open("cfg/confstate_cfg.cfg", "wb")
            file.close()

        self.deleting = {}

        if not os.path.exists("cfg/delstate_cfg.cfg"):
            file = open("cfg/delstate_cfg.cfg", "wb")
            file.close()

        self.loadConfig()

        @self.bot.message_handler(commands=["start"])
        def startBot(message):
            # reply to start command
            print("Received start message")
            self.bot.reply_to(
                message,
                """This bot will translate all user messages in this chat
You can configure which languages need to be translated and what the target language should be with /add_config command
After that you will be able to /enable the bot in this chat
Use /help to see other commands""",
            )

        @self.bot.message_handler(commands=["help"])
        def startBot(message):
            # reply to help command
            print("Received help message")
            self.bot.reply_to(
                message,
                """This bot has the following commands:
/start - starting message
/help - this help page
/add_config - add a langauge pair src:dest, where src - is source language and dest is target language. For src and dest you should use language codes, which can be aquired with /all_langs command
/rm_config - this command will list all present configuration pairs and will wait a src:dest pair, which will be deleted from config
/show_config - list all current configuration pairs
/all_langs - bot will send you a PM with all supported languages
/enable - enable bot in this chat
/disable - disable bot in this chat""",
            )

        @self.bot.message_handler(commands=["add_config"])
        def addConfigBot(message):
            # reply to add_config command
            print("Received add_config message")
            self.configuring[message.chat.id] = True
            self.bot.reply_to(
                message,
                "Choose a source language and destination language.\nNow you can write messages with 'src:dest' to add new translation configs, where src is source language and dest is target language.\nFor example, en:fr.",
            )

        @self.bot.message_handler(commands=["all_langs"])
        def showLangsBot(message):
            # reply to all_langs command
            print("Received all_langs message")
            self.bot.reply_to(message, "I will send you all supported languages")
            try:
                # try to send a PM to user
                self.bot.send_message(message.from_user.id, self.all_langs)
            except:
                # reply to user's message if command fails
                print("Failed to send the message to used", message.from_user.id)
                self.bot.reply_to(
                    message,
                    "Failed to send you a PM. Please, check if you have blocked the bot.",
                )

        @self.bot.message_handler(commands=["show_config"])
        def showConfigBot(message):
            # reply to show_config command
            print("Received show_config message")
            if not message.chat.id in self.groups:
                # bot is new to this group
                self.bot.reply_to(message, "No configuration pairs in this chat.")
                return
            if not bool(self.groups[message.chat.id]):
                # no pairs in a known group
                self.bot.reply_to(message, "No configuration pairs in this chat.")
                return
            s = ", ".join(
                [
                    ":".join((k, str(self.groups[message.chat.id][k])))
                    for k in sorted(
                        self.groups[message.chat.id],
                        key=self.groups[message.chat.id].get,
                        reverse=True,
                    )
                ]
            )
            self.bot.reply_to(message, "All configuration pairs: " + s + ".")

        @self.bot.message_handler(commands=["enable"])
        def enable(message):
            # reply to enable command
            print("Received enable command")
            self.enabled[message.chat.id] = True
            self.bot.reply_to(message, "Bot enabled")

        @self.bot.message_handler(commands=["disable"])
        def disable(message):
            # reply to disable command
            print("Received disable command")
            self.enabled[message.chat.id] = False
            self.bot.reply_to(message, "Bot disabled")

        @self.bot.message_handler(commands=["rm_config"])
        def delConfigBot(message):
            # reply to rm_config command
            print("Received rm_config message")
            if not message.chat.id in self.groups:
                # bot is new to this group
                self.bot.reply_to(
                    message, "No configuration pairs in this chat. Nothing to delete."
                )
                return
            if not bool(self.groups[message.chat.id]):
                # no pairs in a known group
                self.bot.reply_to(
                    message, "No configuration pairs in this chat. Nothing to delete."
                )
                return
            self.deleting[message.chat.id] = True
            s = ", ".join(
                [
                    ":".join((k, str(self.groups[message.chat.id][k])))
                    for k in sorted(
                        self.groups[message.chat.id],
                        key=self.groups[message.chat.id].get,
                        reverse=True,
                    )
                ]
            )
            self.bot.reply_to(
                message,
                "All configuration pairs: "
                + s
                + ".\nChoose one and write a message with it. This pair will be removed from config.",
            )
            self.saveConfig()

        @self.bot.message_handler(func=lambda message: True)
        def getMessages(message):
            print("New user message")
            if not message.chat.id in self.configuring:
                self.configuring[message.chat.id] = False
            if not message.chat.id in self.deleting:
                self.deleting[message.chat.id] = False
            if not message.chat.id in self.enabled:
                self.enabled[message.chat.id] = False
            if self.configuring[message.chat.id]:
                # wait for a new pair after command
                print("Received text message while configuring")
                self.addConfigPair(message)
                self.configuring[message.chat.id] = False
            elif self.deleting[message.chat.id]:
                # wait for pair after command
                print("Received text message while deleting cfg pair")
                self.delConfigPair(message)
                self.deleting[message.chat.id] = False
            elif self.enabled[message.chat.id]:
                # regular message
                print("Received text message")
                try:
                    result = self.translator.translate(
                        message.text,
                        dest=self.groups[message.chat.id][
                            self.translator.detect(message.text).lang
                        ],
                    )
                    self.bot.reply_to(message, result.text)
                    print("Translated the message successfully")
                except:
                    # Do not reply to unknown/unconfigured languages
                    print(
                        "Skipping unknown language",
                        self.translator.detect(message.text).lang,
                    )
            else:
                # Bot's sleeping
                print("Disabled")

    def addConfigPair(self, message):
        try:
            # detect src and dest languages
            langs = message.text.split(":")
            langs[0] = langs[0].lower()
            langs[1] = langs[1].lower()
            # check if googletrans API can translate them
            if not (langs[0] in googletrans.LANGUAGES):
                self.bot.reply_to(message, "Incorrect language " + langs[0])
                return
            if not (langs[1] in googletrans.LANGUAGES):
                self.bot.reply_to(message, "Incorrect language " + langs[1])
                return
            if not message.chat.id in self.groups:
                self.groups[message.chat.id] = {}
            # add a pair to group config
            self.groups[message.chat.id][langs[0]] = langs[1]
            self.bot.reply_to(message, "Added new source/target pair.")
            print("Added new src/dest pair")
            self.saveConfig()
        except:
            self.bot.reply_to(message, "String format is incorrect, please try again")
            print("Failed to add new src/dest pair")

    def saveConfig(self):
        # save all configs to cfg directory
        print("Trying to save config to file")
        pickle.dump(self.groups, open("cfg/langs_cfg.cfg", "wb"))
        pickle.dump(self.enabled, open("cfg/enabled_cfg.cfg", "wb"))
        pickle.dump(self.configuring, open("cfg/confstate_cfg.cfg", "wb"))
        pickle.dump(self.deleting, open("cfg/delstate_cfg.cfg", "wb"))
        print("Saved config to file")

    def loadConfig(self):
        # load all configs from cfg directory
        print("Trying to load config from file")
        try:
            self.groups = pickle.load(open("cfg/langs_cfg.cfg", "rb"))
            self.enabled = pickle.load(open("cfg/enabled_cfg.cfg", "rb"))
            self.configuring = pickle.load(open("cfg/confstate_cfg.cfg", "rb"))
            self.deleting = pickle.load(open("cfg/delstate_cfg.cfg", "rb"))
            print("Loaded config from file")
        except:
            print("Cannot load or find saved config for chats")

    def delConfigPair(self, message):
        try:
            # detect src and dest languages
            langs = message.text.split(":")
            langs[0] = langs[0].lower()
            langs[1] = langs[1].lower()
            # check if we can detete pair from group config
            self.groups[message.chat.id].pop(langs[0])
            self.bot.reply_to(message, "Removed a source/target pair.")
            print("Removed src/dest pair")
        except:
            self.bot.reply_to(message, "String format is incorrect, please try again")
            print("Failed to remove src/dest pair")

    def launchBot(self):
        # start polling
        print("Launching bot...")
        self.bot.polling()


# create an instance
tbot = TranslatorBot()
# launch polling
tbot.launchBot()
