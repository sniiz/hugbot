with open("leaderboard.json", "w") as f:
    f.write("[]")

with open("hug.log", "w") as f:
    f.write("0")

with open("token.txt", "w") as f:
    token = input("enter token: ")
    f.write(token)
