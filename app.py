from flask import Flask, render_template
from database import get_db_connection

app = Flask(__name__)


@app.route("/")
def home():
    connection = get_db_connection()

    if connection.is_connected():
        message = "Database connection successful!"
        connection.close()
    else:
        message = "Database connection failed!"

    return render_template("home.html", message=message)


if __name__ == "__main__":
    app.run(debug=True)