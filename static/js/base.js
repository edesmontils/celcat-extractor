//<script language="javascript">
// nécessite Prototypejs.org et Script.aculo.us

var Request = Class.create({
    initialize: function (t, nom, prenom, course, groupe, debut, fin, resp, res) {
        this.type = t;
        this.nom = nom;
        this.prenom = prenom;
        this.course = course;
        this.groupe = groupe;
        this.debut = debut;
        this.fin = fin;
        this.resp = resp;
        this.error = res;
        this.result = null;
    }
});

var RequestSet = Class.create({
    initialize: function () {
        this.init();
    },
    init: function () {
        this.set = new Array();
        this.nb = 0;
    },
    add: function (request) {
        this.set.push(request);
        this.nb = this.nb + 1;
    },
    remove: function (i) {
        for (var j = i; j < this.nb - 1; j++)
        this.set[i] = this.set[i + 1];
        this.set[ this.nb - 1] = null;
        this.nb = this.nb - 1;
    },
    show: function () {
        t = '<div class="post"><h2 class="title">Query Bag</h2>' 
          + '<div class="story"><table cellspacing="1" border="1" cellpadding="2">' 
          + '<thead><th>n°</th><th>Type</th><th>Nom</th>'
          + '<th>Module</th>' + '<th>Groupe</th>'  + '<th>Début</th>'  + '<th>Fin</th>' + '<th>resp</th>'
          + '<th>Actions</th>'
          + '<th>Well formed ?</th>'
          + '</thead>';
        
        for (var i = 0; i < this.nb; i++) {
            r = this.set[i];
            t = t + '<tr><td> ' + (i+1) + ' </td>'; 
            t = t + '<td>' + r.type + '</td>' + '<td>' + r.nom + ', '+ r.prenom + '</td>';
            t = t + '<td>' + r.course + '</td>' + '<td>' + r.groupe + '</td>' + '<td>' + r.debut + '</td>' + '<td>' + r.fin + '</td>' + '<td>' + r.resp + '</td>';
            t = t + '<td>';
            // t = t + "<img src='./static/images/gear_64.png' alt='Envoyer la requête' title='Envoyer la requête' width='32' onClick='histo(" + i + "); return false;'  style='cursor:pointer'/>";
            t = t + "<img src='./static/images/pencil_64.png' alt='Edit query' title='Edit query' width='32' onClick='histo_mod(" + i + "); return false;'  style='cursor:pointer'/>";
            t = t + "&nbsp;&nbsp;&nbsp;<img src='./static/images/delete_64.png' alt='Delete query' title='Delete query' width='32' onClick='histo_del(" + i + "); return false;'  style='cursor:pointer'/>";
            t = t + '</td>';
            if (r.error) t = t + "<td><img src='./static/images/tick_64.png' width='32' alt='ok' title='ok' /></td>"; 
            else t = t + "<td><img src='./static/images/block_64.png' width='32' alt='ko' title='ko'/></td>";

            t = t + "</tr>";
        }
        
        t = t + '</table></div></div>';

        return t;
    }
});



//=================================================================
// Contrôle de la sortie de page pour éviter de perdre les requêtes
//=================================================================

window.onbeforeunload = function (evt) {
    var message = 'Queries will be deleted!';
    if (typeof evt == 'undefined') {
        evt = window.event;
    }
    if (evt) {
        evt.returnValue = message;
    }
    return message;
}

//=======================================================
// Fonctions de gestion de l'interface et des appels AJAX
//=======================================================

function clear() {
	
	// Variables de gestion de la mémoire initialisées.
	rs = new RequestSet();
    result_type = null;
    current_nom = "";current_prenom = "";
    current_course = ""; current_groupe="" ; current_type="bp" ; 
    current_debut="" ; current_fin="";current_resp=false;
    current_result = null;
    
	// mémorisation des messages et aides pour éviter de charger le serveur.
	messages_aides = null;
	messages = null;
	messages_mentions = null;
	messages_apropos = null;

    // Page effacée
    $('posts').update("");
}

function effacer() {
    
    // Variables de gestion de la mémoire initialisées.
    result_type = null;
    current_nom = "";current_prenom = "";
    current_course = ""; current_groupe="" ; current_type="bp" ; 
    current_debut="" ; current_fin="";current_resp=false;
    current_result = null;
    
    // Page effacée
    if ($('results')) {
        $('nom').setValue(current_nom);
        $('prenom').setValue(current_prenom);
        $('module').setValue(current_course);
        $('groupe').setValue(current_groupe);
        $('debut').setValue(current_debut);
        $('fin').setValue(current_fin);
        $('resp').setValue(current_resp);
        if (current_type=="bm") { $('bm').setValue(true);}
        else {
            if (current_type=="bg" ) { $('bg').setValue(true);}
            else { $('bp').setValue(true);}
        }
        $('results').update("");
    }
}

