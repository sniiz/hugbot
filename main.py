import discord
import cv2
import requests
import os
import json
import asyncio
import random
import time

bot = discord.Client(intents=discord.Intents.all())  # bad idea probably
prefix = "hb."

path = "/home/sniiz/code/hugbot/"  # change this to your path to the repo folder


def log(x):
    print(f"[HB {time.time()}] {x}")
    open(f"{path}log.txt", "a").write(f"[HB {time.time()}] {x}\n")


hugs = 0

hugTargetChannel = 1068261928604024852
hugTargetServer = 1036940104536703036

recentAutoHugs = {}

with open(f"{path}hug.log", "r") as f:
    hugs = int(f.read())

hfToken = open(f"{path}hftoken.txt", "r").read()


def sentiment(text):
    url = "https://api-inference.huggingface.co/models/cardiffnlp/twitter-roberta-base-sentiment-latest"
    headers = {"Authorization": f"Bearer {hfToken}"}
    res = requests.post(url, headers=headers, json={"inputs": text})
    log(res.json())
    if res.status_code != 200:
        return "error", 0
    return res.json()[0][0]["label"], res.json()[0][0]["score"]


@bot.event
async def on_ready():
    log("hugger online")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{hugs} hugs given! | {prefix}help",
        )
    )


@bot.event
async def on_message(message: discord.Message):
    global hugs
    global recentAutoHugs

    global command
    command = "NONE"

    if not message.content.startswith(prefix):
        autoHugBlacklist = open(f"{path}donthug.log", "r").read().splitlines()
        if str(message.author.id) in autoHugBlacklist:
            return
        if message.author.bot:
            return
        if random.randint(0, 10) > 5:
            return
        if (
            message.author.id in recentAutoHugs
            and time.time() - recentAutoHugs[message.author.id] < 600
        ):
            return
        messageSentiment, score = sentiment(message.clean_content)
        threshold = 0.93
        if messageSentiment == "negative" and score > threshold:
            await message.reply(f"hb.hug {message.author.mention}")
            recentAutoHugs[message.author.id] = time.time()
            return
    else:
        command = message.clean_content.split()[0].replace(prefix, "")

    if command == "hug":
        session = message.id
        mainGif = False

        log("getting author avatar")
        url = message.author.display_avatar.url

        mainGif = url.endswith(".gif")

        url = str(url).replace("webp", "png")
        name = f"{path}{session}A.png"

        with open(name, "wb") as f:
            f.write(requests.get(url).content)

        if mainGif:
            authorPic = cv2.VideoCapture(name)
            authorPic.set(cv2.CAP_PROP_POS_FRAMES, 0)
            authorPic.read()
        else:
            authorPic = cv2.imread(name)

        log("getting target avatar")

        test = False
        delete = True

        if "TESTUSER" in message.content:
            target = bot.user
            test = True
        elif message.mentions:
            target = message.mentions[0]
            if target.id == bot.user.id:
                await message.reply(
                    "unfortunately, you can't hug me. i am a bot, after all :("
                )
                return
            if target.bot:
                await message.reply("sadly bots can't accept hugs :(")
                return
        else:
            await message.reply("mention someone to hug them!")
            return

        if "-nd" in message.content:
            delete = False

        messageText = (
            message.content.replace(f"{prefix}hug", "")
            .replace("TESTUSER", "")
            .replace("-nd", "")
            .strip()
            .split()
        )

        if messageText:
            messageText = filter(lambda x: not x.startswith("<@"), messageText)
            messageText = " ".join(messageText)

        if target.id == message.author.id:
            await message.reply(
                "you can't hug yourself on discord, but you can do it in real life! actually, go do it now :D"
            )
            return

        url = target.display_avatar.url

        mainGif = url.endswith(".gif")

        url = str(url).replace("webp", "png")
        name = f"{path}{session}T.png"

        with open(name, "wb") as f:
            f.write(requests.get(url).content)

        if mainGif:
            targetPic = cv2.VideoCapture(name)
            targetPic.set(cv2.CAP_PROP_POS_FRAMES, 0)
            targetPic.read()
        else:
            targetPic = cv2.imread(name)

        log("creating background")
        background = cv2.imread(f"{path}assets/pre.png")
        [bgH, bgW, bgC] = background.shape

        authorPic = cv2.resize(authorPic, (300, 300))

        offsetY = 180
        background[
            bgH // 2 - offsetY - 150 : bgH // 2 - offsetY + 150,
            bgW // 2 - 150 : bgW // 2 + 150,
        ] = authorPic

        if messageText:
            font = cv2.FONT_HERSHEY_SIMPLEX
            # TODO: custom font
            fontScale = 1.5
            fontColor = (0, 0, 0)
            lineType = 5

            textSize = cv2.getTextSize(messageText, font, fontScale, lineType)[0]

            textX = (bgW - textSize[0]) // 2
            textY = bgH // 2 - offsetY - 210

            cv2.putText(
                background,
                messageText,
                (textX, textY),
                font,
                fontScale,
                fontColor,
                lineType,
            )

        cv2.imwrite(f"{path}{session}R.png", background)

        log("sending")

        channel = message.channel
        guildId = message.guild.id if message.guild else 0
        if guildId == hugTargetServer:
            if not message.channel.id == hugTargetChannel and not message.author.bot:
                smileys = [
                    ":)",
                    ":D",
                    "<3",
                    "^^",
                    "c:",
                ]
                await message.reply(f"<#{hugTargetChannel}> {random.choice(smileys)}")
            channel = bot.get_channel(hugTargetChannel)

        botReply = await channel.send(
            f"<@{message.author.id}> offers a hug to <@{target.id}>! {target.display_name}, react with 🫂 to accept!",
            file=discord.File(f"{path}{session}R.png", filename="hug.png"),
        )

        os.remove(f"{path}{session}R.png")

        await botReply.add_reaction("🫂")

        def check(reaction, user):
            return user == target and str(reaction.emoji) == "🫂"

        if test:
            await asyncio.sleep(5)
        else:
            try:
                reaction, user = await bot.wait_for(
                    "reaction_add", timeout=1200.0, check=check
                )
            except:
                await botReply.edit(
                    content=f"<@{target.id}> didn't accept {message.author.display_name}'{'' if message.author.display_name[-1] == 's' else 's'} hug in time! :'(",
                    attachments=[],
                )
                os.remove(f"{path}{session}A.png")
                os.remove(f"{path}{session}T.png")
                await botReply.remove_reaction("🫂", bot.user)
                return

        log("accepted")
        await botReply.remove_reaction("🫂", bot.user)

        background = cv2.imread(f"{path}assets/hug.png")

        targetPic = cv2.resize(targetPic, (280, 280))

        authorPic = cv2.resize(authorPic, (280, 280))

        offsetXY = [-100, 130]
        background[
            bgH // 2 - offsetXY[1] - 140 : bgH // 2 - offsetXY[1] + 140,
            bgW // 2 + offsetXY[0] - 140 : bgW // 2 + offsetXY[0] + 140,
        ] = authorPic

        offsetXY = [100, 100]
        background[
            bgH // 2 - offsetXY[1] - 140 : bgH // 2 - offsetXY[1] + 140,
            bgW // 2 + offsetXY[0] - 140 : bgW // 2 + offsetXY[0] + 140,
        ] = targetPic

        if messageText:
            cv2.putText(
                background,
                messageText,
                (textX, textY),
                font,
                fontScale,
                fontColor,
                lineType,
            )

        # save
        cv2.imwrite(f"{path}{session}R.png", background)

        await botReply.edit(
            content=f"{target.display_name} accepted {message.author.display_name}'{'' if message.author.display_name[-1] == 's' else 's'} hug! {'raccoodles' if 609808863914491944 in [message.author.id, target.id] else ''} ❤️\n{f'***{messageText}***' if messageText else ''}",
            attachments=[discord.File(f"{path}{session}R.png", filename="hug.png")],
        )

        if not test and not message.author.id == bot.user.id:
            hugs += 1

            with open(f"{path}hug.log", "w") as f:
                f.write(str(hugs))

            with open(f"{path}leaderboard.json", "r") as f:
                leaderboard = json.load(f)

            if str(message.author.id) in leaderboard:
                leaderboard[str(message.author.id)]["given"] += 1
            else:
                leaderboard[str(message.author.id)] = {"given": 1, "received": 0}

            if str(target.id) in leaderboard:
                leaderboard[str(target.id)]["received"] += 1
            else:
                leaderboard[str(target.id)] = {"given": 0, "received": 1}

            with open(f"{path}leaderboard.json", "w") as f:
                json.dump(leaderboard, f)

            await bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=f"{hugs} hugs given! | {prefix}help",
                )
            )

            if hugs % 100 == 0:
                replies = [
                    f"oh hey, that's the lucky {hugs}th hug! that's pretty cool, right? :D",
                    f"hey, you're the {hugs}th hug! how cool is that? :D",
                    f"woah, that's the {hugs}th hug! that's a lot of hugs! :D",
                    f"oh wow, that's the {hugs}th hug! how cool is that? :D",
                    # F"hey, that's the {hugs}th hug! that's a lot of hugs! :D",
                ]

                await botReply.reply(
                    random.choice(replies),
                )

        os.remove(f"{path}{session}R.png")
        os.remove(f"{path}{session}A.png")
        os.remove(f"{path}{session}T.png")
        # hehe rat

        if delete:
            await asyncio.sleep(1200)

            await botReply.edit(attachments=[])

    elif command == "dontautohug":
        autoHugBlacklist = open(f"{path}donthug.log", "r").read().splitlines()
        await message.reply("ok :(")
        if not str(message.author.id) in autoHugBlacklist:
            autoHugBlacklist.append(str(message.author.id))
            with open(f"{path}donthug.log", "w") as f:
                f.write("\n".join(autoHugBlacklist))
        return

    elif command == "doautohug":
        autoHugBlacklist = open(f"{path}donthug.log", "r").read().splitlines()
        await message.reply("yay :)")
        if str(message.author.id) in autoHugBlacklist:
            autoHugBlacklist.remove(str(message.author.id))
            with open(f"{path}donthug.log", "w") as f:
                f.write("\n".join(autoHugBlacklist))
        return

    elif command == "leaderboard":
        with open(f"{path}leaderboard.json", "r") as f:
            leaderboard = json.load(f)  # {id: {given: int, received: int}}

        leaderboardGiven = sorted(
            leaderboard.items(), key=lambda x: x[1]["given"], reverse=True
        )  # [(id, {given: int, received: int})]

        leaderboardGivenTop = leaderboardGiven[:5]

        output = "top huggers:\n"

        for i, (id, data) in enumerate(leaderboardGivenTop):
            if data["given"] == 0:
                break
            bold = "**" if message.author.id == int(id) else ""
            user = None
            if message.guild:
                user = message.guild.get_member(int(id))
            if not user:
                user = bot.get_user(int(id))
            try:
                name = user.display_name
            except:
                name = "(unknown)"
            output += f"{bold}{i + 1}. {name} - {data['given']} hugs given{bold}\n"

        topIds = list(int(x[0]) for x in leaderboardGivenTop)
        ids = list(int(x[0]) for x in leaderboardGiven)

        if (not message.author.id in topIds) and (message.author.id in ids):
            position = (
                leaderboardGiven.index(
                    (str(message.author.id), leaderboard[str(message.author.id)])
                )
                + 1
            )

            userAboveID = leaderboardGiven[position - 2][0]
            userAbove = None
            if message.guild:
                userAbove = message.guild.get_member(int(userAboveID))
            if not userAbove:
                userAbove = bot.get_user(int(userAboveID))
            try:
                name = userAbove.display_name
            except:
                name = "(unknown)"

            if not userAboveID in leaderboardGivenTop:
                output += "...\n"

            output += f"{position - 1}. {name} - {leaderboard[str(userAboveID)]['given']} hugs given\n"
            output += f"**{position}. {message.author.display_name} - {leaderboard[str(message.author.id)]['given']} hugs given**\n"

            try:
                userBelowID = leaderboardGiven[position][0]
                userBelow = None
                if message.guild:
                    userBelow = message.guild.get_member(int(userBelowID))
                if not userBelow:
                    userBelow = bot.get_user(int(userBelowID))
                try:
                    name = userBelow.display_name
                except:
                    name = "(unknown)"

                output += f"{position + 1}. {name} - {leaderboard[str(userBelowID)]['given']} hugs given\n"
            except:
                pass

        leaderboardReceived = sorted(
            leaderboard.items(), key=lambda x: x[1]["received"], reverse=True
        )

        leaderboardReceivedTop = leaderboardReceived[:5]

        output += "------------\ntop huggees:\n"

        for i, (id, data) in enumerate(leaderboardReceivedTop):
            if data["received"] == 0:
                break
            bold = "**" if message.author.id == int(id) else ""
            user = None
            if message.guild:
                user = message.guild.get_member(int(id))
            if not user:
                user = bot.get_user(int(id))
            try:
                name = user.display_name
            except:
                name = "(unknown)"
            output += (
                f"{bold}{i + 1}. {name} - {data['received']} hugs received{bold}\n"
            )

        topIds = list(int(x[0]) for x in leaderboardReceivedTop)
        ids = list(int(x[0]) for x in leaderboardReceived)
        if (not message.author.id in topIds) and (message.author.id in ids):
            position = (
                leaderboardReceived.index(
                    (str(message.author.id), leaderboard[str(message.author.id)])
                )
                + 1
            )

            userAboveID = leaderboardReceived[position - 2][0]
            userAbove = None
            if message.guild:
                userAbove = message.guild.get_member(int(userAboveID))
            if not userAbove:
                userAbove = bot.get_user(int(userAboveID))
            try:
                name = userAbove.display_name
            except:
                name = "(unknown)"

            if not userAboveID in leaderboardReceivedTop:
                output += "...\n"

            output += f"{position - 1}. {name} - {leaderboard[str(userAboveID)]['received']} hugs received\n"

            output += f"**{position}. {message.author.display_name} - {leaderboard[str(message.author.id)]['received']} hugs received**\n"

            try:
                userBelowID = leaderboardReceived[position][0]
                userBelow = None
                if message.guild:
                    userBelow = message.guild.get_member(int(userBelowID))
                if not userBelow:
                    userBelow = bot.get_user(int(userBelowID))
                try:
                    name = userBelow.display_name
                except:
                    name = "(unknown)"

                output += f"{position + 1}. {name} - {leaderboard[str(userBelowID)]['received']} hugs received\n"
            except:
                pass

        await message.reply(output)

    elif command == "ping":
        await message.reply(f"pong! ({round(bot.latency * 1000)}ms)")
        return

    elif command == "help":
        await message.reply(
            f"""
**{prefix}hug @user** - hug someone!
**{prefix}help** - show this message
**{prefix}leaderboard** - see the top huggers and huggees
**{prefix}ping** - check the bot's latency
**{prefix}nick** - change hugbot's nickname in this server
**{prefix}dontautohug** - hugbot will no longer autohug you
**{prefix}doautohug** - hugbot will autohug you again
if you have any questions or suggestions, `@smhaley` will be happy to help <3
feel free to contribute on github ( https://github.com/sniiz/hugbot )!
"""
        )

    elif command == "nick":
        if message.author.id != 643009464252891146:
            await message.reply("you don't have permission to do that!")
            return

        for guild in bot.guilds:
            await guild.me.edit(
                nick=message.content.replace(f"{prefix}nick ", "")
                if len(message.content) > 6
                else None
            )
            await message.reply(f"changed nickname in {guild.name}")

    elif command == "NONE":
        pass

    else:
        await message.reply(
            f"hmm. i don't know what `{command}` is. try `{prefix}help` for a list of commands!"
        )


token = open(f"{path}token.txt", "r").read()
bot.run(token)
