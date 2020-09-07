#!/usr/bin/env python3

from ics import Calendar, Event
from functools import reduce
import requests # http://docs.python-requests.org/en/master/user/quickstart/
import re
import sys
from typing import Optional, Iterator, List, Any, Dict
import datetime
from datetime import date

import csv
import os.path
import io

import pprint as pp
import argparse
from configparser import ConfigParser, ExtendedInterpolation

from flask import Flask, render_template, request, jsonify, url_for # http://flask.pocoo.org/docs/0.12/
# from flask_cas import CAS, login_required
from lxml import etree  # http://lxml.de/index.html#documentation

import unicodedata

# Test sur l'interpréteur python3
"""
import requests
from ics import Calendar, Event
req = requests.get("https://edt.univ-nantes.fr/sciences/s85976.ics")
i = req.text
cal = Calendar(i)
"""
#==================================================
#============ Tools ===============================
#==================================================

def existFile(f):
    return os.path.isfile(f)

def existDir(d):
    return os.path.exists(d)


#== changer date d'un fichier
# touch -t 2006010000 tmp/s88581.ics
#==
def modifDate(f):
    return date.fromtimestamp(os.stat(f).st_mtime)

def daysOld(f) :
    n = date.today()
    d = modifDate(f)
    delta = n-d
    return delta.days

#==================================================
#============ Web =================================
#==================================================

class Context(object):
    """docstring for Context"""

    def __init__(self):
        super(Context, self).__init__()
        self.host = '0.0.0.0'
        self.port = 80
        self.tree = None
        self.debug = False
        self.version = '1.0'
        self.name = 'Name'
        self.personnel_dpt = {}
        self.tab_module = {}
        self.cfg = None

    def start(self):
        pass

    def stop(self):
        pass

    def loadWebConfig(self, configFile) :
        if existFile(configFile) :
            XMLparser = etree.XMLParser(recover=True, strip_cdata=True)
            self.tree = etree.parse(configFile, XMLparser)
            if existFile('web-config.dtd') :
                #---
                dtd = etree.DTD('web-config.dtd')
                assert dtd.validate(self.tree), '%s non valide au chargement : %s' % (
                    configFile, dtd.error_log.filter_from_errors()[0])
                #---
            self.version = self.tree.getroot().get('version')
            self.name = self.tree.getroot().get('name')
            if self.tree.getroot().get('debug') == 'false':
                self.debug = False
            else:
                self.debug = True
        else:
            pass

ctx = Context()

#==================================================

# Initialize the Flask application
app = Flask(__name__)

# //authentification CAS
# define("C_CASServer","cas-ha.univ-nantes.fr") ;
# define("C_CASPort",443) ;
# define("C_CASpath","/esup-cas-server") ;

# set the secret key.  keep this really secret:
app.secret_key = '\x0ctD\xe3g\xe1XNJ\x86\x02\x03`O\x98\x84\xfd,e/5\x8b\xd1\x11'

# cas = CAS(app)
# app.config['CAS_SERVER'] = 'https://cas-ha.univ-nantes.fr'
# app.config['CAS_PORT'] = 443
# app.config['CAS_PATH'] = '/esup-cas-server'
# app.config['CAS_AFTER_LOGIN'] = 'route_root'


@app.route('/')
# @login_required
def index():
    # print(url_for('static',filename='js/prototype.js',_external=True))
    return render_template(
        'index.html',
        # username = cas.username,
        # display_name = cas.attributes['cas:displayName'],
        nom_appli=ctx.name, 
        version=ctx.version,
        listeMembres=[ctx.personnel_dpt[x] for x in ctx.personnel_dpt if ctx.personnel_dpt[x][2]!='AUTRE']
    )

@app.route('/news')
def news():
    listeMessages = ctx.tree.getroot().findall('listeMessages/message')
    d = list()
    for message in listeMessages:
        r = dict()
        titre = message.get('titre')
        date = message.get('date')
        auteur = message.get('auteur')
        r['titre'] = titre
        r['post'] = "-> Le "+date+" par "+auteur
        s = ''
        for cont in message:
            s += etree.tostring(cont, encoding='utf8').decode('utf8')
        r['s'] = s
        d.append(r)
    return jsonify(result=d)


