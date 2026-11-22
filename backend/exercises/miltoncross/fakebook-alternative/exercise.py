print("Welcome to Fakebook")
print("********************")
print()

username = input("Username: ")
password = input("Password: ")
print()

if username.lower() == "lisa" and password == "PurpleDonuts":
    print("Welcome Lisa\n")
    login_success = True
else:
    print("Those details were not recognised.")
    print("Hint: Purple + Donuts")
    login_success = False