function init() {
    //alert("Inti !")
    clear();
    news();
}

function attention() {
    alert('Query bag is erased. Retrieving reference queries.');
}

function end() {
    new Ajax.Request('/end', {
        method: 'get',
        onSuccess: function (trs) {
            $('posts').hide();
            $('posts').update(trs.responseText);
            $('posts').appear();
        },
        onFailure: function () {
            alert('end: Impossible !')
        }
    });
}

// (t, nom, prenom, course, groupe, debut, fin, resp, res, lab)

function remember() {
    res = current_result['val'];
    req = new Request(current_type, current_nom, current_prenom, current_course, current_groupe, current_debut, current_fin, current_resp, result_type);
    req.result = current_result['val'];
    rs.add(req);
    $('memoriser').hide();
    $('results').insert("<p>Query inserted in the Query bag</p>");
}

function histo(i) { // Risque de problème de mémoire s'il y a beaucoup de requête et/ou très grosses. Peut-être refaire un accès à la base...
    code = 'results-' + i;
    if ($(code).empty()) {
        r = rs.set[i];
        $(code).hide();
        $(code).update(r.result);
        $('memoriser').hide();
        $(code).appear();
    } else {
        $(code).hide();
        $(code).update("");
    }
}

function histo_mod(i) {
    r = rs.set[i];
    current_nom = r.nom;
    current_prenom = r.prenom;
    current_course = r.course;
    current_groupe = r.groupe;
    current_debut = r.debut;
    current_fin = r.fin;
    current_resp = r.resp;
    current_type = r.type;
    new_query();
}

function histo_del(i) {
    if (confirm("Êtes-vous certain(e) de vouloir supprimer la requête " + i + " ?")) {
        rs.remove(i);
        get_histo();
    }
}

function get_histo() {
    $('posts').hide();
    $('posts').update(rs.show());
    $('posts').appear();
}

function bmr(nom,prenom) {
    new Ajax.Request('/bmr/'+nom+'/'+prenom, {
        method: 'get',
        onSuccess: function (trs) {
            $('posts').hide();
            $('posts').update(trs.responseText);
            $('posts').appear();
        },
        onFailure: function () {
            alert('bmr: Impossible !')
        }
    });
}

function query() {
    mss = '<p>'+''+'</p>'

    current_nom = $('nom').getValue();
    current_prenom = $('prenom').getValue();
    current_course = $('module').getValue();
    current_groupe = $('groupe').getValue();
    current_debut = $('debut').getValue();
    current_fin = $('fin').getValue();
    current_resp = $('resp').getValue();
    if ($('bm').getValue()) {current_type="bm";}
    else {
        if ($('bg').getValue()) {current_type="bg";}
        else {current_type="bp";}
    }
    $('message').update(mss);

    // $('results').hide();
    $('results').update('<p>Computing request</p>');
    // $('results').appear();

    new Ajax.Request('/envoyer', {
        method: 'post',
        parameters: {
            nom: current_nom, 
            prenom: current_prenom,
            course: current_course,
            groupe: current_groupe,
            debut: current_debut,
            fin: current_fin,
            resp: current_resp=='on' ,
            type: current_type
        },
        onSuccess: function (trs) {
            current_result = JSON.parse(trs.responseText).result;
            result_type = current_result['ok']
            s = current_result['val']
            if (result_type) s = s + "<br><img src='./static/images/tick_64.png'  width='32' alt='ok' title='ok'/>"
            else s = s + "<img src='./static/images/block_64.png'  width='32' alt='ko' title='ko'/>"
            s = s + '<img src="./static/images/add_64.png" id="memoriser" name="Mémoriser" alt="Save in Query bag" title="Save in Query bag" width="32" onClick="remember(); return false;" style="cursor:pointer"/>';
            $('message').update(mss);
            $('results').hide();
            $('results').update(s);
            $('results').appear();
        },
        onFailure: function () {
            alert('query: unable to send the query !')
        }
    });
}

