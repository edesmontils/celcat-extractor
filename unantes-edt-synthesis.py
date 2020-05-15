#!/usr/bin/env python3

from ics import Calendar, Event
from functools import reduce
import requests
import re
import sys
from typing import Optional, Iterator, List, Any, Dict
import datetime

import csv
import os.path
import io

import pprint as pp
import argparse

import unicodedata

# Test sur l'interpréteur python3
"""
import requests
from ics import Calendar, Event
req = requests.get("https://edt.univ-nantes.fr/sciences/s85976.ics")
i = req.text
cal = Calendar(i)
"""

def existFile(f):
    return os.path.isfile(f)
def existDir(d):
    return os.path.exists(d)

def getPerso():

    personnel = {}

    if not existFile('personnels.csv') :
        personnel_dpt = {}
        if existFile('Liste_Permanents_2019-2020.csv') :
            with open('Liste_Permanents_2019-2020.csv', 'r') as csvfile:
                dct = csv.DictReader(csvfile, delimiter=';')
                for row in dct:
                    nom = ''.join((c for c in unicodedata.normalize('NFD', row['NOM'].strip()) if unicodedata.category(c) != 'Mn'))
                    prenom = ''.join((c for c in unicodedata.normalize('NFD', row['PRENOM'].strip()) if unicodedata.category(c) != 'Mn'))
                    personnel_dpt[nom+', '+prenom] = [nom, prenom, row['STATUT'].strip()]

        # Get page with all names and urls
        url: str = "https://edt.univ-nantes.fr/sciences/sindex.html"
        req = requests.get(url)
        if req.status_code == 200:
            page_content: str = req.text

            # Find id in there
            fda = re.findall(r'<option value="(.*)\.html">(.*), (.*)</option>', page_content, re.MULTILINE)
            if not fda is None:
                file = 'personnels.csv'
                print('Saving ',file)
                try:
                    with open(file, "w", encoding='utf-8') as f:
                        fn = ['id', 'Nom', 'Prénom','Statut']
                        writer = csv.DictWriter(f, fieldnames=fn, delimiter='\t')
                        writer.writeheader()
                        for c in fda:
                            nom = ''.join((c for c in unicodedata.normalize('NFD', c[1].strip()) if unicodedata.category(c) != 'Mn'))
                            prenom = ''.join((c for c in unicodedata.normalize('NFD', c[2].strip()) if unicodedata.category(c) != 'Mn'))
                            nomc = nom+', '+prenom
                            if nomc in personnel_dpt.keys():
                                p = personnel_dpt[nomc]
                                stt = p[2].upper()
                            else: 
                                stt = 'AUTRE'
                            s = {'id': c[0], 'Nom': nom, 'Prénom':prenom, 'Statut':stt}
                            personnel[nomc] = [ nom, prenom, stt]
                            writer.writerow(s)
                    print('saved')
                except KeyboardInterrupt:
                    print('Interupted') 
        else:
            print('Impossible de récupérer le référentiel des personnels')
    else:
        with open('personnels.csv', 'r', encoding='utf-8') as csvfile:
            dct = csv.DictReader(csvfile, delimiter='\t')
            for row in dct:
                nom = row['Nom']
                prenom = row['Prénom']
                personnel[nom+', '+prenom] = [nom, prenom, row['Statut']]        
    return personnel

def getModule():
    if not existFile('modules.csv') :
        # Get page with all names and urls
        url: str =  "https://edt.univ-nantes.fr/sciences/mindex.html" #'https://edt.univ-nantes.fr/sciences/d359754mindex.html' #
        req = requests.get(url)
        if req.status_code == 200:
            page_content: str = req.text

            # Find id in there
            fda = re.findall(r'<option value="(.*)\.html">(.*), (.*)</option>',
                              page_content, re.MULTILINE)

            if not fda is None:
                file = 'modules.csv'
                print('Saving ',file)

                try:
                    with open(file, "w", encoding='utf-8') as f:
                        fn = ['id', 'Nom', 'Code']
                        writer = csv.DictWriter(f, fieldnames=fn, delimiter='\t')
                        writer.writeheader()
                        for c in fda:
                            s = {'id': c[0], 'Nom': c[1], 'Code':c[2]}
                            writer.writerow(s)
                    print('saved')
                except KeyboardInterrupt:
                    print('Interupted') 
        else:
            print("Impossible de récupérer le référentiel des modules")

