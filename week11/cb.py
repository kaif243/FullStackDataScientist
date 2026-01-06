import random

def generate_number():
    # Generate a random 4-digit number as a string
    digits = list("0123456789")
    random.shuffle(digits)
    return ''.join(digits[:4])

def cows_and_bulls(target, guess):
    bulls = 0
    cows = 0

    for i in range(4):
        if guess[i] == target[i]:
            bulls += 1
        elif guess[i] in target:
            cows += 1

    return cows, bulls

# Main Game
target = generate_number()
attempts = 0

print("🎯 Welcome to Cows and Bulls Game!")
print("Guess the 4-digit number")

while True:
    guess = input("Enter your 4-digit guess: ")

    if len(guess) != 4 or not guess.isdigit():
        print("❌ Please enter a valid 4-digit number")
        continue

    attempts += 1
    cows, bulls = cows_and_bulls(target, guess)

    print(f"🐄 Cows: {cows}, 🐂 Bulls: {bulls}")

    if bulls == 4:
        print(f"🎉 Congratulations! You guessed the number {target} in {attempts} attempts.")
        break
