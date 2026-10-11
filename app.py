
import os
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort,
)
from werkzeug.security import check_password_hash
from database import get_db_connection


app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "Please set the FLASK_SECRET_KEY environment variable."
    )


# Role IDs from the roles table:
# 1 = Admin, 2 = Doctor, 3 = Nurse, 4 = Receptionist

def roles_required(*allowed_role_ids):
    def decorator(view_function):
        @wraps(view_function)
        def wrapped_view(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))

            if session.get("role_id") not in allowed_role_ids:
                abort(403)

            return view_function(*args, **kwargs)

        return wrapped_view
    return decorator


# -------------------------
# Login
# -------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT user_id, username, password_hash, role_id
                FROM users
                WHERE username = %s AND is_active = 1
                """,
                (username,),
            )

            user = cursor.fetchone()

            if user and check_password_hash(
                user["password_hash"], password
            ):
                session.clear()
                session["user_id"] = user["user_id"]
                session["username"] = user["username"]
                session["role_id"] = user["role_id"]

                return redirect(url_for("home"))

            error = "Invalid username or password."

        except Exception:
            app.logger.exception("Login failed")
            error = "Unable to sign in right now."

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    return render_template("login.html", error=error)


# -------------------------
# Dashboard
# -------------------------

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = None
    message = "Database connection failed!"

    try:
        connection = get_db_connection()

        if connection and connection.is_connected():
            message = "Database connection successful!"

    except Exception:
        app.logger.exception("Database connection check failed")

    finally:
        if connection and connection.is_connected():
            connection.close()

    return render_template(
        "home.html",
        message=message,
        username=session.get("username"),
        role_id=session.get("role_id"),
    )


# -------------------------
# Logout
# -------------------------

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------------
# Forbidden page
# -------------------------

@app.errorhandler(403)
def forbidden(error):
    return render_template("403.html"), 403


# -------------------------
# Patient list and search
# -------------------------

@app.route("/patients")
@roles_required(1, 2, 3, 4)
def patients():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        search = request.args.get("q", "").strip()

        if search:
            cursor.execute(
                """
                SELECT patient_id, identity_type, identity_number,
                       nationality, first_name, last_name,
                       date_of_birth, gender, phone
                FROM patients
                WHERE first_name LIKE %s
                   OR last_name LIKE %s
                   OR identity_number LIKE %s
                ORDER BY patient_id DESC
                """,
                (f"%{search}%", f"%{search}%", f"%{search}%"),
            )
        else:
            cursor.execute(
                """
                SELECT patient_id, identity_type, identity_number,
                       nationality, first_name, last_name,
                       date_of_birth, gender, phone
                FROM patients
                ORDER BY patient_id DESC
                """
            )

        patient_rows = cursor.fetchall()

        return render_template(
            "patients.html",
            patients=patient_rows,
            search=search,
            role_id=session.get("role_id"),
        )

    except Exception:
        app.logger.exception("Could not load patients")
        return "Unable to load patients.", 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# -------------------------
# Add patient
# Admin, Doctor, Receptionist
# -------------------------

@app.route("/patients/add", methods=["POST"])
@roles_required(1, 2, 4)
def add_patient():
    fields = {
        "identity_type": request.form.get("identity_type", "").strip(),
        "identity_number": request.form.get("identity_number", "").strip(),
        "nationality": request.form.get("nationality", "").strip(),
        "first_name": request.form.get("first_name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "date_of_birth": request.form.get("date_of_birth", "").strip(),
    }

    if not all(fields.values()):
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("patients"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO patients (
                identity_type, identity_number, nationality,
                first_name, last_name, date_of_birth,
                gender, blood_type, phone, address,
                smoking_status, allergies
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                fields["identity_type"],
                fields["identity_number"],
                fields["nationality"],
                fields["first_name"],
                fields["last_name"],
                fields["date_of_birth"],
                request.form.get("gender") or None,
                request.form.get("blood_type") or None,
                request.form.get("phone") or None,
                request.form.get("address") or None,
                request.form.get("smoking_status") or None,
                request.form.get("allergies") or None,
            ),
        )

        connection.commit()
        flash("Patient added successfully.", "success")

    except Exception as err:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Could not add patient")

        if "uq_patient_identity" in str(err):
            flash(
                "A patient with this identity type and number already exists.",
                "error",
            )
        else:
            flash(
                "Could not add patient. Check the submitted data and database constraints.",
                "error",
            )

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("patients"))


# -------------------------
# Edit patient
# Admin, Doctor, Nurse
# -------------------------

@app.route(
    "/patients/<int:patient_id>/edit",
    methods=["GET", "POST"],
)
@roles_required(1, 2, 3)
def edit_patient(patient_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":
            fields = {
                "identity_type": request.form.get(
                    "identity_type", ""
                ).strip(),
                "identity_number": request.form.get(
                    "identity_number", ""
                ).strip(),
                "nationality": request.form.get(
                    "nationality", ""
                ).strip(),
                "first_name": request.form.get(
                    "first_name", ""
                ).strip(),
                "last_name": request.form.get(
                    "last_name", ""
                ).strip(),
                "date_of_birth": request.form.get(
                    "date_of_birth", ""
                ).strip(),
            }

            if not all(fields.values()):
                cursor.execute(
                    "SELECT * FROM patients WHERE patient_id = %s",
                    (patient_id,),
                )
                patient = cursor.fetchone()

                if not patient:
                    flash("Patient not found.", "error")
                    return redirect(url_for("patients"))

                flash("Please fill in all required fields.", "error")
                return render_template(
                    "edit_patient.html",
                    patient=patient,
                    role_id=session.get("role_id"),
                )

            cursor.execute(
                """
                UPDATE patients
                SET identity_type = %s,
                    identity_number = %s,
                    nationality = %s,
                    first_name = %s,
                    last_name = %s,
                    date_of_birth = %s,
                    gender = %s,
                    blood_type = %s,
                    phone = %s,
                    address = %s,
                    smoking_status = %s,
                    allergies = %s
                WHERE patient_id = %s
                """,
                (
                    fields["identity_type"],
                    fields["identity_number"],
                    fields["nationality"],
                    fields["first_name"],
                    fields["last_name"],
                    fields["date_of_birth"],
                    request.form.get("gender") or None,
                    request.form.get("blood_type") or None,
                    request.form.get("phone") or None,
                    request.form.get("address") or None,
                    request.form.get("smoking_status") or None,
                    request.form.get("allergies") or None,
                    patient_id,
                ),
            )

            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT patient_id FROM patients WHERE patient_id = %s",
                    (patient_id,),
                )

                if cursor.fetchone() is None:
                    connection.rollback()
                    flash("Patient not found.", "error")
                    return redirect(url_for("patients"))

            connection.commit()
            flash("Patient updated successfully.", "success")
            return redirect(url_for("patients"))

        cursor.execute(
            "SELECT * FROM patients WHERE patient_id = %s",
            (patient_id,),
        )
        patient = cursor.fetchone()

        if not patient:
            flash("Patient not found.", "error")
            return redirect(url_for("patients"))

        return render_template(
            "edit_patient.html",
            patient=patient,
            role_id=session.get("role_id"),
        )

    except Exception as err:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Could not edit patient")

        if "uq_patient_identity" in str(err):
            flash(
                "Another patient already has this identity type and number.",
                "error",
            )
        else:
            flash(
                "Could not update patient. Please check the submitted data.",
                "error",
            )

        return redirect(url_for("patients"))

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# -------------------------
# Delete patient
# Admin only
# -------------------------

@app.route(
    "/patients/<int:patient_id>/delete",
    methods=["POST"],
)
@roles_required(1)
def delete_patient(patient_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT patient_id FROM patients WHERE patient_id = %s",
            (patient_id,),
        )

        if cursor.fetchone() is None:
            flash("Patient not found.", "error")
            return redirect(url_for("patients"))

        cursor.execute(
            "DELETE FROM patients WHERE patient_id = %s",
            (patient_id,),
        )

        connection.commit()
        flash("Patient deleted successfully.", "success")

    except Exception as err:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Could not delete patient")

        error_text = str(err).lower()

        if (
            "1451" in error_text
            or "foreign key constraint fails" in error_text
        ):
            flash(
                "This patient has related records and cannot be deleted. "
                "Preserve the related medical records.",
                "error",
            )
        else:
            flash("Could not delete patient.", "error")

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("patients"))


if __name__ == "__main__":
    app.run(debug=True)
