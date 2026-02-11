FROM python:3.12-slim

WORKDIR /app

# Sistemske odvisnosti
RUN apt-get update && apt-get install -y     curl     gnupg     unixodbc     unixodbc-dev     && rm -rf /var/lib/apt/lists/*

# Microsoft ODBC Driver 18 za SQL Server
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg     && echo 'deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main' > /etc/apt/sources.list.d/mssql-release.list     && apt-get update     && ACCEPT_EULA=Y apt-get install -y msodbcsql18     && rm -rf /var/lib/apt/lists/*

# Python odvisnosti
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Aplikacija
COPY app/ ./app/

# Ustvari direktorije
RUN mkdir -p /app/documents /app/logs

# Expose port
EXPOSE 8000

# Zaženi
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
