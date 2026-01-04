# 🔒 SSH Sentinel Pro - Analyse de Sécurité

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://votre-app.streamlit.app)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Description

**SSH Sentinel Pro** est une application web interactive développée avec Streamlit pour analyser et visualiser les tentatives d'intrusion SSH. Elle transforme des fichiers de logs bruts en tableaux de bord interactifs avec géolocalisation des attaques, statistiques détaillées et filtres avancés.

### 🎯 Objectif du Projet

Fournir aux responsables sécurité un outil visuel et accessible pour surveiller les tentatives d'intrusion sans avoir à lire du code ou manipuler des fichiers de logs complexes.

---

## ✨ Fonctionnalités

### 📊 Visualisations Interactives
- **Tableau de bord dynamique** avec métriques clés (événements totaux, IPs uniques, tentatives échouées)
- **Graphiques temporels** : activité horaire et journalière
- **Top 10 des IPs** les plus agressives
- **Carte géographique interactive** avec géolocalisation des attaques

### 🔍 Filtres Avancés
- **Filtrage temporel** : sélection par plage de dates
- **Filtrage par type d'événement** : tentatives échouées, connexions réussies, utilisateurs invalides, etc.
- **Filtrage par IP** : analyse d'adresses spécifiques
- **Filtrage par utilisateur** : suivi des comptes ciblés

### 🚀 Optimisations
- **Système de cache intelligent** : évite le rechargement des données à chaque interaction
- **Géolocalisation automatique** des IPs avec MaxMind GeoLite2
- **Échantillonnage optionnel** pour les gros fichiers
- **Détection automatique de l'encodage** des fichiers

### 📤 Export
- **Téléchargement CSV** des données filtrées
- **Gestion du cache** avec possibilité de vidage manuel

---

## 🛠️ Installation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Installation Locale

1. **Cloner le repository**
```bash
git clone https://github.com/Voldemort54/ssh_monitor.git
cd ssh_monitor
```