@app.route('/mentions')
def mentions():
    m = ctx.tree.getroot().find('mentions')
    s = ''
    for cont in m:
        if cont.text is not None:
            s += etree.tostring(cont, encoding='utf8').decode('utf8')
    return s


@app.route('/apropos')
def apropos():
    m = ctx.tree.getroot().find('aPropos')
    s = ''
    for cont in m:
        if cont.text is not None:
            s += etree.tostring(cont, encoding='utf8').decode('utf8')
    return s

@app.route('/end')
def end():
    return "<p>Bases purgées...</p>"

@app.route('/help')
def help():
    m = ctx.tree.getroot().find('aides')
    s = ''
    for cont in m:
        if cont.text is not None:
            s += etree.tostring(cont, encoding='utf8').decode('utf8')
    return s

@app.route('/envoyer', methods=['post'])
def envoyer():
    nom = request.form['nom']
    s = 'error'
    tab = 'topo '+nom
    print(request.form)

    if request.form['type']=='bp': 
        print('BP received')
        tab = '<pre>\n' + doBP(ctx.cfg, request.form['nom'], request.form['prenom'], 
                        request.form['course'], request.form['groupe'], request.form['debut'], 
                        request.form['fin'], ctx.personnel_dpt, ctx.tab_module) + '</pre>'
        s = 'ok'
        #print(tab)
    elif request.form['type']=='bm': 
        print('BM received')
        tab = '<pre>\n' + doBM(ctx.cfg, request.form['nom'], request.form['prenom'], 
                        request.form['course'], request.form['groupe'], 
                        request.form['resp']=='true', request.form['debut'], 
                        request.form['fin'], ctx.personnel_dpt, ctx.tab_module) + '</pre>'
        s = 'ok'
        #print(tab)
    elif request.form['type']=='bg': 
        print('BG received')
        tab = '<pre>\n' + doBG(ctx.cfg, request.form['nom'], request.form['prenom'], 
                        request.form['course'], request.form['groupe'], 
                        request.form['debut'], 
                        request.form['fin'], ctx.personnel_dpt, ctx.tab_module) + '</pre>'
        s = 'ok'
        #print(tab)
    else: print('Type inconnu')
    d = dict({'ok': s != 'Error', 'val': tab})
    return jsonify(result=d)

@app.route('/bp/<nom>/<prenom>')
def bp(nom, prenom):
    s = doBP(ctx.cfg, nom, prenom, '', '', '', '', ctx.personnel_dpt, ctx.tab_module)
    d = "<pre>\n"+s+"</pre>"
    return d 

@app.route('/bpt/<nom>/<prenom>/<deb>/<fin>')
def bpt(nom, prenom, deb, fin):
    s = doBP(ctx.cfg, nom, prenom, '', '', deb, fin, ctx.personnel_dpt, ctx.tab_module)
    d = "<pre>\n"+s+"</pre>"
    return d 

@app.route('/bm/<course>')
def bm(course):
    s = doBM(ctx.cfg, '', '', course, '', False, '', '', ctx.personnel_dpt, ctx.tab_module)
    d = "<pre>\n"+s+"</pre>"
    return d 

@app.route('/bmt/<course>/<deb>/<fin>')
def bmt(course, deb, fin):
    s = doBM(ctx.cfg, '', '', course, '', False, deb, fin, ctx.personnel_dpt, ctx.tab_module)
    d = "<pre>\n"+s+"</pre>"
    return d 

@app.route('/bmr/<nom>/<prenom>')
def bmr(nom, prenom):
    s = doBM(ctx.cfg, nom, prenom, '', '', True, '', '', ctx.personnel_dpt, ctx.tab_module)
    d = "<pre>\n"+s+"</pre>"
    return d 

@app.route('/bmrt/<nom>/<prenom>/<deb>/<fin>')
def bmrt(nom, prenom,deb,fin):
    s = doBM(ctx.cfg, nom, prenom, '', '', True, deb, fin, ctx.personnel_dpt, ctx.tab_module)
    d = "<pre>\n"+s+"</pre>"
    return d 

