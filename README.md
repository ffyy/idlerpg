# idlerpg
Dependencies: [discord.py](https://github.com/Rapptz/discord.py/) and [python-dotenv](https://github.com/theskumar/python-dotenv)

This project is a remake of an irc bot I created a decade ago as university coursework in Java. It is intended to familiarize me with python, which I was not familiar with before starting this project. I am trying to avoid using any external libraries other than discord.py as solving various problems by implementing a solution by myself is good practice.

## What even is idlerpg?
In the idlerpg, players (Discord users) can register a character for themselves. The characters are adventuring in a classic AD&D-style fantasy adventure and the bot running the game is a bit of a dick. The players have **no control** over their characters. All actions done by the characters are handled by random pseudo-dice rolls. The goal of the game is for your character to survive and get to the top of the leaderboard by achieving the highest level and gearscore.

## Game rules

Use /rules command in Discord

## Scope
initial scope:
- create character, 2 classes (random & stable) ✔
- level up character by adventuring ✔
- pve ✔
- pvp ✔
- gear & level up gearscore by adventuring ✔

planned improvements after first playtest:
- useful find/whoami command ✔
- ascii tables instead of discord embeds ✔
- rethink how gearscore affects rolls ❌

improvements after the second playtest:
- character statistics ✔
- permadeath ✔
- weekly 'raid' involving all characters in the world

improvements after beta season:
- add warlock (strong but cursed), hunter (weak but need-rolls all gear) classes
- rework cleric
- add death descriptions to graveyard
- allow users to select which columns to show in reports
- tie some sort of progression to character level
- triggered pvp events (fight over gear, group up to gank the top character etc)
- try if encompassing entire adventuring day in one message works better ❌
- randomize order of the events in the day ✔

future scope:
- AI generated quest text & outcomes ❌
- different challenge types
- more classes ✔
- subclasses (better at some challenge type)
- world map
- adventure party, pvp encounters & encounter choice depends on position on world map