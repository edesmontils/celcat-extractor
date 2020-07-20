# Extracteur d'informations Celcat Université de Nantes

Permet de récupérer dans l'EDT en ligne le volume horaire d'un intervenant sur une UE à partir du Celcet de l'Université de Nantes.

Il est basé sur l'outil https://gitlab.univ-nantes.fr/bousse-e/edt-extractor 


## Prérequis

```
$ pip3 install --user ics requests argparse lxml flask
```

Documentation :

  * https://icspy.readthedocs.io/en/stable/
  
  * https://arrow.readthedocs.io/en/latest/

## Installation 

```
git clone https://github.com/edesmontils/celcat-extractor.git
cd celcat-extractor
```

## Usage

### En ligne de commande

```
usage: celcat_extractor.py [-h] [-n NOM] [-p PRENOM] [-m MODULE]
                                [-g GROUPE] [-bm] [-bp] [-bg] [-resp]
                                [-d DEBUT] [-f FIN]

Celcat explorer

optional arguments:
  -h, --help            show this help message and exit
  -n NOM, --nom NOM     Nom d'une personne (en majuscules)
  -p PRENOM, --prenom PRENOM
                        Prenom d'une personne (minuscules, sauf première
                        lettre)
  -m MODULE, --module MODULE
                        Code du module
  -g GROUPE, --groupe GROUPE
                        Code du groupe
  -bm                   Recherche par module (-m XXX obligatoire)
  -bp                   Recherche par personne (-n NNN et -p PPP obligatoires)
  -bg                   Recherche par groupe (-g GGG obligatoire)
  -resp                 Des modules où la personne donne des cours (si -bm, -p
                        et -n)
  -d DEBUT, --debut DEBUT
                        date de début des créneaux à analyser (AAAA-MM-JJ)
  -f FIN, --fin FIN     date de fin des créneaux à analyser (AAAA-MM-JJ)
```

Exemple :
```
$ python3 celcat_extractor.py -bp -resp -n 'Desmontils' -p '.*'    
Reconstruction des CSV
Préparation des données

=========================
= Analyse par personnel =
=========================

==================================================
==> Recherche pour : DESMONTILS Emmanuel
Read saved ics
Analyse de : <https://edt.univ-nantes.fr/sciences/s85976.ics>

=== Volume horaire pour « X1IP020 »
− CM info : 12:00:00 (12.00)
− TD info : 20:00:00 (20.00)
− TP info : 8:00:00 (8.00)
− Contrôle continu : 2:50:00 (2.83)
− Contrôle continu TD : 2:00:00 (2.00)

=== Volume horaire pour « X1IM020 »
− CM info : 12:00:00 (12.00)
− TD info : 20:00:00 (20.00)
− TP info : 8:00:00 (8.00)

=== Volume horaire pour « X21I040 »
− CM info : 10:40:00 (10.67)
− Contrôle continu : 1:20:00 (1.33)

=== Volume horaire pour « X31I110 »
− TD info : 8:00:00 (8.00)

=== Volume horaire pour « r*FSU21APROG »
− Formation continue : 1 day, 3:00:00 (27.00)

=== Volume horaire pour « r*BASEDEDONN »
− TD info : 12:40:00 (12.67)
− Contrôle continu : 1:30:00 (1.50)

=== Volume horaire pour « X2IM030 »
− CM info : 6:40:00 (6.67)
− TD info : 9:20:00 (9.33)
− Contrôle continu : 1:20:00 (1.33)

=== Volume horaire pour « X2IP030 »
− CM info : 5:20:00 (5.33)
− TD info : 10:40:00 (10.67)
− Contrôle continu : 1:20:00 (1.33)

=== Volume horaire pour « r*JOURNÉEENS »
− Divers : 11:30:00 (11.50)
==================================================



Fin
```

### En serveur Flask


```
usage: celcat-extractor.py  -w
```

Les caractéristiques du serveur Flask se trouvent dans de fichier 'config.cfg'. Il est de la forme :
```
[File Names]
Teachers = personnels.csv
Courses = modules.csv
Groups = groupes.csv
ComputerScience_teachers = xxxx.csv

[Dir Names]
Cache_dir = ./tmp/

[Web]
Celcat_url = https://edt.univ-nantes.fr/sciences/
host=0.0.0.0
port=32769

[Autre]
debug=False
duree=7
```

### En serveur Gunicorn

Faire au préalable :
```
$ pip3 install --user gunicorn
```

Les caractristiques du serveur se trouvent dans le fichier de configuration 'gunicorn_cfg.py'. Il est de la forme :
```
bind='0.0.0.0:32769'

workers=2

pidfile='gu.pid'
daemon=True

accesslog='gunicorn_access.log'
errorlog='gunicorn_error.log'

capture_output=True
loglevel='debug'
reload=True

enable_stdio_inheritance=True

proc_name='celcat_ext'
```

Ensuite, il suffit de lancer le serveur avec la commande :
```
$ gunicorn -c gunicorn_cfg.py celcat-extractor:app
```

## Tests

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/edesmontils/celcat-extractor.git/master)