def getGroupe():
    if not existFile('groupes.csv') :
        # Get page with all names and urls
        url: str = "https://edt.univ-nantes.fr/sciences/gindex.html"
        req = requests.get(url)
        if req.status_code == 200:
            page_content: str = req.text

            # Find id in there
            fda = re.findall(r'<option value="(.*)\.html">(.*)</option>',
                              page_content, re.MULTILINE)

            if not fda is None:
                file = 'groupes.csv'
                print('Saving ',file)

                try:
                    with open(file, "w", encoding='utf-8') as f:
                        fn = ['id', 'Code']
                        writer = csv.DictWriter(f, fieldnames=fn, delimiter='\t')
                        writer.writeheader()
                        for c in fda:
                            s = {'id': c[0], 'Code': c[1]}
                            writer.writerow(s)
                    print('saved')
                except KeyboardInterrupt:
                    print('Interupted') 
        else:
            print("Impossible de récupérer le référentiel des groupes")

class Creneau :
    def __init__(self, icsEvent):
        self.ics = icsEvent
        self.duree = icsEvent.duration
        self.begin = icsEvent.begin.format('YYYY-MM-DD')
        self.end = icsEvent.end.format('YYYY-MM-DD')

        p = re.search(r'Personnel : (.*)\n', icsEvent.description, re.MULTILINE)
        if p is not None : 
            self.personnel = []
            lp = [i.strip() for i in p.group(1).split(",")]
            n = len(lp) // 2
            for i in range(n):
                self.personnel.append(lp[2*i]+', '+lp[2*i+1])
        else: self.personnel = []

        g =  re.search(r'Groupe : (.*)\n',icsEvent.description, re.MULTILINE)
        if g is not None : 
            self.groupe = [i.strip() for i in g.group(1).split(",")]
        else: self.groupe = []

        s =  re.search(r'Salle : (.*)\n',icsEvent.description, re.MULTILINE)
        if s is not None : 
            self.salles = [i.strip() for i in s.group(1).split(",")]
        else: self.salles = []

        t = re.search(r'^(.*?) -', icsEvent.name)
        self.type = t.group(1)

        r =  re.search(r'Remarques : (.*)',icsEvent.description, re.MULTILINE)
        if r is not None : 
            self.remarque = r.group(1)
        else: self.remarque = 'None'

        m = re.search(r'Matière : (.*) \((.*)\)\n',icsEvent.description, re.MULTILINE)
        if m is not None : 
            self.matiere = m.group(1)
            if m.group(2) is not None :
                self.code_matiere = m.group(2)
            else:
                self.code_matiere = "m*"+m.group(1).replace(" ","").replace(":","").replace("-","").replace("(","").replace(")","").replace("'","").upper()#'Sans_code'
        else:
            self.matiere = 'Sans_code'    
            self.code_matiere =  "r*"+self.remarque.replace(" ","").replace(":","").replace("-","").replace("(","").replace(")","").replace("'","")[:10].upper()#'Sans_code'


        if self.code_matiere == 'Sans_code' :
            print("Module sans code")
            print(icsEvent.name)
            print(icsEvent.description)
            print()

    def __str__(self):
        s = "---\n"+"personnel:"+self.personnel+"\n matière:"+self.matiere+"\n"
        return(s)

def load(ics, debut, fin):
    ok = False
    fileName = "./tmp/"+ics+".ics"
    url = "https://edt.univ-nantes.fr/sciences/"+ics+".ics"

    if existFile(fileName):
        print("Read saved ics")
        file = open(fileName,"r")
        text = file.read()
        file.close()
        if text != '': 
            ok = True
        else:
            print('saved but empty ics')
    else: 
        print("Read UN ics")
        req = requests.get(url)
        if req.status_code == 200:
            ok = True
            file = open(fileName,"w")
            file.write(req.text)
            file.close()
            text = req.text
        else:
            file = open(fileName,"w")
            file.write('')
            file.close()            
    if ok:
        print("Analyse de : <"+url+">")
        ics_content: str = text
        cal = Calendar(ics_content)
        lc = []
        lp = []
        lm = []
        lg = []
        for e in list(cal.timeline):
            ev = Creneau(e)

            ok = True
            if debut is not None :
                if ev.begin < debut : ok = False
            if fin is not None :
                if ev.end > fin : ok = False

            if ok :
                lc.append(ev)
                if ev.personnel is not None :
                    lp += [p for p in ev.personnel if p not in lp]
                if ev.code_matiere is not None :
                    if ev.code_matiere not in lm: lm.append(ev.code_matiere)
                else: 
                    if "Sans_code" not in lm: lm.append('Sans_code')
                if ev.groupe is not None :
                    lg += [g for g in ev.groupe if g not in lg ]

        return lc, lp, lm, lg
    else:
        print(url + " introuvable !")
        return None, None, None, None

