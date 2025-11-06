# 🚀 Lancement du projet

## 🧩 Prérequis

Avant de commencer, assurez-vous d’avoir installé :

- **Python 3.10+**
- **[uv](https://github.com/astral-sh/uv)** (gestionnaire d’environnements et de dépendances)

---

## ⚙️ Installation des dépendances

Dans le premier terminal :

```bash
uv sync
```

Cette commande installe toutes les dépendances nécessaires au projet à partir du fichier `pyproject.toml`.

---

## 🖥️ Lancer l’API

Toujours dans le **premier terminal**, exécutez :

```bash
uv run python api/start_api.py
```

Cela démarre le serveur **API** (backend) de l’application.

---

## 💡 Lancer l’application Streamlit

Dans un **second terminal**, lancez l’interface Streamlit :

```bash
uv run streamlit run app/app_api.py
```

Cela démarre le **frontend** Streamlit connecté à l’API.

---

## 🌍 Accès à l’application

Une fois les deux serveurs lancés, ouvrez votre navigateur à l’adresse indiquée par Streamlit  
(par défaut : [http://localhost:8501](http://localhost:8501)).

---

## 🧰 Structure du projet

```
.
├── api/
│   └── start_api.py        # Démarrage de l’API
├── app/
│   └── app_api.py          # Application Streamlit
├── pyproject.toml          # Dépendances du projet
└── README.md               # Documentation (ce fichier)
```

---

## 🧑‍💻 Développement

Pour exécuter n’importe quel script Python dans l’environnement du projet :

```bash
uv run python path/to/script.py
```
