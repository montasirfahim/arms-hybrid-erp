# ARMS (AI Powered Result Management System) - Hybrid AI-ERP 
Author: Fahim Montasir (ICT'19, MBSTU)

## Project Overview
ARMS is a specialized Enterprise Resource Planning (ERP) solution designed to automate academic workflows. It solves the complexity of manual result processing by providing a secure, automated, and AI-enhanced platform for faculty and administration.

## Tech Stack

Backend: Django 6.0 (System of Record)

AI Service: FastAPI (System of Intelligence)

Database: MySQL (Relational Storage)

AI Integration: Groq Cloud (Llama 3.3) / RAG Implementation

Security: JWT Authentication & OTP (via email) based Faculty Login

## Key Features

#### Automated Processing: 
Real-time GPA/CGPA calculation immediately upon mark entry, eliminating manual computation errors.

#### Predictive Analytics: 
Early detection of "At-Risk" students via the AI Brain, allowing faculty to intervene before the final semester results.

#### Conversational Intelligence: 
Replaces traditional, complex filter buttons with a Chat-based Query System. Users can ask, "Show me students with GPA below 2.5 in ICT-4101," and get instant results.

#### Hybrid Architecture: 
Decoupled services (Django + FastAPI) for high scalability, ensuring the AI logic doesn't slow down the core database.

#### Secure Reporting: 
Generates professional, department-standard Legal-size PDF Marksheets and automated Resultsheets for official use.


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