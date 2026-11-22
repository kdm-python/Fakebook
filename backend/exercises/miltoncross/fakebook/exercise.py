print("Welcome to Fakebook")
print("********************")
print()

username = input("Please enter your username: ")
print()
password = input("Please enter your password: ")
print()

banned = []
invalid = False

for item in banned:
    if item in username:
        invalid = True

if username == "george" and password == "RedSimpsons" and not invalid:
    print("Welcome George\n")
    login_success = True
else:
    print("Incorrect password, try again")
    print("Hint: ColourTV")
    login_success = False
