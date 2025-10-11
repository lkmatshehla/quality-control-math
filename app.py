from flask import Flask, render_template, request, session, redirect, url_for
import random
import time

# Import PayPal Payouts SDK
from paypalpayoutssdk.core import PayPalHttpClient, LiveEnvironment
from paypalpayoutssdk.payouts import PayoutsPostRequest
from paypalhttp import HttpError

app = Flask(__name__)
app.secret_key = "supersecretkey"
COIN_TO_USD = 0.10

# Your LIVE PayPal credentials (replace with your actual live keys)
CLIENT_ID = "AYwazerdTT9PRde0K9tCmMjTLtuieD08o-EJ4ZqVymNpJoBvBuWgnBryzuXNWo9sohkIaAFRFh461jdg"
CLIENT_SECRET = "EPUUZ2YuhclTL5mAONVDSOSE6yADoXIjYpS4lKfHSP5UfLAqJoU1uaK2cmVvql1_xYgOsAkOY80e0G5p"

# Configure PayPal client in LIVE mode
paypal_client = PayPalHttpClient(
    LiveEnvironment(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
)

def coins_to_currency(coins):
    return round(coins * COIN_TO_USD, 2)

def generate_question():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    op = random.choice(["+", "-", "*"])
    if op == "+":
        answer = a + b
    elif op == "-":
        answer = a - b
    else:
        answer = a * b
    question = f"{a} {op} {b}"
    return question, answer

@app.route("/", methods=["GET", "POST"])
def index():
    if "coins" not in session:
        session["coins"] = 0
    feedback = ""
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = session.get("correct_answer")
        if user_answer and correct_answer is not None:
            try:
                if int(user_answer) == correct_answer:
                    session["coins"] += 1
                    feedback = "Correct! You earned a coin."
                else:
                    feedback = "Incorrect. Try again!"
            except ValueError:
                feedback = "Please enter a number."
    question, answer = generate_question()
    session["correct_answer"] = answer
    usd = coins_to_currency(session["coins"])
    return render_template("index.html", question=question, coins=session["coins"], usd=usd, feedback=feedback)

@app.route("/cashout", methods=["GET", "POST"])
def cashout():
    if "coins" not in session:
        session["coins"] = 0
    usd = coins_to_currency(session["coins"])
    message = ""

    if request.method == "POST":
        paypal_email = request.form.get("paypal_email")
        if usd >= 1.0 and paypal_email:
            # Build Payout Request
            request_body = {
                "sender_batch_header": {
                    "recipient_type": "EMAIL",
                    "sender_batch_id": f"batch_{int(time.time())}",
                    "email_subject": "You have a payout!",
                    "email_message": "Thanks for playing the math game!"
                },
                "items": [
                    {
                        "receiver": paypal_email,
                        "amount": {
                            "value": f"{usd:.2f}",
                            "currency": "USD"
                        },
                        "note": "Your cashout from Math Game!",
                        "sender_item_id": f"item_{int(time.time())}"
                    }
                ]
            }

            payout_request = PayoutsPostRequest()
            payout_request.request_body(request_body)

            try:
                response = paypal_client.execute(payout_request)
                batch_id = response.result.batch_header.payout_batch_id
                message = f"✅ Payout sent! PayPal batch ID: {batch_id}"
                session["coins"] = 0
                usd = 0.0
            except HttpError as httpe:
                message = f"❌ PayPal payout failed: {httpe.status_code} {httpe.message}"
        else:
            message = "Minimum cash out is $1 and valid PayPal email is required."

    return render_template("cashout.html", coins=session["coins"], usd=usd, message=message)

if __name__ == "__main__":
    app.run(debug=True)