def analyse(lev, code):
    sorted_events: Dict[str, List[Creneau]] = {}
    for c in lev:
        if c.type is None: evt = "autre"
        else: evt = c.type

        if not evt in sorted_events : sorted_events[evt] = []
        sorted_events[evt].append(c)

    print()
    print("=== Volume horaire pour « " + code + " »")
    for ct in sorted_events:
        evts = sorted_events[ct]
        # Sum durations for events of course type
        course_type_total = reduce(lambda d1, d2: d1 + d2,
                                   map(lambda e: e.duree, evts), datetime.timedelta(0))

        # Format in hours only
        format_string = "{:.2f}"
        course_type_total_hours = format_string.format(course_type_total.total_seconds() / 3600)

        # Output
        print(f'− {ct} : {str(course_type_total)} ({str(course_type_total_hours)})')    


def getModules(args, match_np, type_list):
    lcf = []
    if (args.nom is not None) and (args.prenom is not None):
        test = lambda rx, ry, x, y : match_np.match(rx+', '+ry) # x==rx and y==ry
    else: test = lambda rx, ry, x, y : True
    with open('personnels.csv', 'r') as csvfile:
        dct = csv.DictReader(csvfile, delimiter='\t')
        for row in dct:
            if test(row['Nom'], row['Prénom'], args.nom, args.prenom) :
                (lc, lp, lm, lg) = load(row['id'])
                if lc is not None:
                    lcf += [c.code_matiere for c in lc if (c.type in type_list)]

    return list(set(lcf))

