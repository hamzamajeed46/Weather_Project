# Weather Subscription & Historical Data Django App

## 📦 Project Overview

This Django project allows users to:
- **Subscribe** to daily weather email updates for selected cities.
- **View historical weather data** for any supported city (latest log per day).
- **Manage subscriptions** via web UI and REST API.
- **Receive automated weather emails** using Celery.

Supported cities: London, New York, Tokyo, Lahore, Karachi (configurable).

---

## 🚀 Features

- **User Authentication** (signup/login/logout)
- **Weather Subscription** (choose city, receive daily emails)
- **Historical Weather API** (`/api/weather/history/<city>/`)
- **Celery-based Email Scheduling** (daily weather emails)
- **RESTful API Endpoints** for subscription management
- **Responsive Web UI** for all major features

---

## 🗂️ Project Structure

```
weather_project/
├── weather_app/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── tasks.py
│   ├── templates/weather_app/
│   │   ├── home.html
│   │   └── auth.html
│   └── ...
├── weather_project/
│   ├── settings.py
│   ├── celery.py
│   └── ...
├── venv/
├── .env
├── requirements.txt
└── manage.py
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```sh
git clone <your-repo-url>
cd Weather
```

### 2. Create & Activate Virtual Environment

```sh
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```
DJANGO_SECRET_KEY=your_secret_key
EMAIL_HOST=smtp.yourprovider.com
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
OPENWEATHER_API_KEY=your_openweathermap_api_key
```

### 5. Database Setup

By default, uses SQLite. For MySQL, update `settings.py` accordingly.

```sh
python manage.py migrate
```

### 6. Create Superuser (optional)

```sh
python manage.py createsuperuser
```

### 7. Start Django Server

```sh
python manage.py runserver
```

### 8. Start Celery Worker & Beat

Open two terminals:

**Terminal 1:**
```sh
celery -A weather_project worker --loglevel=info
```

**Terminal 2:**
```sh
celery -A weather_project beat --loglevel=info
```

---

## 🌐 Usage

- Visit `http://localhost:8000/` to access the web UI.
- Sign up, log in, and manage your weather subscriptions.
- View historical weather data for any city via the UI or API.

### API Endpoints

- **Subscribe:** `POST /api/subscribe/`
- **Unsubscribe:** `POST /api/unsubscribe/`
- **List Subscriptions:** `GET /api/subscriptions/`
- **Weather History:** `GET /api/weather/history/<city>/`

---

## 📝 Notes

- Weather data is fetched from OpenWeatherMap and cached in the database.
- Celery schedules daily weather emails at 12:00 PM PKT.
- Historical weather API returns one log per day (latest entry).

---

## 🛠️ Troubleshooting

- If emails are not sent, check your SMTP credentials and Celery worker logs.
- For production, configure a robust database and broker (e.g., MySQL, Redis).

---

## 📄 License

MIT License (see `LICENSE` file).

---

## 👨‍💻 Author

Hamza Majeed 
hamzamajeed466@gmail.com

---

Enjoy