@app.route('/bg/<groupe>')
def bg(groupe):
    s = doBG(ctx.cfg, '', '', '', groupe, '', '', ctx.personnel_dpt, ctx.tab_module)
    d = "<pre>\n"+s+"</pre>"
    return d 

@app.route('/bgt/<groupe>/<deb>/<fin>')
def bgt(groupe, deb, fin):
    s = doBG(ctx.cfg, '', '', '', groupe, deb, fin, ctx.personnel_dpt, ctx.tab_module)
    d = "<pre>\n"+s+"</pre>"
    return d 

#==================================================
#============ Functions ===========================
#==================================================

def getPerso(cfg):

    personnel = {}

    if not existFile(cfg['File Names']['Teachers']) :
        personnel_dpt = {}
        if existFile(cfg['File Names']['ComputerScience_teachers']) :
            with open(cfg['File Names']['ComputerScience_teachers'], 'r') as csvfile:
                dct = csv.DictReader(csvfile, delimiter=';')
                for row in dct:
                    nom = ''.join((c for c in unicodedata.normalize('NFD', row['NOM'].strip()) if unicodedata.category(c) != 'Mn'))
                    prenom = ''.join((c for c in unicodedata.normalize('NFD', row['PRENOM'].strip()) if unicodedata.category(c) != 'Mn'))
                    personnel_dpt[nom+', '+prenom] = [nom, prenom, row['STATUT'].strip(),row['EDT']]

        # Get page with all names and urls
        # https://edt.univ-nantes.fr/chantrerie-gavy/sindex.html
        url = cfg['Web']['Celcat_url']+"sindex.html"
        req = requests.get(url)
        if req.status_code == 200:
            page_content = req.text

            # Find id in there
            fda = re.findall(r'<option value="(.*)\.html">(.*), (.*)</option>', page_content, re.MULTILINE)
            if not fda is None:
                file = cfg['File Names']['Teachers']
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
                            urlservice = c[0] # cfg['Web']['Celcat_url']+c[0]+".ics"
                            s = {'id': urlservice, 'Nom': nom, 'Prénom':prenom, 'Statut':stt}
                            personnel[nomc] = [ nom, prenom, stt, urlservice]
                            writer.writerow(s)
                        # Ajout d'autres étudiants (Polytech par exemple)
                        # todo
                        for p in personnel_dpt.keys() :
                            if p not in personnel : 
                                desc = personnel_dpt[p]
                                s = {'id': desc[3], 'Nom': desc[0], 'Prénom':desc[1], 'Statut':desc[2]}
                                personnel[p] = [ desc[0], desc[1], desc[2], desc[3]]
                                writer.writerow(s)
                    print('saved')
                except KeyboardInterrupt:
                    print('Interupted') 
        else:
            print('Impossible de récupérer le référentiel des personnels')
    else:
        with open(cfg['File Names']['Teachers'], 'r', encoding='utf-8') as csvfile:
            dct = csv.DictReader(csvfile, delimiter='\t')
            for row in dct:
                nom = row['Nom']
                prenom = row['Prénom']
                personnel[nom+', '+prenom] = [nom, prenom, row['Statut'],row['id']]        
    return personnel

def getModule(cfg):
    module = {}
    if not existFile(cfg['File Names']['Courses']) :
        # Get page with all names and urls
        url =  cfg['Web']['Celcat_url']+"mindex.html" #'https://edt.univ-nantes.fr/sciences/d359754mindex.html' #
        req = requests.get(url)
        if req.status_code == 200:
            page_content = req.text

            # Find id in there
            fda = re.findall(r'<option value="(.*)\.html">(.*), (.*)</option>',
                              page_content, re.MULTILINE)

            if not fda is None:
                file = cfg['File Names']['Courses']
                print('Saving ',file)

                try:
                    with open(file, "w", encoding='utf-8') as f:
                        fn = ['id', 'Nom', 'Code']
                        writer = csv.DictWriter(f, fieldnames=fn, delimiter='\t')
                        writer.writeheader()
                        for c in fda:

                            # version edt-standard
                            s = {'id': c[0], 'Nom': c[1], 'Code':c[2]}
                            # --------------------

                            # version edt-bis
                            # s = {'id': c[0], 'Nom': c[2], 'Code':c[1]}
                            # --------------------

                            writer.writerow(s)
                            module[c[2]] = [c[1],c[0]]
                    print('saved')
                except KeyboardInterrupt:
                    print('Interupted') 
        else:
            print("Impossible de récupérer le référentiel des modules")
    else:
        with open(cfg['File Names']['Courses'], 'r', encoding='utf-8') as csvfile:
            dct = csv.DictReader(csvfile, delimiter='\t')
            for row in dct:
                module[row['Code']] = [row['Nom'],row['id']]        
    return module

