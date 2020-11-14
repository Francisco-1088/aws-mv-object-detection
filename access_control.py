import badges
import time

def badge_reader():
    access_code=input("Please, don't obscure your face while badging in. Enter your access code: ")
    time_stamp=time.strftime("%z")
    for item in badges.badges:
        name="Unknown Person"
        if item["code"]==access_code:
            name=item["name"]
            break

    return time_stamp, access_code, name

if __name__ == "__main__":
    i=0
    a=0
    while i==0 and a<3:
        time_stamp, access_code, name = badge_reader()

        if name != "Unknown Person":
            print("This badge belongs to {}. Badge-in time is {}.".format(name, time_stamp))
            i=1
        else:
            a=a+1
            print("Invalid badge. Please try again.")
    if a==3:
        print("Too many badge-in attempts. Your badge has been locked. Speak to an officer.")
