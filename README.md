# MiniTranslator_bot
A Telegram translator bot. You can chat directly to this bot or add it to your group chat. The bot will detect user messages and their languages. If the bot is configured to translate language of some message, it will reply to this message with translation.

List of commands:

/start - start the bot in this chat

/help - get basic info about this bot

/add_config - add new source:destination language pair

/rm_config - remove one source:destination language pair

/show_config - show all source:destination language pairs

/all_langs - get a PM with all available languages

/enable - enable bot in this chat

/disable - disable bot in this chat

# How to use
You will need to install Google Translate API version 4.0.1rc1 and pyTelegramBotAPI version 3.8.1.

To use it, you should create a new Telegram bot with @BotFather. Also you should disable private mode with /setprivacy. After that, you should set your bot's token in token.txt file and save it in the same directory. Launch the bot with 'python main.py'. Now you can add your bots to any group and configure what languages it should translate.