def getGroupe(cfg):
    if not existFile(cfg['File Names']['Groups']) :
        # Get page with all names and urls
        url = cfg['Web']['Celcat_url']+"gindex.html"
        req = requests.get(url)
        if req.status_code == 200:
            page_content = req.text

            # Find id in there
            fda = re.findall(r'<option value="(.*)\.html">(.*)</option>',
                              page_content, re.MULTILINE)

            if not fda is None:
                file = cfg['File Names']['Groups']
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

        # version edt-standard
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
        # -------------------------

        # version edt-bis
        # m = re.search(r'Matière : (.*?) \((.*)\)\n',icsEvent.description, re.MULTILINE)
        # if m is not None : 
        #     self.matiere = m.group(2)
        #     if m.group(1) is not None :
        #         self.code_matiere = m.group(1)
        #     else:
        #         self.code_matiere = "m*"+m.group(2).replace(" ","").replace(":","").replace("-","").replace("(","").replace(")","").replace("'","").upper()#'Sans_code'
        # else:
        #     self.matiere = 'Sans_code'    
        #     self.code_matiere =  "r*"+self.remarque.replace(" ","").replace(":","").replace("-","").replace("(","").replace(")","").replace("'","")[:10].upper()#'Sans_code'
        # -------------------------- 

        if self.code_matiere == 'Sans_code' :
            print("Module sans code")
            print(icsEvent.name)
            print(icsEvent.description)
            print()

    def __str__(self):
        s = "---\n"+"personnel:"+self.personnel+"\n matière:"+self.matiere+"\n"
        return(s)

def load(cfg, ics, debut, fin):
    ok = False
    fileName = cfg['Dir Names']['Cache_dir']+ics+".ics"
    url = cfg['Web']['Celcat_url']+ics+".ics"

    if existFile(fileName) and daysOld(fileName) < int(cfg['Autre']['duree']) :
        print("Read saved ics ",daysOld(fileName))
        file = open(fileName,"r")
        text = file.read()
        file.close()
        if text != '': 
            ok = True
        else:
            print('saved but empty ics')
    else: 
        print("Read UN ics ")
        if not existFile(fileName) : print("Cached file does'nt exist")
        elif daysOld(fileName) >= int(cfg['Autre']['duree']) : print("Cached file too old : ",daysOld(fileName))
        req = requests.get(url)
        if req.status_code == 200:
            print('FST')
            ok = True
            file = open(fileName,"w")
            file.write(req.text)
            file.close()
            text = req.text
        else:
            url = "https://edt.univ-nantes.fr/chantrerie-gavy/"+ics+".ics"
            req = requests.get(url)
            if req.status_code == 200:
                print('PLT')
                ok = True
                file = open(fileName,"w")
                file.write(req.text)
                file.close()
                text = req.text            
            else:
                print('Not founded')
                file = open(fileName,"w")
                file.write('')
                file.close()            
    if ok:
        print("Analyse de : <"+url+">")
        ics_content = text
        cal = Calendar(ics_content)
        lc = []
        lp = []
        lm = []
        lg = []
        for e in list(cal.timeline):
            ev = Creneau(e)

            ok = True
            if debut is not '' :
                if ev.begin < debut : ok = False
            if fin is not '' :
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

        return lc, sorted(lp), sorted(lm), sorted(lg)
    else:
        print(url + " introuvable !")
        return None, None, None, None

