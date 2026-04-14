# 🏥 AI-Powered Patient Pre-Consultation System

A full-stack mobile application that collects and structures patient symptom data **before** a GP appointment — reducing consultation time and improving the quality of information clinicians receive.

Built with a React Native frontend, FastAPI backend, MySQL database, and Groq (LLaMA) for AI-driven adaptive conversation.

---

## 💡 Motivation

Standard GP intake forms are rigid and impersonal. Patients — especially those who are anxious or unfamiliar with medical language — often struggle to describe what's wrong in a fixed format. This system replaces that experience with a natural, conversational AI that follows the patient's own language, asking adaptive follow-up questions based on what they actually say, not a predetermined script.

This insight came directly from real-world care experience working with vulnerable adults who avoided seeking medical help because the process felt inaccessible.

---

## ✨ Features

- 🤖 **Adaptive AI prompting** — follow-up questions are generated dynamically based on patient responses, not a fixed flow
- 🎙️ **Text and speech input** — patients can speak or type their symptoms
- 📋 **Clinician-ready summaries** — structured output aligned with NHS-style symptom reporting (frequency, severity, duration)
- 🔐 **Secure session flow** — code-based session linking between patient and doctor
- 🗄️ **MySQL data storage** — all session data persisted securely
- 📱 **Cross-platform mobile UI** — built with React Native (Expo), runs on iOS and Android

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

Create a `.env` file in the `backend/` directory:

```env
GROQ_API_KEY=your_groq_api_key_here
DB_HOST=localhost
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=preconsultation_db
```

Set up the MySQL database:

```bash
mysql -u root -p < schema.sql
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

---

### 3. Frontend setup

```bash
cd frontend
npm install
npx expo start
```

Scan the QR code with the Expo Go app on your phone, or run on an emulator.

---

## 📁 Project Structure

```
FinalYearProject/
├── backend/
│   ├── main.py          # FastAPI entry point
│   ├── routes/          # API route handlers
│   ├── models/          # Database models
│   ├── ai/              # Groq/LLaMA prompting logic
│   └── schema.sql       # MySQL database schema
├── frontend/
│   ├── app/             # React Native screens
│   ├── components/      # Reusable UI components
│   └── services/        # API communication layer
└── README.md
```

---

## 🔮 Future Work

- [ ] Clinician-facing dashboard to review patient summaries
- [ ] Cloud deployment (backend on Render or Railway)
- [ ] Enhanced speech recognition accuracy
- [ ] GP system integration via HL7/FHIR standards

---

## 👤 Author

**Igwegbe Emmanuel**
- GitHub: [@NarutoEmma](https://github.com/NarutoEmma)
- LinkedIn: [emmanuel-igwegbe](https://www.linkedin.com/in/emmanuel-igwegbe-22b837347/)
- Email: captainemm45@gmail.com

---

## 📄 Licence

This project is for academic and portfolio purposes. Contact the author for any other use.