function new_query() {
    t = '<div class="post">';
    t = t + '<h2 class="title">Query editor</h2>';

    t = t + '<div class="story">';
    t = t + '   <form method="POST" id="SaisieRequete" onSubmit="query(); return false;">';
    t = t + '   <p>Nom : <input type="text" name="nom" id="nom" cols="40"></text> <br/>';
    t = t + '   <p>Prénom : <input type="text" name="prenom" id="prenom" cols="40"/> <br/>';
    t = t + '   <p>Module : <input type="text" name="module" id="module" cols="40"/> <br/>';
    t = t + '   <p>Groupe : <input type="text" name="groupe" id="groupe" cols="40"/> <br/>';
    t = t + '   <p>Début : <input type="date" name="debut" id="debut" cols="40"/> <br/>';
    t = t + '   <p>Fin : <input type="date" name="fin" id="fin" cols="40"/> <br/>';
    t = t + '   <p>Resp : <input type="checkbox" name="resp" id="resp"/> <br/>';

    t = t + '<fieldset> <legend>Type</legend><ul>';
    t = t + '<li><label for="bp"><input type="radio" id="bp" required name="type" value="bp" >Par personne</label></li>';
    t = t + '<li><label for="bm"><input type="radio" id="bm" required name="type" value="bm">Par module</label></li>';
    t = t + '<li><label for="bg"><input type="radio" id="bg" required name="type" value="bg">Par groupe</label></li>';
    t = t + '</ul></fieldset>'

    t = t + '   <input type="button" name="Soumettre" value="Envoyer" onClick="query(); return false;" style="cursor:pointer"  id="send"/>';
    t = t + '   <input type="button" name="Effacer" value="Effacer" onClick="effacer(); return false;" style="cursor:pointer"  id="eff"/>';

    t = t + '   </form></p>';
    t = t + '   <div id="message"></div>';
    t = t + '   <div id="results"></div>';
    t = t + '</div>';



    t = t + '</div>';
    
    $('posts').hide();
    $('posts').update(t);
    
    $('nom').setValue(current_nom);
    $('prenom').setValue(current_prenom);
    $('module').setValue(current_course);
    $('groupe').setValue(current_groupe);
    $('debut').setValue(current_debut);
    $('fin').setValue(current_fin);
    $('resp').setValue(current_resp);
    if (current_type=="bm") { $('bm').setValue(true);}
    else {
        if (current_type=="bg" ) { $('bg').setValue(true);}
        else { $('bp').setValue(true);}
    }
    $('posts').appear();
}


function news() {
    if (messages == null) {
        new Ajax.Request('/news', {
            method: 'get',
            onSuccess: function (trs) {
                rep = JSON.parse(trs.responseText).result;
                s = ''
                for(var i = 0; i < rep.length;i++) {
                    r = rep[i];
                    s += "<div class='post'><h2 class='title'>"
                         +r['titre']+"</h2><h3 class='posted'>"
                         +r['post']+"</h3><div class='story'>";
                    s += r['s'];
                    s += "</div></div>\n";
                };
                $('posts').hide();
                $('posts').update(s);
                $('posts').appear();
            },
            onFailure: function () {
                alert('messages: Impossible d\'obtenir la rubrique !')
            }
        });
    } else {
        $('posts').hide();
        $('posts').update(messages);
        $('posts').appear();
    }
}


function mentions() {
    if (messages_mentions == null) {
        new Ajax.Request('/mentions', {
            method: 'get',
            onSuccess: function (trs) {
                messages_mentions = trs.responseText
                messages_mentions = '<div class="post"><h2 class="title">Mentions</h2> <h3 class="posted">par E. Desmontils</h3><div class="story">' 
                            + messages_mentions + "</div></div>\n";
                $('posts').hide();
                $('posts').update(messages_mentions);
                $('posts').appear();
            },
            onFailure: function () {
                alert('mentions: Impossible d\'obtenir la rubrique !')
            }
        });
    } else {
        $('posts').hide();
        $('posts').update(messages_mentions);
        $('posts').appear();
    }
}

function apropos() {
    if (messages_apropos == null) {
        new Ajax.Request('/apropos', {
            method: 'get',
            onSuccess: function (trs) {
                messages_apropos = trs.responseText
                $('posts').hide();
                $('posts').update(messages_apropos);
                $('posts').appear();
            },
            onFailure: function () {
                alert('apropos: Impossible d\'obtenir la rubrique !')
            }
        });
    } else {
        $('posts').hide();
        $('posts').update(messages_apropos);
        $('posts').appear();
    }
}

function aides() {
    if (messages_aides == null) {
        new Ajax.Request('/help', {
            method: 'get',
            onSuccess: function (trs) {
                messages_aides = trs.responseText
                $('posts').hide();
                $('posts').update(messages_aides);
                $('posts').appear();
            },
            onFailure: function () {
                alert('aide: Impossible d\'obtenir la rubrique !')
            }
        });
    } else {
        $('posts').hide();
        $('posts').update(messages_aides);
        $('posts').appear();
    }
}

//</script>