# Hospital Management System 

A Flask-based Hospital Management System designed to support inpatient clinical information management and General Surgery patient follow-up.

This project focuses on improving inpatient follow-up workflows through structured patient records, relational database design, and role-based access control.

## Technologies

- **Backend:** Python, Flask
- **Database:** MySQL
- **Frontend:** HTML, CSS
- **Password Security:** Werkzeug password hashing
- **Version Control:** Git, GitHub

## Database Design

The EER diagram illustrates the relational database structure designed for the Hospital Management System.

[View the EER Diagram](https://github.com/eylwren/Hospital-management-system/blob/main/docs/eer-diagram.png)

![Hospital Management System EER Diagram](https://github.com/eylwren/Hospital-management-system/raw/main/docs/eer-diagram.png)

## Current Features

### Authentication and Authorization
- User login and logout
- Password hashing and verification
- Session-based authentication
- Role-based access control
- Restricted access to unauthorized operations
- HTTP 403 Forbidden error handling

### Patient Management
- Patient listing and search
- Patient registration
- Patient record editing
- Patient deletion with administrator-only authorization
- Database constraint to prevent duplicate patient identities

### Database
- MySQL database connectivity
- Relational database structure for hospital and inpatient clinical data
- Database tables for patient admissions, diagnoses, procedures, medications, vital signs, and clinical courses

## User Roles

| Role | Current Permissions |
|---|---|
| Admin | View, add, edit, and delete patients |
| Doctor | View, add, and edit patients |
| Nurse | View and edit patients |
| Receptionist | View and add patients |

*Permissions are enforced at the application route level. The interface and permission rules are still under development.*

## Planned Features

- Inpatient admission tracking workflows
- Clinical course and vital signs management
- Diagnosis and procedure management
- Medication management workflows
- Audit logging for patient-related operations
- Further role-specific interface improvements
- Additional validation and security improvements

## Local Setup

### Prerequisites

- Python
- MySQL Server
- Git

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/eylwren/Hospital-management-system.git
   cd Hospital-management-system
   ```

2. Create and activate a virtual environment:

   **Windows (PowerShell)**

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install the project dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

   If `requirements.txt` has not been created yet, install the dependencies used by the application and add them to a requirements file before following this step.

4. Create the MySQL database and configure the database connection in your local environment.

5. Set the Flask secret key as an environment variable:

   ```powershell
   $env:FLASK_SECRET_KEY = "your-local-secret-key"
   ```

6. Run the application:

   ```powershell
   python app.py
   ```

7. Open the local address displayed in the terminal in your browser.

## Security and Data Disclaimer

This project is intended for educational and portfolio purposes only.

- Use synthetic test data only.
- Do not enter real patient information.
- Do not commit passwords, secret keys, database credentials, or environment files to version control.
- The application is a development project and is not intended for production use.

## Project Status

**In development.**

The project currently includes the initial Flask application, MySQL connectivity, patient management operations, authentication, and role-based access control. Clinical workflows, audit logging, and additional security improvements remain in development.
