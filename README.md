# 💬 Chatbot RAG Project (Django + FAISS)

Un chatbot basé sur le **Retrieval-Augmented Generation (RAG)**, développé avec Django, FAISS et OpenAI.  
Ce projet permet d'uploader des documents, de les indexer avec FAISS, puis d'interroger leur contenu grâce à l'API OpenAI.

---

## ⚙️ Prérequis

- Python 3.12+
- `pip`
- Une clé API OpenAI
- (Optionnel) Docker

---

## 📦 Installation locale (sans Docker)

Clonez ce dépôt :

```bash
git clone https://github.com/votre-utilisateur/chatbot_rag_project.git
cd chatbot_rag_project
```

Ensuite :

```bash
# 1. Créer un environnement virtuel
python -m venv venv

# 2. L’activer
source venv/bin/activate  # sous Linux/macOS
# .\venv\Scripts\activate  # sous Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer l'environnement
cp .env.example .env
# Ajoutez votre clé OpenAI dans le fichier `.env`

# 5. Préparer la base de données et les index
cp db.sqlite3.example db.sqlite3
mkdir -p data faiss_index

# 6. Appliquer les migrations
python manage.py makemigrations
python manage.py migrate

# 7. Lancer le serveur
python manage.py runserver
```

Accédez à l'application via :  
[http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🐳 Utilisation avec Docker

```bash
# 1. Cloner le projet
git clone https://github.com/votre-utilisateur/chatbot_rag_project.git
cd chatbot_rag_project

# 2. Construire l'image Docker
docker build -t chatbot_rag_project .

# 3. Lancer le conteneur avec votre clé API
docker run -e OPENAI_API_KEY=your_key \
    -p 8000:8000 \
    --name chatbot_rag_container \
    chatbot_rag_project
```

---

## 🔐 Interface d'administration Django

Créer un super utilisateur (optionnel mais recommandé) :

```bash
python manage.py createsuperuser
```

Accès à l'administration :  
[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 📁 Structure du projet

```
chatbot_rag_project/
│
├── data/            # Dossiers de documents
├── faiss_index/     # Index vectoriels FAISS
├── db.sqlite3       # Base de données locale
├── .env             # Clé API OpenAI
├── manage.py        # Entrée Django
├── requirements.txt
├── Dockerfile
└── ...
```

---

## 🧠 Stack utilisée

* Django (Backend web + ORM)
* FAISS (indexation vectorielle)
* OpenAI API (GPT pour les réponses)
* Docker (déploiement)

---

## 📜 Licence

Projet éducatif à usage libre.