def analyse(lev, code):
    #sorted_events: Dict[str, List[Creneau]] = {}
    sorted_events = {}
    for c in lev:
        if c.type is None: evt = "autre"
        else: evt = c.type

        if not evt in sorted_events : sorted_events[evt] = []
        sorted_events[evt].append(c)

    s = "\n === Volume horaire pour « "+ code + " »\n"
    for ct in sorted_events:
        evts = sorted_events[ct]
        # Sum durations for events of course type
        course_type_total = reduce(lambda d1, d2: d1 + d2,
                                   map(lambda e: e.duree, evts), datetime.timedelta(0))

        # Format in hours only
        format_string = "{:.2f}"
        course_type_total_hours = format_string.format(course_type_total.total_seconds() / 3600)

        # Output
        #s = s + f'− {ct} : {str(course_type_total)} ({str(course_type_total_hours)})' + "\n"
        s = s + '− '+str(course_type_total)+' ('+str(course_type_total_hours)+')' + "\n"

    return s


def getModulesInfo(cfg, nom, prenom, debut, fin, match_np, type_list):
    lcf = []
    if (nom is not '') and (prenom is not ''):
        test = lambda rx, ry, x, y : match_np.match(rx+', '+ry.upper()) # x==rx and y==ry
    else: test = lambda rx, ry, x, y : True
    with open(cfg['File Names']['Teachers'], 'r') as csvfile:
        dct = csv.DictReader(csvfile, delimiter='\t')
        for row in dct:
            if test(row['Nom'], row['Prénom'], nom, prenom) :
                (lc, lp, lm, lg) = load(cfg,row['id'],debut,fin)
                if lc is not None:
                    lcf += [c.code_matiere for c in lc if (c.type in type_list)]
    return list(set(lcf))

def doMatches(nom, prenom, module, groupe) :
    if (nom is not '') and (prenom is not ''):
        match_np = re.compile(nom.upper()+', '+prenom.upper())
    else: match_np = re.compile('.*')

    if module is not '':
        match_m = re.compile(module)
    else: match_m = re.compile('.*')

    if groupe is not '':
        match_g = re.compile(groupe)
    else: match_g = re.compile('.*')     
    return match_np, match_m, match_g

def doBP(cfg, nom, prenom, module, groupe, debut, fin, personnel_dpt, tab_module) :
    s = ''
    print('BP', nom, prenom, module, groupe, debut, fin)
    (match_np, match_m, match_g) = doMatches(nom, prenom, module, groupe)

    s += "=========================\n"
    s += "= Analyse par personnel =\n"
    s += "=========================\n\n"
    if (nom is not '') and (prenom is not ''):
        test = lambda rx, ry, x, y : match_np.match(rx+', '+ry.upper())
    else: test = lambda rx, ry, x, y : True
    # with open(cfg['File Names']['Teachers'], 'r') as csvfile:
    #     dct = csv.DictReader(csvfile, delimiter='\t')
    #     for row in dct:
    
    for nomp, (pnom, pprenom, pstt, pcode ) in personnel_dpt.items() :
        if test(pnom, pprenom, nom, prenom):
            #nomp = row['Nom']+', '+row['Prénom']
            if nomp in personnel_dpt.keys(): statut =  nomp+' ('+pstt+')'
            else: statut = nomp 
            s += "==================================================\n"
            s += "==> Recherche pour : "+statut+"\n"
            (lc, lp, lm, lg) = load(cfg, pcode, debut, fin)
            if lc is not None:
                if module is not '' :
                    for m in lm :
                        if match_m.match(m) is not None : 
                            if m in tab_module : mname= ' ('+tab_module[m][0]+') '
                            else: mname = ''
                            if groupe is not '' :
                                for g in lg :
                                    if match_g.match(g) is not None :
                                        s += analyse([c for c in lc if (m == c.code_matiere) and (g in c.groupe) ], m+mname+'|'+g)
                            else: s += analyse([c for c in lc if m == c.code_matiere], m+mname)                            
                elif  groupe is not '' :
                    for g in lg :
                        if match_g.match(g) is not None :  
                            s += analyse([c for c in lc if g in c.groupe], g)
                else: 
                    for m in lm :
                        if m in tab_module : mname= ' ('+tab_module[m][0]+') '
                        else: mname = ''
                        #print('-----------',m)
                        s += analyse([c for c in lc if m == c.code_matiere], m+mname)
            s += "==================================================\n\n"
    s += "\n"
    return s

