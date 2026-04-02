# ARMS-Hybrid-ERP
Author: Fahim Montasir (ICT'19, MBSTU)

## Project Overview
ARMS is a specialized Enterprise Resource Planning (ERP) solution designed to automate academic workflows. It solves the complexity of manual result processing by providing a secure, automated, and AI-enhanced platform for faculty and administration.

## Tech Stack

Backend: Django 6.0 (System of Record)

AI Service: FastAPI (System of Intelligence)

Database: MySQL (Relational Storage)

AI Integration: Groq Cloud (Llama 3.3) / RAG Implementation

Security: JWT Authentication & OTP-based Faculty Login

## Key Features

Automated Processing: Real-time GPA/CGPA calculation on mark entry.

Predictive Analytics: Early detection of "At-Risk" students via the AI Brain.

Hybrid Architecture: Decoupled services for high scalability and performance.

Secure Reporting: Generates professional Legal-size PDF Marksheets.

## Installation & Setup

Clone the repository to your local machine.

Create a virtual environment: 
```
python -m venv venv
```

Activate the environment: 
```
.\venv\Scripts\activate
```

Install dependencies: 
```
pip install -r requirements.txt
```
Configure your ```.env``` file with MySQL credentials and Groq API keys.

Run migrations: 
```
python manage.py migrate
```

Start the system: ```run_arms.bat```