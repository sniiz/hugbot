with open("leaderboard.json", "w") as f:
    f.write("[]")

with open("hug.log", "w") as f:
    f.write("0")

with open("donthug.log", "w") as f:
    f.write("")

with open("token.txt", "w") as f:
    token = input("enter discord token: ")
    f.write(token)

with open("hftoken.txt", "w") as f:
    token = input("enter huggingface token: ")
    f.write(token)