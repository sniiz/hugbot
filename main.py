import discord
import cv2
import requests
import os
import json

bot = discord.Client(intents=discord.Intents.all())  # bad idea probably
prefix = "hb."

path = "/home/sniiz/code/hugbot/"  # change this to your path to the repo folder

log = lambda x: print(f"[LOG] {x}")

hugs = 0

with open(f"{path}hug.log", "r") as f:
    hugs = int(f.read())


@bot.event
async def on_ready():
    print("hugger online")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{hugs} hugs given! | {prefix}help",
        )
    )


@bot.event
async def on_message(message: discord.Message):
    global hugs
    if not message.content.startswith(prefix):
        return
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
        if not message.mentions:
            await message.reply("mention someone to hug them!")
            return

        target = message.mentions[0]
        if target.id == bot.user.id:
            await message.reply(
                "unfortunately, you can't hug me. i am a bot, after all :("
            )
            return

        if target.bot:
            await message.reply("sadly bots can't accept hugs :(")
            return

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

        cv2.imwrite(f"{path}{session}R.png", background)

        log("sending")
        botReply = await message.reply(
            f"<@{message.author.id}> offers a hug to <@{target.id}>! {target.display_name}, react with 🫂 to accept!",
            file=discord.File(f"{path}{session}R.png", filename="hug.png"),
        )

        os.remove(f"{path}{session}R.png")

        await botReply.add_reaction("🫂")

        def check(reaction, user):
            return user == target and str(reaction.emoji) == "🫂"

        try:
            reaction, user = await bot.wait_for(
                "reaction_add", timeout=120.0, check=check
            )
        except:
            await botReply.edit(
                content=f"<@{target.id}> didn't accept the hug in time! 😢",
                attachments=[],
            )
            os.remove(f"{path}{session}A.png")
            os.remove(f"{path}{session}T.png")
            return

        log("accepted")

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

        # save
        cv2.imwrite(f"{path}{session}R.png", background)

        await botReply.edit(
            content=f"{target.display_name} accepted the hug! ❤️",
            attachments=[discord.File(f"{path}{session}R.png", filename="hug.png")],
        )

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

        os.remove(f"{path}{session}R.png")
        os.remove(f"{path}{session}A.png")
        os.remove(f"{path}{session}T.png")
        # hehe rat

    elif command == "leaderboard":
        with open(f"{path}leaderboard.json", "r") as f:
            leaderboard = json.load(f)

        leaderboardGiven = sorted(
            leaderboard.items(), key=lambda x: x[1]["given"], reverse=True
        )

        leaderboardGivenTop = leaderboardGiven[:5]

        output = "top huggers:\n"

        for (i, (id, data)) in enumerate(leaderboardGivenTop):
            if data["given"] == 0:
                break
            bold = "**" if message.author.id == int(id) else ""
            user = None
            if message.guild:
                user = message.guild.get_member(int(id))
            if not user:
                user = bot.get_user(int(id))

            name = user.display_name
            output += f"{bold}{i + 1}. {name} - {data['given']} hugs given{bold}\n"

        if (
            not message.author.id in leaderboardGivenTop
            and message.author.id in leaderboard
        ):
            position = (
                leaderboardGiven.index(
                    (str(message.author.id), leaderboard[str(message.author.id)])
                )
                + 1
            )
            output += f"...\n{position}. {message.author.display_name} - {leaderboard[str(message.author.id)]['given']} hugs given"

        await message.reply(output)

        leaderboardReceived = sorted(
            leaderboard.items(), key=lambda x: x[1]["received"], reverse=True
        )

        leaderboardReceivedTop = leaderboardReceived[:5]

        output = "------------\ntop huggees:\n"

        for (i, (id, data)) in enumerate(leaderboardReceivedTop):
            if data["received"] == 0:
                break
            bold = "**" if message.author.id == int(id) else ""
            user = None
            if message.guild:
                user = message.guild.get_member(int(id))
            if not user:
                user = bot.get_user(int(id))
            name = user.display_name
            output += (
                f"{bold}{i + 1}. {name} - {data['received']} hugs received{bold}\n"
            )

        if (
            not message.author.id in leaderboardReceivedTop
            and message.author.id in leaderboard
        ):
            position = (
                leaderboardReceived.index(
                    (str(message.author.id), leaderboard[str(message.author.id)])
                )
                + 1
            )
            output += f"...\n{position}. {message.author.display_name} - {leaderboard[str(message.author.id)]['received']} hugs received"

        await message.channel.send(output)

    elif command == "help":
        await message.reply(
            f"""
**{prefix}hug @user** - hug someone!
**{prefix}help** - show this message
**{prefix}leaderboard** - see the top huggers and huggees
if you have any questions or suggestions, `haley 👻#5308` will be happy to help <3
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

    else:
        await message.reply(
            f"hmm. i don't know what `{command}` is. try `{prefix}help` for a list of commands!"
        )


token = open(f"{path}token.txt", "r").read()
bot.run(token)
