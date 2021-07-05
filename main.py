from game import Game

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from pathlib import Path
import logging
import yaml

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
            return yaml.load(f, Loader=yaml.UnsafeLoader)
    else:
        return Group(chat)


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

    def save(self):
        with getSaveFileName(self).open("w") as f:
            yaml.dump(self, f)


class GuessBot:
    def __init__(self):
        self.groups = []

    def setMinNumRoots(self, update, context):
        """Set the minimum number of roots that a new game will be initialized with."""
        group = self.getGroup(update.effective_chat)
        content = update.message.text
        minNumRoots = self.tryConvertToInt(content.replace("/setMinNumRoots", ""))
        if minNumRoots is not None:
            group.game.minNumRoots = minNumRoots

    def setMaxNumRoots(self, update, context):
        """Set the maximum number of roots that a new game will be initialized with."""
        group = self.getGroup(update.effective_chat)
        content = update.message.text
        maxNumRoots = self.tryConvertToInt(content.replace("/setMaxNumRoots", ""))
        if maxNumRoots is not None:
            group.game.maxNumRoots = maxNumRoots

    def setNumRootsToGuessDownTo(self, update, context):
        """Set the number of remaining roots at which the score for the current polynomial is evaluated"""
        group = self.getGroup(update.effective_chat)
        content = update.message.text
        numRootsToGuessDownTo = self.tryConvertToInt(content.replace("/setNumRootsToGuessDownTo", ""))
        if numRootsToGuessDownTo is not None:
            group.game.numRootsToGuessDownTo = numRootsToGuessDownTo

    def toggleAutoRecap(self, update, context):
        """Toggle whether a recap of all the guessed values is shown after each guess."""
        group = self.getGroup(update.effective_chat)
        content = update.message.text
        group.game.autoRecap = not group.game.autoRecap
        context.bot.send_message(chat_id=group.id, text="Auto-recap set to {}".format(group.game.autoRecap))

    def toggleAutoPlay(self, update, context):
        """Toggle whether obvious guesses (a single empty space between a positive and a negative number) are performed for the current player automatically"""
        group = self.getGroup(update.effective_chat)
        content = update.message.text
        group.game.autoPlay = not group.game.autoPlay
        context.bot.send_message(chat_id=group.id, text="Auto-recap set to {}".format(group.game.autoRecap))

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

    def parseMessage(self, update, context):
        assert update.effective_chat.type == "group"
        group = self.getGroup(update.effective_chat)
        group.save()
        player = group.getPlayer(update.effective_user)
        content = update.message.text
        reply = self.processGuess(group, player, content)
        if reply is not None and reply != "":
            context.bot.send_message(chat_id=group.id, text=reply, parse_mode="markdown")

    def processGuess(self, group, player, content):
        if numGuessSettingIdentifierString in content:
            numGuesses = self.tryConvertToInt(content.replace(numGuessSettingIdentifierString, ""))
            if numGuesses is None:
                return
            group.game.handlePlayerWantsNumGuesses(player, numGuesses)
        else:
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
            ("setMinNumRoots", self.setMinNumRoots),
            ("setMaxNumRoots", self.setMaxNumRoots),
            ("setNumRootsToGuessDownTo", self.setNumRootsToGuessDownTo),
            ("toggleAutoRecap", self.toggleAutoRecap),
            ("toggleAutplay", self.toggleAutoPlay),
            ("recap", self.recap),
            ("roots", self.roots),
            ("showSettings", self.showSettings),
            ("help", self.help),
        ]

        for (name, command) in self.commands:
            dispatcher.add_handler(CommandHandler(name, command))
        dispatcher.add_handler(MessageHandler(Filters.chat_type.groups, self.parseMessage))

        updater.start_polling()
        updater.idle()


bot = GuessBot()
if __name__ == "__main__":
    bot.main()
