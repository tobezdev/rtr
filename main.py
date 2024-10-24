import time
import json
import turtle
import random
import sqlite3
import winsound
from getpass import getpass
from werkzeug.security import generate_password_hash, check_password_hash

with open("config.json", "r") as file:
    config = json.load(file)

conn = sqlite3.connect("rtr.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, 
        password TEXT, 
        score INTEGER
    )
""")

screen = turtle.Screen()
screen.title("Run 𝐓𝐨𝐛𝐲 Run!")
screen.bgcolor(config["background_color"])
screen.setup(width=config["screen_width"], height=config["screen_height"])
screen.tracer(0)

player = turtle.Turtle()
player.shape("square")
player.color("blue")
player.penup()
player.goto(-250, 0)
player.speed(0)

obstacles = []
power_ups = []

difficulty = config["initial_difficulty"]
obstacle_speed = config["obstacle_speed"]

score = 0
paused = False

winsound_flags = winsound.SND_FILENAME | winsound.SND_ASYNC


def register():
    print("Create a New Account")
    username = input("Enter a username: ")
    password = getpass("Enter a password (hidden): ")
    hashed_password = generate_password_hash(password)

    try:
        cursor.execute(
            "INSERT INTO users (username, password, score) VALUES (?, ?, 0)",
            (username, hashed_password),
        )
        conn.commit()
        print("Account created successfully!")
    except sqlite3.IntegrityError:
        print("Username already exists. Try again.")


def login():
    global username
    print("Login to Your Account")
    username = input("Enter your username: ")
    password = getpass("Enter your password (hidden): ")

    cursor.execute("SELECT password, score FROM users WHERE username=?", (username,))
    user = cursor.fetchone()

    if user and check_password_hash(user[0], password):
        print(f"Login successful! Highest score: {user[1]}")
    else:
        print("Invalid username or password. Please try again.")
        login()


def move_up():
    y = player.ycor()
    if y < (config["screen_height"] / 2 - 10):
        player.sety(y + config["player_speed"])
        winsound.PlaySound('assets/move-player.mp3', winsound_flags)


def move_down():
    y = player.ycor()
    if y > -(config["screen_height"] / 2 - 10):
        player.sety(y - config["player_speed"])
        winsound.PlaySound('assets/move-player.mp3', winsound_flags)


def create_obstacle():
    obstacle = turtle.Turtle()
    obstacle.shape("circle")
    obstacle.color("red")
    obstacle.penup()
    obstacle.goto(
        config["screen_width"] // 2,
        random.randint(
            -config["screen_height"] // 2 + 20, config["screen_height"] // 2 - 20
        ),
    )
    obstacles.append(obstacle)


def create_power_up():
    power_up = turtle.Turtle()
    power_up.shape("triangle")
    power_up.color("green")
    power_up.penup()
    power_up.goto(
        config["screen_width"] // 2,
        random.randint(
            -config["screen_height"] // 2 + 20, config["screen_height"] // 2 - 20
        ),
    )
    power_ups.append(power_up)


def check_collision():
    for obstacle in obstacles:
        if player.distance(obstacle) < 20:
            return True
    return False


def check_power_up_collision():
    global score
    for power_up in power_ups:
        if player.distance(power_up) < 20:
            score += 10
            power_up.hideturtle()
            power_ups.remove(power_up)
            winsound.PlaySound('assets/item-pickup.mp3', winsound_flags)


def update_leaderboard():
    cursor.execute("SELECT username, score FROM users ORDER BY score DESC")
    top_players = cursor.fetchall()
    print("\nLeaderboard (Top 5):")
    for i, player in enumerate(top_players[:5]):
        print(f"{i + 1}. {player[0]} - {player[1]}")


def pause_game():
    global paused
    paused = not paused
    if paused:
        print("Game Paused. Press 'P' to resume.")
    else:
        print("Game Resumed.")


def game_loop():
    global score, difficulty, obstacle_speed
    screen.listen()
    screen.onkey(move_up, "Up")
    screen.onkey(move_down, "Down")
    screen.onkey(pause_game, "p")

    while True:
        if not paused:
            screen.update()
            time.sleep(difficulty)
            for obstacle in obstacles:
                x = obstacle.xcor()
                obstacle.setx(x - obstacle_speed)
                if obstacle.xcor() < -config["screen_width"] // 2:
                    obstacle.hideturtle()
                    obstacles.remove(obstacle)

            for power_up in power_ups:
                x = power_up.xcor()
                power_up.setx(x - obstacle_speed)
                if power_up.xcor() < -config["screen_width"] // 2:
                    power_up.hideturtle()
                    power_ups.remove(power_up)

            if random.randint(1, 5) == 1:
                create_obstacle()
            if random.randint(1, 20) == 1:
                create_power_up()

            if check_collision():
                print(f"Game Over! Final Score: {score}")
                cursor.execute("SELECT score FROM users WHERE username=?", (username,))
                high_score = cursor.fetchone()[0]
                if score > high_score:
                    cursor.execute(
                        "UPDATE users SET score=? WHERE username=?", (score, username)
                    )
                    conn.commit()
                    print(f"New high score: {score}")

                update_leaderboard()
                break

            check_power_up_collision()

            score += 1
            if score % 100 == 0:
                difficulty *= config["difficulty_increase_factor"]
                obstacle_speed += 1


def main():
    print("Welcome to Run 𝐓𝐨𝐛𝐲 Run!")
    action = input("Do you have an account? [yes/no]: ").lower()
    if action[0] == "n":
        register()
    login()
    print("Press the UP and DOWN arrow keys to dodge obstacles.")
    print("Press 'P' to pause the game.")
    game_loop()


if __name__ == "__main__":
    main()