#==================================================
#==================================================
#==================================================
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Celcat explorer')
    parser.add_argument("-n", "--nom", default=None, dest="nom", help="Nom d'une personne (en majuscules)")
    parser.add_argument("-p", "--prenom", default=None, dest="prenom", help="Prenom d'une personne (minuscules, sauf première lettre)")
    parser.add_argument("-m", "--module", default=None, dest="module", help="Code du module")
    parser.add_argument("-g", "--groupe", default=None, dest="groupe", help="Code du groupe")
    parser.add_argument("-bm", action="store_true", help="Recherche par module (-m XXX obligatoire)")
    parser.add_argument("-bp", action="store_true", help="Recherche par personne (-n NNN et -p PPP obligatoires)")
    parser.add_argument("-bg", action="store_true", help="Recherche par groupe (-g GGG obligatoire)")

    parser.add_argument("-resp", action="store_true", help="Des modules où la personne donne des cours (si -bm, -p et -n)" )

    parser.add_argument("-d", "--debut", default=None, dest="debut", help="date de début des créneaux à analyser (AAAA-MM-JJ)" )    
    parser.add_argument("-f", "--fin", default=None, dest="fin", help="date de fin des créneaux à analyser (AAAA-MM-JJ)" ) 

    args = parser.parse_args()

    print("Reconstruction des CSV")

    personnel_dpt = getPerso()
    getModule()
    getGroupe()

    if not existDir('./tmp'):
        os.makedirs('./tmp')

    print("Préparation des données")



    if (args.nom is not None) and (args.prenom is not None):
        args.nom = args.nom.upper()
        args.prenom = args.prenom.capitalize()
        match_np = re.compile(args.nom+', '+args.prenom)
    else: match_np = re.compile('.*')

    if args.module is not None:
        #args.module = args.module.upper()
        match_m = re.compile(args.module)
    else: match_m = re.compile('.*')

    if args.groupe is not None:
        #args.groupe = args.module.upper()
        match_g = re.compile(args.groupe)
    else: match_g = re.compile('.*')

    if args.bm and args.resp and (args.nom is not None) and (args.prenom is not None) :
        lcf = getModules(args, match_np, 'CM info')
    else: lcf = []

    print()

    if args.bp:
        print("=========================")
        print("= Analyse par personnel =")
        print("=========================\n")
        if (args.nom is not None) and (args.prenom is not None):
            test = lambda rx, ry, x, y : match_np.match(rx+', '+ry) # x==rx and y==ry
        else: test = lambda rx, ry, x, y : True
        with open('personnels.csv', 'r') as csvfile:
            dct = csv.DictReader(csvfile, delimiter='\t')
            for row in dct:
                if test(row['Nom'], row['Prénom'], args.nom, args.prenom) :
                    nomp = row['Nom']+', '+row['Prénom']
                    if nomp in personnel_dpt.keys(): statut =  nomp+' ('+personnel_dpt[nomp][2]+')'
                    else: statut = nomp 
                    print("==================================================")
                    print("==> Recherche pour : "+statut)
                    (lc, lp, lm, lg) = load(row['id'], args.debut, args.fin)
                    if lc is not None:
                        if args.module is not None :
                            for m in lm :
                                if match_m.match(m) is not None : #m == args.module : 
                                    if args.groupe is not None :
                                        for g in lg :
                                            if match_g.match(g) is not None :
                                                analyse([c for c in lc if (m == c.code_matiere) and (g in c.groupe) ], m+'|'+g)
                                    else: analyse([c for c in lc if m == c.code_matiere], m)                            
                        elif  args.groupe is not None :
                            for g in lg :
                                if match_g.match(g) is not None : #m == args.module : 
                                    analyse([c for c in lc if g in c.groupe], g)
                        else: 
                            for m in lm :
                                analyse([c for c in lc if m == c.code_matiere], m)
                    print("==================================================\n\n")
            print()

    if args.bm:
        print("======================")
        print("= Analyse par module =")
        print("======================\n")
        if args.module is not None:
            test = lambda rx, x : match_m.match(rx) is not None # x==rx
        else: test = lambda rx, x : True
        with open('modules.csv', 'r') as csvfile:
            dct = csv.DictReader(csvfile, delimiter='\t')
            for row in dct:
                if args.resp and (args.nom is not None) and (args.prenom is not None) and (row['Code'] in lcf):
                    print("=================== ", args.nom, ", ",args.prenom ,"  ===============================")
                    print("==> Recherche pour : "+row['Nom'])
                    print("Code : "+row['Code'])
                    (lc, lp, lm, lg) = load(row['id'], args.debut, args.fin)
                    for p in lp : analyse([c for c in lc if p in c.personnel ], p)
                    print("==================================================\n\n")
                elif not(args.resp) and test(row['Code'], args.module) : 
                    print("==================================================")
                    print("==> Recherche pour : "+row['Nom'])
                    print("Code : "+row['Code'])
                    (lc, lp, lm, lg) = load(row['id'], args.debut, args.fin)
                    if lc is not None:
                        if (args.nom is not None) and (args.prenom is not None):
                            for p in lp :
                                if match_np.match(p) is not None : #p == args.nom+', '+args.prenom: 
                                    if p in personnel_dpt.keys(): statut =  p+' ('+personnel_dpt[p][2]+')'
                                    else: statut = p 
                                    if args.groupe is not None : 
                                        for g in lg :
                                            if match_g.match(g) is not None :
                                                analyse([c for c in lc if (p in c.personnel) and (g in c.groupe) ], statut+'|'+g)
                                    else: analyse([c for c in lc if p in c.personnel ], statut)
                        elif  args.groupe is not None :
                            for g in lg :
                                if match_g.match(g) is not None : #m == args.module : 
                                    analyse([c for c in lc if g in c.groupe], g)
                        else: 
                            for p in lp :
                                if p in personnel_dpt.keys(): statut =  p+' ('+personnel_dpt[p][2]+')'
                                else: statut = p
                                analyse([c for c in lc if p in c.personnel ], statut)


                    print("==================================================\n\n")
            print()

    if args.bg: 
        print("======================")
        print("= Analyse par groupe =")
        print("======================\n")
        if args.groupe is not None:
            test = lambda rx, x : match_g.match(rx) is not None #  x==rx
        else: test = lambda rx, x : True
        with open('groupes.csv', 'r') as csvfile:
            dct = csv.DictReader(csvfile, delimiter='\t')
            for row in dct:
                if test(row['Code'], args.groupe) : 
                    print("==================================================")
                    print("==> Recherche pour : "+row['Code'])
                    (lc, lp, lm, lg) = load(row['id'], args.debut, args.fin)
                    if lc is not None:
                        if (args.nom is not None) and (args.prenom is not None):
                            for p in lp :
                                if match_np.match(p) is not None : # p == args.nom+', '+args.prenom: 
                                    if p in personnel_dpt.keys(): statut =  p+' ('+personnel_dpt[p][2]+')'
                                    else: statut = p
                                    if args.module is not None :
                                        for m in lm :
                                            if match_m.match(m) is not None :
                                                analyse([c for c in lc if (m == c.code_matiere) and (p in c.personnel) ], statut+'|'+m)
                                    else: analyse([c for c in lc if p in c.personnel ], statut)
                        elif  args.module is not None :
                            for m in lm :
                                if match_m.match(m) is not None : #m == args.module : 
                                    analyse([c for c in lc if m == c.code_matiere], m)
                        else: 
                            for p in lp :
                                if p in personnel_dpt.keys(): statut =  p+' ('+personnel_dpt[p][2]+')'
                                else: statut = p
                                analyse([c for c in lc if p in c.personnel ], statut)
                    print("==================================================\n\n")
            print()
    print("Fin")