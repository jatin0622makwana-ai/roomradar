# RoomRadar

A room-finding web app built with **Flask** and **SQLite**.

## Project Structure

```text
RoomRadar/
  app.py                  Flask backend, routes and database logic
  requirements.txt        Python dependencies
  templates/              HTML pages
  static/                 CSS files
```

## Setup and Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the app:

```bash
python app.py
```

3. Open:

```text
http://127.0.0.1:5000
```

## Database

The SQLite database is auto-created on first run. By default it is stored in your local application data folder. To use a custom path:

```bat
set ROOMRADAR_DB_PATH=C:\path\to\roomradar.db
python app.py
```

## Tables

| Table | Purpose |
| --- | --- |
| users | Registered users with name, email, phone and hashed password |
| listings | PG, hostel and flat listings with filters |
| contact_messages | Messages submitted from the contact form |

## Features

| Feature | Route | Method |
| --- | --- | --- |
| Homepage | `/` | GET |
| Login | `/login` | GET / POST |
| Sign Up | `/signup` | GET / POST |
| Reset Password | `/reset-password` | GET / POST |
| Logout | `/logout` | GET |
| Listings and Filters | `/listings` | GET |
| Listing Details | `/listings/<id>` | GET |
| Compare Listings | `/compare` | GET |
| List Property | `/list-property` | GET / POST |
| Contact | `/contact` | GET / POST |
| Listings API | `/api/listings` | GET |

## Listing Filters

- `city` - filter by city
- `area` - filter by area or keyword
- `stay_type` - PG, Hostel or Flat
- `budget` - below Rs. 5000, Rs. 5000 to Rs. 10000, or above Rs. 10000
- `gender` - Male, Female or Any

Passwords are hashed with SHA-256 before storing.
