    # Use the official Python image.
    FROM python:3.10-slim

    # Set the working directory in the container
    WORKDIR /app

    # Install poetry for dependency management
    RUN pip install poetry

    # Copy only the files needed for dependency installation
    COPY poetry.lock pyproject.toml ./

    # Install dependencies without installing dev dependencies
    RUN poetry config virtualenvs.create false && poetry install --no-dev

    # Copy the rest of the application code
    COPY ./app /app/app

    # Command to run the application using uvicorn
    # It will be accessible on port 8000
    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    