def doBM(cfg, nom, prenom, module, groupe, resp, debut, fin, personnel_dpt, tab_module) :
    s = ''
    print('BM', nom, prenom, module, groupe, debut, fin)
    (match_np, match_m, match_g) = doMatches(nom, prenom, module, groupe)      

    s += "======================\n"
    s += "= Analyse par module =\n"
    s += "======================\n\n"
    if module is not '':
        test = lambda rx, x : match_m.match(rx) is not None
    else: test = lambda rx, x : True
    if resp and (nom is not '') and (prenom is not ''): lcf = getModulesInfo(cfg, nom, prenom, debut, fin, match_np, ['CM info'])
    else: lcf = []
    # with open(cfg['File Names']['Courses'], 'r') as csvfile:
    #     dct = csv.DictReader(csvfile, delimiter='\t')
    #     for row in dct:
    for code, (course, cid) in tab_module.items() : # module[row['Code']] = [row['Nom'],row['id']] 
        if resp and (nom is not '') and (prenom is not '') and (code in lcf):
            s += "=================== "+ nom+ ", "+prenom +"  ===============================\n"
            s += "==> Recherche pour : "+course+"\n"
            s += "Code : "+code+"\n"
            (lc, lp, lm, lg) = load(cfg, cid, debut, fin)
            for p in lp : 
                if p in personnel_dpt.keys(): statut =  p+' ('+personnel_dpt[p][2]+')'
                else: statut = p 
                s += analyse([c for c in lc if p in c.personnel ], statut)
            s += "==================================================\n\n\n"
        elif not(resp) and (test(code, module) or test(course, module)) : 
            s += "==================================================\n"
            s += "==> Recherche pour : "+course+"\n"
            s += "Code : "+code+"\n"
            (lc, lp, lm, lg) = load(cfg, cid, debut, fin)
            if lc is not None:
                if (nom is not '') and (prenom is not ''):
                    for p in lp :
                        if match_np.match(p.upper()) is not None : 
                            if p in personnel_dpt.keys(): statut =  p+' ('+personnel_dpt[p][2]+')'
                            else: statut = p 
                            if groupe is not '' : 
                                for g in lg :
                                    if match_g.match(g) is not None :
                                        s += analyse([c for c in lc if (p in c.personnel) and (g in c.groupe) ], statut+'|'+g)
                            else: s += analyse([c for c in lc if p in c.personnel ], statut)
                elif  groupe is not '' :
                    for g in lg :
                        if match_g.match(g) is not None : 
                            s += analyse([c for c in lc if g in c.groupe], g)
                else: 
                    for p in lp :
                        if p in personnel_dpt.keys(): statut =  p+' ('+personnel_dpt[p][2]+')'
                        else: statut = p
                        s += analyse([c for c in lc if p in c.personnel ], statut)
            s += "==================================================\n\n\n"
    s += "\n"
    return s

def doBG(cfg, nom, prenom, module, groupe, debut, fin, personnel_dpt, tab_module) :
    s = ''
    print('BG', nom, prenom, module, groupe, debut, fin)
    (match_np, match_m, match_g) = doMatches(nom, prenom, module, groupe)      

    s += "======================\n"
    s += "= Analyse par groupe =\n"
    s += "======================\n\n"
    if groupe is not '':
        test = lambda rx, x : match_g.match(rx) is not None 
    else: test = lambda rx, x : True
    with open(cfg['File Names']['Groups'], 'r') as csvfile:
        dct = csv.DictReader(csvfile, delimiter='\t')
        for row in dct:
            if test(row['Code'], groupe) : 
                s += "==================================================\n"
                s += "==> Recherche pour : "+row['Code']+"\n"
                (lc, lp, lm, lg) = load(cfg, row['id'], debut, fin)
                if lc is not None:
                    if (nom is not '') and (prenom is not ''):
                        for p in lp :
                            if match_np.match(p.upper()) is not None : 
                                if p in personnel_dpt.keys(): statut =  p+' ('+personnel_dpt[p][2]+')'
                                else: statut = p
                                if module is not '' :
                                    for m in lm :
                                        if m in tab_module : mname= ' ('+tab_module[m][0]+') '
                                        else: mname = ''
                                        if match_m.match(m) is not None :
                                            s += analyse([c for c in lc if (m == c.code_matiere) and (p in c.personnel) ], statut+'|'+m+mname)
                                else: s += analyse([c for c in lc if p in c.personnel ], statut)
                    elif  module is not '' :
                        for m in lm :
                            if m in tab_module : mname= ' ('+tab_module[m][0]+') '
                            else: mname = ''
                            if match_m.match(m) is not None :  
                                s += analyse([c for c in lc if m == c.code_matiere], m+mname)
                    else: 
                        for p in lp :
                            if p in personnel_dpt.keys(): statut =  p+' ('+personnel_dpt[p][2]+')'
                            else: statut = p
                            s += analyse([c for c in lc if p in c.personnel ], statut)
                s += "==================================================\n\n\n"
        s += "\n"
    return s

