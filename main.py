from game import Game
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def findById(objectWithId, listOfObjects, constructor):
    for obj in listOfObjects:
        if objectWithId.id == obj.id:
            return obj
    return constructor(objectWithId)
    
class Player:
    def __init__(self, user):
        self.id = user.id
        self.name = user.first_name

    def __repr__(self):
        return self.name

class Group:
    def __init__(self, chat):
        self.id = chat.id
        self.numMembers = chat.get_members_count()
        self.players = []

    def getPlayer(self, user):
        player = findById(user, self.players, Player)
        if player not in self.players:
            self.addPlayer(player)
        return player

    def addPlayer(self, player):
        logger.info("Registering new player {}".format(player))
        self.players.append(player)
        self.game = Game(self.players[:])

class GuessBot:
    def __init__(self):
        self.groups = []

    def setNumRoots(self, bot, update):
        group = self.getGroup(update.effective_chat)
        content = update.message.text
        numRoots = self.tryConvertToInt(content.replace("/setNumRoots", ""))
        if numRoots is not None:
            group.game.numRoots = numRoots
        
    def resetScore(self, bot, update):
        group = self.getGroup(update.effective_chat)
        group.game.resetScore()
        bot.send_message(chat_id=group.id, text=group.game.log.dump())

    def startNewGame(self, bot, update):
        group = self.getGroup(update.effective_chat)
        group.game.reset()
        bot.send_message(chat_id=group.id, text=group.game.log.dump())
        
    def parseMessage(self, bot, update):
        assert update.effective_chat.type == "group"
        group = self.getGroup(update.effective_chat)
        player = group.getPlayer(update.effective_user)
        content = update.message.text
        reply = self.processGuess(group, player, content)
        if reply is not None and reply != "":
            bot.send_message(chat_id=group.id, text=reply)

    def processGuess(self, group, player, content):
        guessedNumber = self.tryConvertToInt(content)
        if guessedNumber is None:
            return
        group.game.handlePlayerGuess(player, guessedNumber)
        return group.game.log.dump()

    def tryConvertToInt(self, content):
        try:
            return int(content)
        except (ValueError, TypeError) as e:
            return None

    def getGroup(self, chat):
        group = findById(chat, self.groups, Group)
        if group not in self.groups:
            logger.info("Registering new group {}".format(group))
            self.groups.append(group)
        return group

    def error(self, bot, update, error):
        logger.warning('Update "%s" caused error "%s"', update, error)

    def main(self):
        with open("apiToken", "r") as f:
            token = f.readlines()[0].replace("\n", "")
        updater = Updater(token)

        dispatcher = updater.dispatcher
        dispatcher.add_error_handler(self.error)
        dispatcher.add_handler(CommandHandler("startNewGame", self.startNewGame))
        dispatcher.add_handler(CommandHandler("resetScore", self.resetScore))
        dispatcher.add_handler(CommandHandler("setNumRoots", self.setNumRoots))
        dispatcher.add_handler(MessageHandler(Filters.group, self.parseMessage))

        updater.start_polling()
        updater.idle()


bot = GuessBot()
if __name__ == '__main__':
    bot.main()
