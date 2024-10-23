# Surveillance des Prix des Livres d'Occasion Rares

Ce projet est un programme de web scraping développé pour surveiller les prix des livres d'occasion rares vendus par le site **OldBooks Finder**. Le programme extrait les informations tarifaires et de disponibilité des livres et les stocke dans un fichier CSV.

## Prérequis

Avant de pouvoir exécuter le programme, assurez-vous d'avoir installé les dépendances nécessaires. Vous pouvez les installer en utilisant le fichier `requirements.txt`.

### Installation de l'environnement virtuel

Sous MacOS/Linux :
```sh
python3 -m venv env
```

Sous Windows :
```sh
python -m venv env
```
### Activer l'environnement

```
source env/bin/activate
```


### Installation des dépendances

Pour installer les dépendances à partir du fichier `requirements.txt`, exécutez la commande suivante :
```sh
pip install -r requirements.txt
```

### Utilisation du programme

Pour utiliser le programme permettant d'obtenir plusieurs information sur différents livres, éxécuter la commande suivante:

Sous MacOS/Linux :
```sh
python3 app.py
```

Sous Windows :
```sh
python app.py
```