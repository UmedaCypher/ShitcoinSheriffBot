# Étape 1: Utiliser une image Python officielle et légère
FROM python:3.11-slim

# Ajout d'une variable d'environnement pour que les logs s'affichent instantanément
ENV PYTHONUNBUFFERED=1

# Étape 2: Définir le dossier de travail à l'intérieur du conteneur
WORKDIR /app

# Étape 3: Copier le fichier des dépendances
COPY requirements.txt .

# Étape 4: Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Étape 5: Copier le code du bot
COPY bot.py .

# Étape 6: Définir la commande qui sera lancée au démarrage du conteneur
CMD ["python3", "bot.py"]
