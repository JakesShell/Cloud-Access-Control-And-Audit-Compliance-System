# Secure Document Portal

## Overview

Secure Document Portal is a Flask-based web application that allows authenticated users to upload, encrypt, store, and download files through a simple browser interface.

This project is positioned as a portfolio-ready demonstration of a real-world business scenario: an internal company portal where employees need a safer way to manage sensitive documents such as contracts, onboarding files, reports, audit evidence, HR forms, or internal records.

Instead of storing files in plain form, the application encrypts uploaded files before saving them on the server and only allows the logged-in owner to download them again.

## Real-World Business Use Case

A tool like this connects directly to common business needs.

### Example scenario

A small business, legal office, school administration team, HR department, or finance team often needs a secure internal document workflow for files such as:

- employee onboarding forms
- internal policy documents
- contracts and agreements
- audit evidence and compliance files
- client intake forms
- school or office records

In a real business environment, this kind of portal could serve as the first version of an internal secure file exchange system.

This portfolio project demonstrates important full-stack ideas that recruiters and clients care about:

- user registration and login
- access control
- encrypted file storage
- protected download flow
- persistent database records
- web application structure using Flask and SQLite

## Key Features

- User registration and login
- Password hashing for stored credentials
- File upload for authenticated users
- File encryption before server storage
- File listing for the logged-in user
- Secure file download for the file owner
- SQLite database for users and file records
- Clean browser-based interface

## Tech Stack

- Python
- Flask
- Flask-Login
- Flask-SQLAlchemy
- SQLite
- Cryptography
- HTML/CSS

## Project Structure

```text
Secure-Document-Portal/
|-- app.py
|-- requirements.txt
|-- README.md
|-- login.html
|-- register.html
|-- home.html
|-- upload.html
|-- styles.css
|-- uploads/
|   |-- .gitkeep
|-- docs/
|   |-- images/
|       |-- login-page.png
|       |-- dashboard-page.png
## Author Notes

This project was reviewed, debugged, and refactored into a working portfolio piece that demonstrates secure file handling concepts in a business-oriented web application.
