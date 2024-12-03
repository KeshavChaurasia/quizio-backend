# Quizio

A Django-based quiz application where users can register, take quizzes, and track their quiz history. The app includes features such as multimedia questions, user profiles, and quiz creation.

## Features

- User authentication and profiles.
- Create, view, and take quizzes with multimedia questions.
- Track quiz attempts and scores.
- Admin interface for managing quizzes, questions, and attempts.

## Prerequisites

Ensure you have the following installed on your machine:

- Python 3.8 or higher
- Poetry for dependency management
- PostgreSQL (or any database supported by Django)

## Setup Instructions
### Step 1: Clone the Repository

`git clone https://github.com/your-username/quiz-app.git
cd quiz-app`

### Step 2: Install Dependencies

Using Poetry, install the project dependencies:

`poetry install`

This command will create a virtual environment and install all required dependencies as listed in pyproject.toml.

### Step 3: Configure Environment Variables

Create a .env file in the project root directory to store environment variables. Example:

SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=postgres://username:password@localhost:5432/quiz_db

You can generate a SECRET_KEY using the following Python snippet:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Step 4: Apply Migrations

Run the migrations to set up the database schema:

```bash
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```
### Step 5: Create a Superuser (Admin Account)

Create an admin account to access the Django admin panel:

`poetry run python manage.py createsuperuser`

### Step 6: Populate the Database (Optional)

If you want to add initial data such as quizzes, questions, and attempts, run the populate_db.py script:

`poetry run python populate_db.py`

### Step 7: Run the Development Server

Start the Django development server:

`poetry run python manage.py runserver`

Visit http://127.0.0.1:8000 in your browser to access the app.

## Running Tests

To run tests for the application, use the following command:

`poetry run python manage.py test`

## Deployment

When deploying to production:

- Set DEBUG=False in your .env file.
- Configure ALLOWED_HOSTS with your domain or server IP.
- Use a production-ready web server (e.g., Gunicorn or uWSGI) and configure a reverse proxy like Nginx.
- Run the following command to collect static files:

    `poetry run python manage.py collectstatic`

## API Documentation

The application uses drf-yasg for API documentation. After starting the server, visit the Swagger UI at:

http://127.0.0.1:8000/swagger/

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Contributing

- Fork the repository.
- Create a feature branch (git checkout -b feature-name).
- Commit your changes (git commit -m "Add feature name").
- Push to the branch (git push origin feature-name).
- Create a pull request.

## Support

If you encounter any issues, please open an issue on GitHub or reach out to the maintainer.