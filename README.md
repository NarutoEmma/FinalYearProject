# AI-Powered Patient Pre-Consultation System

A full-stack mobile application that collects and structures patient symptom data **before** a GP appointment, reducing consultation time and improving the quality of information clinicians receive.

Built with a React Native frontend, FastAPI backend, MySQL database, and Groq (LLaMA) for AI-driven adaptive conversation.

---

## 💡 Motivation

Standard GP intake forms are rigid and impersonal. Patients, especially those who are anxious or unfamiliar with medical language  often struggle to describe what's wrong in a fixed format. This system replaces that experience with a natural, conversational AI that follows the patient's own language, asking adaptive follow-up questions based on what they actually say, not a predetermined script.

This insight came directly from real-world care experience working with vulnerable adults who avoided seeking medical help because the process felt inaccessible.

---

## ✨ Features

- 🤖 **Adaptive AI prompting** — follow-up questions are generated dynamically based on patient responses, not a fixed flow
- 🎙️ **Text and speech input** — patients can speak or type their symptoms
- 📋 **Clinician-ready summaries** — clear and structured symptom reporting (frequency, severity, duration)
- 🔐 **Secure session flow** — code-based session linking between patient and doctor
- 🗄️ **MySQL data storage** — all session data persisted securely
- 📱 **Cross-platform mobile UI** — built with React Native (expo), runs on ios and android

> ⚠️ **Note:** The clinician-facing dashboard UI is currently set aside for future development. The patient-facing side is fully functional.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Mobile Frontend | React Native (Expo), TypeScript |
| Backend API | Python, FastAPI |
| Database | MySQL |
| AI Model | Groq API (LLaMA) |
| Version Control | Git, GitHub |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js & Expo CLI
- MySQL (local instance)
- A [Groq API key](https://console.groq.com/)

---

### 1. Clone the repository

```bash
git clone https://github.com/NarutoEmma/FinalYearProject.git
cd FinalYearProject
```

---

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the overall project directory:

```env
GROQ_API_KEY=your_groq_api_key_here
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
SECRET_KEY=your_secret_key

SENDER_EMAIL=your_actual_email@gmail.com
SENDER_APP_PASSWORD=your_16_char_app_password
DOCTOR_EMAIL=your_target_email@gmail.com
```

Set up the MySQL database:

```bash
mysql -u root -p < database/preconsultationdb.sql
```

Start the FastAPI server from the parent project directory:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload    
```

---

### 3. Frontend setup

```bash
cd PreConsultation
npm install
npx expo start
```

Scan the QR code with the Expo Go app on your phone, or run on an emulator.

---

## 📁 Project Structure

```
FinalYearProject/
├── backend/
│   ├── app/            #FastAPI models, schemas, and database config
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── model.py
│   │   └── schemas.py
│   ├── prompts/        #ai prompts for follow-up questions   
│   │   ├── conversation.py
│   │   └── extractor.py
│   ├── routers/        #api route handlers
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── sessions.py
│   │   └── summaries.py
│   ├── services/       #ai service, code generation, emailing, pdf generation and session manager
│   │   ├── ai_service.py
│   │   ├── email_service.py
│   │   └── pdf_generator.py
│   │   └── session_manager.py
│   └── requirements.txt
├── PreConsultation/     #react native frontend
│   ├── app/            #router screens
│   │   ├── index.tsx
│   │   ├── access_code.tsx
│   │   └── _layout.tsx
│   ├── assets/         # Images
│   └── utils/          #utility functions and themes
│       └── theme.tsx
├── database/
│   └── preconsultationdb.sql #database schema
├── reports/            #generated patient symptom reports
└── README.md
```

---

## 🔮 Future Work

- [ ] Clinician-facing dashboard to review patient summaries
- [ ] Cloud deployment 
- [ ] Enhanced speech recognition accuracy
- [ ] Light/Dark themes

---

## 👤 Author

**Igwegbe Emmanuel**
- GitHub: [@NarutoEmma](https://github.com/NarutoEmma)
- LinkedIn: [emmanuel-igwegbe](https://www.linkedin.com/in/emmanuel-igwegbe-22b837347/)
- Email: captainemm699@gmail.com

---

## 📄 Licence

This project is for academic and portfolio purposes. Contact the author for any other use.