2. **Créer un environnement virtuel** (recommandé)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Lancer l'application**
```bash
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

---

## 📖 Utilisation

### 1️⃣ Téléverser un Fichier de Logs

- Cliquez sur **"Browse files"** dans la barre latérale
- Sélectionnez votre fichier CSV de logs SSH
- Format attendu : `Timestamp;Lab;Service;PID;IP;User;EventCode;Message`

### 2️⃣ Configurer les Options

**Géolocalisation :**
- ✅ Activée par défaut (télécharge automatiquement la base GeoLite2)
- Permet d'afficher la carte des attaques

**Échantillonnage :**
- Par défaut : toutes les lignes sont analysées
- Pour les gros fichiers : sélectionnez "Échantillon personnalisé"

### 3️⃣ Filtrer les Données

Utilisez les filtres dans la barre latérale :
- **Plage de dates** : sélectionnez la période à analyser
- **Types d'événements** : choisissez les catégories à afficher
- **IPs spécifiques** : analysez des adresses particulières
- **Utilisateurs** : suivez les comptes ciblés

### 4️⃣ Explorer les Onglets

- **📊 Tableau de Bord** : vue d'ensemble avec métriques et graphiques
- **🗺 Carte** : géolocalisation des attaques sur une carte interactive
- **📈 Statistiques** : répartition des types d'événements
- **🔍 Détails** : tableau complet des événements et messages fréquents

### 5️⃣ Exporter les Résultats

- Cliquez sur **"Exporter les données"** dans la barre latérale
- Téléchargez le CSV filtré avec vos critères

---

## 📁 Structure du Projet

```
ssh_monitor/
├── app.py                  # Application Streamlit principale
├── requirements.txt        # Dépendances Python
├── .gitignore             # Fichiers exclus de Git
├── README.md              # Documentation (ce fichier)
├── cache/                 # Cache des données (généré automatiquement)
└── GeoLite2-City.mmdb    # Base de géolocalisation (téléchargée automatiquement)
```

---

## 🔧 Technologies Utilisées

| Technologie | Version | Utilisation |
|-------------|---------|-------------|
| **Streamlit** | 1.28.0+ | Framework web interactif |
| **Pandas** | 2.0.3+ | Manipulation de données |
| **Plotly** | 5.15.0+ | Visualisations interactives |
| **MaxMind GeoLite2** | 2.4.0+ | Géolocalisation des IPs |
| **Joblib** | 1.3.0+ | Système de cache |
| **Chardet** | 5.2.0+ | Détection d'encodage |

---

## 🎓 Contexte Pédagogique

Ce projet a été développé dans le cadre d'un exercice de formation visant à :
- Transformer un Jupyter Notebook d'analyse en application web professionnelle
- Maîtriser Streamlit pour créer des dashboards interactifs
- Implémenter des optimisations (cache, échantillonnage)
- Déployer une application sur le cloud (Streamlit Community Cloud)
- Utiliser Git et GitHub pour le versioning

### Compétences Développées
- ✅ Architecture d'application web
- ✅ Visualisation de données
- ✅ Optimisation des performances
- ✅ Gestion de versions avec Git
- ✅ Déploiement cloud
- ✅ Analyse de sécurité

---

## 📝 Format des Données

### Format CSV Attendu

Le fichier doit être au format CSV avec séparateur `;` et contenir les colonnes suivantes :

```csv
Timestamp;Lab;Service;PID;IP;User;EventCode;Message
2024-01-15 10:23:45;server01;sshd;12345;192.168.1.100;root;AUTH_FAILED;Failed password for root from 192.168.1.100
```

### Colonnes

| Colonne | Description | Exemple |
|---------|-------------|---------|
| **Timestamp** | Date et heure de l'événement | `2024-01-15 10:23:45` |
| **Lab** | Nom du serveur/laboratoire | `server01` |
| **Service** | Service concerné | `sshd` |
| **PID** | Process ID | `12345` |
| **IP** | Adresse IP source | `192.168.1.100` |
| **User** | Nom d'utilisateur | `root` |
| **EventCode** | Code de l'événement | `AUTH_FAILED` |
| **Message** | Message détaillé du log | `Failed password for root...` |

---

## 🚀 Déploiement

### Streamlit Community Cloud

L'application est déployée sur Streamlit Community Cloud et accessible publiquement.

**URL de l'application :** [À compléter après déploiement]

### Déployer Votre Propre Instance

1. Forkez ce repository
2. Connectez-vous sur [share.streamlit.io](https://share.streamlit.io)
3. Créez une nouvelle app en sélectionnant votre fork
4. Configurez :
   - **Repository :** `votre-username/ssh_monitor`
   - **Branch :** `main`
   - **Main file :** `app.py`
5. Cliquez sur "Deploy!"

---

## 🐛 Dépannage

### Problème : "Aucune donnée géographique valide"
**Solution :** Vérifiez que la géolocalisation est activée et que le fichier GeoLite2-City.mmdb a été téléchargé.

### Problème : "Erreur de lecture CSV"
**Solution :** Vérifiez que votre fichier utilise le séparateur `;` et contient les 8 colonnes attendues.

### Problème : Application lente avec gros fichiers
**Solution :** Activez l'échantillonnage personnalisé et limitez à 50 000 lignes.

### Problème : Cache obsolète
**Solution :** Cliquez sur "Vider le cache" dans la barre latérale.

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## 👤 Auteur

**Damien POLINSKY**
- GitHub: [@Voldemort54](https://github.com/Voldemort54)
- Email: damien54500@hotmail.fr

---

## 🙏 Remerciements

- **MaxMind** pour la base de données GeoLite2
- **Streamlit** pour le framework web
- **Plotly** pour les visualisations interactives

---

## 📊 Statistiques du Projet

![GitHub repo size](https://img.shields.io/github/repo-size/Voldemort54/ssh_monitor)
![GitHub last commit](https://img.shields.io/github/last-commit/Voldemort54/ssh_monitor)
![GitHub stars](https://img.shields.io/github/stars/Voldemort54/ssh_monitor?style=social)

---

**Développé avec ❤️ pour la sécurité informatique**
