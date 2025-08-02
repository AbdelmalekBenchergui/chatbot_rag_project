FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer pip et les dépendances système nécessaires
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copier les fichiers
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copier tout le projet
COPY . /app/

# Exposer le port pour Django
EXPOSE 8000

# Démarrer le serveur Django quand le conteneur démarre
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
