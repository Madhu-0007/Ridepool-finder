# RidePool Finder MVP 🚗
A lightweight Car Pool Finder MVP built with Python/Flask, SQLite, and pristine Vanilla JavaScript/CSS. No Bootstrap dependency. Share the journey, split the cost.

<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/Vanilla_JS-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" />
</div>

## Features
- **Deep Navy & Warm Amber UI**: A highly customized visual identity using Playfair Display and DM Sans.
- **Dynamic Homepage**: Features a split From/To search bar with case-insensitive partial matching to filter active rides. Real-time statistics tracking active rides, connected cities, and shared seats.
- **Driver Profiles**: Dynamic, color-coded driver avatar chips mapped natively to row indices.
- **Seat Requests System**: Passengers can request a seat while adhering to unique duplicate-request constraints.
- **Driver-Controlled Closures**: Rides can be safely manually marked complete/closed by the driver matching their original verification contact string.
- **Animated Toast Notifications**: Real-time feedback securely driven by native Vanilla JS capturing Flask session flash messages.

## Project Structure
```text
/
├── app.py             # Main Flask routing block & logic
├── database.py        # SQLite schema initialization script
├── requirements.txt   # Pip dependencies
├── carpool.db         # SQLite data (ignored in version control)
├── static/
│   └── styles.css     # Fully custom Vanilla CSS variables and layouts
└── templates/
    ├── base.html      # Parent Jinja base providing Nav & Toast logic
    ├── index.html     # Homepage SPA logic (Hero, Stats, Filtered Grid)
    ├── post_ride.html # Standalone 2-column post creation card
    └── ride_detail.html # Split 2/3 ratio detail layout & requests
```

## Local Setup

**1. Clone the repository**
```bash
git clone https://github.com/Madhu-0007/Ridepool-finder.git
cd Ridepool-finder
```

**2. Create a Virtual Environment (Optional but recommended)**
```bash
python -m venv venv
venv\Scripts\activate   # On Windows
# source venv/bin/activate  # On macOS/Linux
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Initialize the Database**
*This will automatically generate your `carpool.db` based on the internal `rides` and `requests` mapping schema.*
```bash
python database.py
```

**5. Boot the Application**
```bash
python app.py
```
*Head over to http://127.0.0.1:5000 in your browser to start posting rides!*
