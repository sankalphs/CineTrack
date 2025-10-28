# 🎬 CineTrack

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://mysql.com)
[![CustomTkinter](https://img.shields.io/badge/CustomTkinter-Latest-green.svg)](https://github.com/TomSchimansky/CustomTkinter)

A comprehensive movie tracking and management application with an IMDB-inspired dark theme interface. CineTrack allows users to manage movie databases, track watchlists, manage cast and crew information, and much more.


## ✨ Features

### 🎭 Core Functionality
- **Movie Management**: Add, edit, and delete movies with detailed information
- **Cast & Crew Database**: Comprehensive cast member management with biographies
- **TV Series Support**: Track and manage television series
- **User System**: Multi-user support with individual watchlists
- **Studio Management**: Track production studios and their films
- **Streaming Platform Integration**: Link movies to streaming services

### 🎨 User Interface
- **IMDB-Inspired Design**: Dark theme with signature yellow accents
- **Responsive Layout**: Adaptive interface with smooth navigation
- **Advanced Search**: Search across movies, cast, and keywords
- **Data Visualization**: Statistics and analytics dashboard
- **Tooltips & Hover Effects**: Enhanced user experience

### 💰 Additional Features
- **Donation System**: User contribution tracking
- **Watchlist Management**: Personal movie tracking per user
- **CSV Import/Export**: Bulk data operations
- **Database Statistics**: Comprehensive analytics dashboard
- **Genre Classification**: Organized content categorization

## 🛠️ Technology Stack

- **Frontend**: CustomTkinter (Modern UI Library)
- **Backend**: Python 3.8+
- **Database**: MySQL 8.0+
- **Additional Libraries**:
  - `mysql-connector-python` - Database connectivity
  - `csv` - Data import/export
  - `datetime` - Date handling
  - `re` - Regular expressions

## 📋 Prerequisites

Before running CineTrack, ensure you have:

1. **Python 3.8 or higher** installed
2. **MySQL Server 8.0+** running locally
3. Required Python packages (see Installation)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/sankalphs/CineTrack.git
cd CineTrack
```

### 2. Install Dependencies
```bash
pip install customtkinter mysql-connector-python
```

### 3. Database Setup

1. Start your MySQL server

2. Create the database manually:
```bash
mysql -u root -p < code.sql
```

3. Update database credentials in `main.py`:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "your_username",      # Change this
    "password": "your_password",  # Change this  
    "database": "cinetrack"
}
```

⚠️ **Security Note**: Never commit real database credentials to version control. Consider using environment variables or a separate config file for production deployments.

### 4. Run the Application
```bash
python p.py
```

## 🔄 CI/CD Pipeline

This project includes automated testing and deployment via GitHub Actions:

- **Continuous Integration**: Automated testing on push/pull requests
- **Code Quality Checks**: Linting and formatting validation
- **Multi-Python Version Testing**: Ensures compatibility across Python versions

The CI configuration is located in `.github/workflows/ci.yml`.

## 📊 Database Schema

The application uses a comprehensive MySQL schema with the following main tables:

- **users** - User accounts and authentication
- **movies** - Movie information and metadata
- **cast_members** - Actor/director profiles
- **genres** - Movie genre classifications
- **studios** - Production company information
- **streaming_platforms** - Streaming service data
- **watchlists** - User personal movie lists
- **donations** - User contribution tracking

## 🎯 Usage Guide

### Getting Started
1. **Launch the Application**: Run `python p.py`
2. **Create Account**: Use the Login page to register
3. **Import Data**: Use CSV import for bulk movie addition
4. **Explore**: Navigate through Movies, Cast, TV, and other sections

### Key Functions
- **Add Movies**: Click "Add Movie" to input new films
- **Search**: Use the top search bar for quick lookups  
- **Manage Watchlist**: Add movies to personal tracking lists
- **View Statistics**: Check the DB Stats page for analytics
- **Export Data**: Use CSV export for data backup

### Navigation
The main navigation bar provides access to:
- 🏠 **Home** - Dashboard and overview
- 🎬 **Movies** - Movie database browser
- 🎭 **Cast** - Actor/director profiles  
- 📺 **TV** - Television series management
- 👤 **Login** - User authentication
- 👥 **Users** - User management (admin)
- 🏢 **Studios** - Production company data
- 📋 **Watchlist** - Personal movie lists
- 💰 **Donations** - Contribution tracking
- 📊 **DB Stats** - Database analytics

## 🔧 Configuration

### Database Connection
Update the connection parameters in `main.py`:
```python
conn = mysql.connector.connect(
    host="localhost",        # Database host
    user="root",            # Your MySQL username
    password="qwerty1234",  # Your MySQL password  
    database="cinetrack"    # Database name
)
```


## 📁 Project Structure

```
CineTrack/
├── main.py                    # Main application file
├── code.sql               # Database schema and setup
├── README.md              # Project documentation
├── .gitignore            # Git ignore configuration
├── .github/              # GitHub configuration
│   └── workflows/        # CI/CD workflows
│       └── ci.yml        # Continuous integration setup
└── __pycache__/          # Python cache files
```


## 👨‍💻 Authors


**Sankalp H S**

- GitHub: [@sankalphs](https://github.com/sankalphs)

**Sandhyarani M**

- GitHub: [@sandhya-6360](https://github.com/ssandhya-6360)

## 🙏 Acknowledgments

- Inspired by [IMDB](https://imdb.com) design aesthetics
- Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) by Tom Schimansky
- Database design following modern relational principles

---

⭐ **Star this repository if you found it helpful!**