#==================================================
#=== Gestion de la configuratiuon =================
#==================================================

cfg = ConfigParser() #interpolation=ExtendedInterpolation())
r = cfg.read('config.cfg')
if r == []:
    print('Config file not founded')
    exit()
else :
    #=== Préparation du contexte
    print("Reconstruction des CSV")

    personnel_dpt = getPerso(cfg)
    tab_module = getModule(cfg)
    getGroupe(cfg)

    if not existDir(cfg['Dir Names']['Cache_dir']):
        os.makedirs(cfg['Dir Names']['Cache_dir'])

    ctx.loadWebConfig('web-config.xml')
    ctx.personnel_dpt = personnel_dpt
    ctx.tab_module = tab_module
    ctx.cfg = cfg
    ctx.debug = cfg['Autre']['debug']=='True'
    ctx.host = cfg['Web']['host']
    ctx.port = cfg['Web']['port']

#==================================================
#==================================================
#==================================================
if __name__ == "__main__":

    #=== Gestion des arguments

    parser = argparse.ArgumentParser(description='Celcat explorer')
    parser.add_argument("-n", "--nom", default='', dest="nom", help="Nom d'une personne (en majuscules)")
    parser.add_argument("-p", "--prenom", default='', dest="prenom", help="Prenom d'une personne (minuscules, sauf première lettre)")
    parser.add_argument("-m", "--module", default='', dest="module", help="Code du module")
    parser.add_argument("-g", "--groupe", default='', dest="groupe", help="Code du groupe")
    parser.add_argument("-bm", action="store_true", help="Recherche par module (-m XXX obligatoire)")
    parser.add_argument("-bp", action="store_true", help="Recherche par personne (-n NNN et -p PPP obligatoires)")
    parser.add_argument("-bg", action="store_true", help="Recherche par groupe (-g GGG obligatoire)")

    parser.add_argument("-resp", action="store_true", help="Des modules où la personne donne des cours (si -bm, -p et -n)" )

    parser.add_argument("-d", "--debut", default='', dest="debut", help="date de début des créneaux à analyser (AAAA-MM-JJ)" )    
    parser.add_argument("-f", "--fin", default='', dest="fin", help="date de fin des créneaux à analyser (AAAA-MM-JJ)" ) 

    parser.add_argument("-w", "--web", action="store_true", help="lance la version serveur Web (les autres paramètres sont ignorés)")

    args = parser.parse_args()

    if args.web :
        try:
            print('Running ', ctx.name ,' on <http://'+ctx.host +':'+ ctx.port+'>')
            ctx.start()
            app.run(
                host=ctx.host,
                port=int(ctx.port),
                debug=ctx.debug
            )
        except KeyboardInterrupt:
            pass
        finally:
            ctx.stop()
    else:
        #=== Lancement des traitements
        if args.bp:
            print(doBP(cfg, args.nom, args.prenom, args.module, args.groupe, args.debut, args.fin, personnel_dpt, tab_module))

        if args.bm:
            print(doBM(cfg, args.nom, args.prenom, args.module, args.groupe, args.resp, args.debut, args.fin, personnel_dpt, tab_module))

        if args.bg: 
            print(doBG(cfg, args.nom, args.prenom, args.module, args.groupe, args.debut, args.fin, personnel_dpt, tab_module))

        print("Fin")
