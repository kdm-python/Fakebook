print("Welcome to Fakebook")
print("********************")
print()

username = input("Please enter your username: ")
print()

banned = []
invalid = False
login_success = False

for item in banned:
    if item in username:
        invalid = True

for attempt in range(3):
    password = input("Please enter your password: ")
    print()

    if username == "george" and password == "RedSimpsons" and not invalid:
        print("Welcome George\n")
        login_success = True
        break

    remaining = 2 - attempt
    if remaining:
        print(f"Incorrect password, try again ({remaining} attempt(s) remaining)")
        print("Hint: ColourTV")
    else:
        print("Incorrect password. No attempts remaining.")
