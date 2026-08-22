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
    print("Welcome George")
    print()
    print("Enter the following URL into a web browser:")
    print()
    print("ncce.io/cybs-3-a0-rf1")
else:
    print()
    print("Incorrect password, try again")
    print("Hint: ColourTV")
