from game import Game

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from pathlib import Path
import logging
import yaml
from util import tryConvertToInt
from gameSettings import GameSettings

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)

saveFolder = "save"

numGuessSettingIdentifierString = "#"


def findById(objectWithId, listOfObjects, constructor):
    for obj in listOfObjects:
        if objectWithId.id == obj.id:
            return obj
    return constructor(objectWithId)


def getNewGroup(chat):
    saveFile = getSaveFileName(chat)
    if saveFile.is_file():
        with saveFile.open("r") as f:
            result = yaml.load(f, Loader=yaml.UnsafeLoader)
            if result is None:
                return None
            print("Found group in save file", result)
            return Group(*result)
    else:
        return Group(chat.id)


def getSaveFileName(group):
    path = Path(saveFolder, str(group.id))
    if not path.is_file():
        path.parent.mkdir(exist_ok=True)
    return path


class Player:
    def __init__(self, user):
        self.id = user.id
        self.name = user.first_name

    def __repr__(self):
        return self.name


class Group:
    def __init__(self, _id, players=None, settings=None):
        self.id = _id
        if players is None:
            self.players = []
            self.game = None
        else:
            self.players = players
            if settings is not None:
                # Make sure we update the settings instead of using
                # the one we read, in case the save file used a
                # previous version of the settings class in which some
                # parameters were not available
                settings = GameSettings().update(settings)
            self.game = Game(players, settings)

    def getPlayer(self, user):
        player = findById(user, self.players, Player)
        if player not in self.players:
            self.addPlayer(player)
        return player

    def addPlayer(self, player):
        logger.info("Registering new player {}".format(player))
        self.players.append(player)
        previousSettings = None if self.game is None else self.game.settings
        self.game = Game(self.players[:], previousSettings)

    def save(self):
        with getSaveFileName(self).open("w") as f:
            if self.game is not None:
                yaml.dump([self.id, self.players, self.game.settings], f)


class GuessBot:
    def __init__(self):
        self.groups = []

    def recap(self, update, context):
        """Show all the guessed values in this current game"""
        group = self.getGroup(update.effective_chat)
        group.game.recap()
        context.bot.send_message(chat_id=group.id, text=group.game.log.dump(), parse_mode="markdown")

    def roots(self, update, context):
        """Show the number of guessed roots in this game for each player."""
        group = self.getGroup(update.effective_chat)
        group.game.playerRecap()
        context.bot.send_message(chat_id=group.id, text=group.game.log.dump())

    def showScore(self, update, context):
        """Show the current score"""
        group = self.getGroup(update.effective_chat)
        group.game.showScore()
        context.bot.send_message(chat_id=group.id, text=group.game.log.dump())

    def startNewGame(self, update, context):
        """Start a new game."""
        group = self.getGroup(update.effective_chat)
        group.game.resetFunction()
        context.bot.send_message(chat_id=group.id, text=group.game.log.dump())

    def showSettings(self, update, context):
        """Display all settings"""
        group = self.getGroup(update.effective_chat)
        content = group.game.dumpSettings()
        context.bot.send_message(chat_id=group.id, text=f"```\n{content}```", parse_mode="markdown")

    def serve(self, update, context):
        """Show whose turn it is to serve."""
        group = self.getGroup(update.effective_chat)
        response = "Serve: {}".format(group.game.getStartingPlayerName())
        context.bot.send_message(chat_id=group.id, text=response, parse_mode="markdown")



    def setParam(self, update, context):
        """Set game parameters"""
        group = self.getGroup(update.effective_chat)
        content = update.message.text
        paramNameValueString = content.replace("/set ", "")
        paramNameValue = paramNameValueString.split(" ")
        if len(paramNameValue) == 2:
            response = group.game.settings.set(*paramNameValue)
        else:
            response = group.game.settings.showHelp()
        group.save()
        context.bot.send_message(chat_id=group.id, text=f"```\n{response}```", parse_mode="markdown")

    def parseMessage(self, update, context):
        assert update.effective_chat.type == "group"
        group = self.getGroup(update.effective_chat)
        player = group.getPlayer(update.effective_user)
        content = update.message.text
        reply = self.processGuess(group, player, content)
        if reply is not None and reply != "":
            context.bot.send_message(chat_id=group.id, text=reply, parse_mode="markdown")
        group.save()

    def processGuess(self, group, player, content):
        if numGuessSettingIdentifierString in content:
            numGuesses = tryConvertToInt(content.replace(numGuessSettingIdentifierString, ""))
            if numGuesses is None:
                return
            group.game.handlePlayerWantsNumGuesses(player, numGuesses)
        else:
            guessedNumber = tryConvertToInt(content)
            if guessedNumber is None:
                return
            group.game.handlePlayerGuess(player, guessedNumber)
        return group.game.log.dump()

    def getGroup(self, chat):
        group = findById(chat, self.groups, getNewGroup)
        if group not in self.groups:
            logger.info("Registering new group {}".format(group))
            self.groups.append(group)
        return group

    def error(self, update, context):
        logger.warning('Update "%s" caused error "%s"', update, context.error)

    def help(self, update, context):
        """You already know what this does."""
        group = self.getGroup(update.effective_chat)
        content = "\n".join("/{}: {}".format(name, command.__doc__) for (name, command) in self.commands)
        context.bot.send_message(chat_id=group.id, text=content)

    def main(self):
        with open("apiToken", "r") as f:
            token = f.readlines()[0].replace("\n", "")
        updater = Updater(token)

        dispatcher = updater.dispatcher
        dispatcher.add_error_handler(self.error)
        self.commands = [
            ("startNewGame", self.startNewGame),
            ("score", self.showScore),
            ("recap", self.recap),
            ("roots", self.roots),
            ("showSettings", self.showSettings),
            ("help", self.help),
            ("serve", self.serve),
            ("set", self.setParam),
        ]

        for (name, command) in self.commands:
            dispatcher.add_handler(CommandHandler(name, command))
        dispatcher.add_handler(MessageHandler(Filters.chat_type.groups, self.parseMessage))

        updater.start_polling()
        updater.idle()


bot = GuessBot()
if __name__ == "__main__":
    bot.main()
