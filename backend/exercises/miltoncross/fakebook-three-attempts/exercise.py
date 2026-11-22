print("Welcome to Fakebook")
print("********************")
print("You have three attempts.\n")

login_success = False

for attempt in range(1, 4):
    username = input("Username: ")
    password = input("Password: ")

    if username == "bart" and password == "BlueSkateboard":
        print("\nWelcome Bart\n")
        login_success = True
        break

    remaining = 3 - attempt
    if remaining:
        print(f"Incorrect details. {remaining} attempt(s) remaining.\n")
    else:
        print("Incorrect details. No attempts remaining.")
