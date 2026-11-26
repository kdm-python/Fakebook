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

while not login_success:
    password = input("Please enter your password: ")
    print()

    if username == "george" and password == "RedSimpsons" and not invalid:
        print("Welcome George\n")
        login_success = True
        break

    print("Incorrect password, try again")
    print("Hint: ColourTV")
