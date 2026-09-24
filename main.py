# ============================================================
# LABMATRICE PROF V9
# Assistant pédagogique pour enseignants
# Python + Kivy + SQLite
# Un seul fichier : main.py
# ============================================================

import os
import json
import html
import sqlite3
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput


# ============================================================
# OUTILS
# ============================================================

def maintenant():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def safe_text(value):
    return "" if value is None else str(value)


def get_export_dir(app_instance):
    """Retourne un chemin d'accès public accessible sur Android ou PC."""
    try:
        from android.storage import primary_external_storage_path
        primary_ext = primary_external_storage_path()
        download_dir = os.path.join(primary_ext, "Download")
        if os.path.exists(download_dir):
            return download_dir
        return primary_ext
    except Exception:
        return app_instance.user_data_dir


# ============================================================
# BASE DE DONNÉES
# ============================================================

class Database:

    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.create_default_canevas()

    def execute(self, sql, params=(), commit=False):
        cur = self.conn.cursor()
        cur.execute(sql, params)

        if commit:
            self.conn.commit()

        return cur

    # --------------------------------------------------------
    # TABLES
    # --------------------------------------------------------

    def create_tables(self):

        self.execute("""
        CREATE TABLE IF NOT EXISTS profil (
            id INTEGER PRIMARY KEY,
            nom TEXT,
            ecole TEXT,
            fonction TEXT,
            option TEXT,
            telephone TEXT,
            email TEXT
        )
        """, commit=True)

        self.execute("""
        CREATE TABLE IF NOT EXISTS canevas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            option TEXT NOT NULL,
            discipline TEXT NOT NULL,
            description TEXT,
            rubriques TEXT NOT NULL,
            modification TEXT,
            UNIQUE(option, discipline)
        )
        """, commit=True)

        self.execute("""
        CREATE TABLE IF NOT EXISTS fiches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            option TEXT,
            discipline TEXT,
            niveau TEXT,
            duree TEXT,
            theme TEXT,
            lecon TEXT,
            contenu TEXT,
            statut TEXT,
            creation TEXT,
            modification TEXT
        )
        """, commit=True)

    # --------------------------------------------------------
    # PROFIL
    # --------------------------------------------------------

    def get_profil(self):

        return self.execute("""
        SELECT * FROM profil WHERE id=1
        """).fetchone()

    def save_profil(self, data):

        self.execute("""
        INSERT OR REPLACE INTO profil
        (id, nom, ecole, fonction, option, telephone, email)
        VALUES (1,?,?,?,?,?,?)
        """, (
            data["nom"],
            data["ecole"],
            data["fonction"],
            data["option"],
            data["telephone"],
            data["email"]
        ), commit=True)

    # --------------------------------------------------------
    # CANEVAS
    # --------------------------------------------------------

    def save_canevas(
        self,
        option,
        discipline,
        description,
        rubriques
    ):

        self.execute("""
        INSERT INTO canevas
        (option, discipline, description, rubriques, modification)
        VALUES (?,?,?,?,?)

        ON CONFLICT(option, discipline)
        DO UPDATE SET
            description=excluded.description,
            rubriques=excluded.rubriques,
            modification=excluded.modification
        """, (
            option,
            discipline,
            description,
            json.dumps(
                rubriques,
                ensure_ascii=False
            ),
            maintenant()
        ), commit=True)

    def get_canevas(
        self,
        option,
        discipline
    ):

        row = self.execute("""
        SELECT * FROM canevas
        WHERE option=? AND discipline=?
        """, (
            option,
            discipline
        )).fetchone()

        if not row:
            return None

        try:
            rubriques = json.loads(
                row["rubriques"]
            )
        except Exception:
            rubriques = []

        return {
            "id": row["id"],
            "option": row["option"],
            "discipline": row["discipline"],
            "description": row["description"],
            "rubriques": rubriques
        }

    def get_all_canevas(self):

        return self.execute("""
        SELECT * FROM canevas
        ORDER BY option, discipline
        """).fetchall()

    def delete_canevas(self, cid):

        self.execute("""
        DELETE FROM canevas WHERE id=?
        """, (cid,), commit=True)

    # --------------------------------------------------------
    # FICHES
    # --------------------------------------------------------

    def add_fiche(
        self,
        option,
        discipline,
        niveau,
        duree,
        theme,
        lecon,
        contenu,
        statut
    ):

        moment = maintenant()

        self.execute("""
        INSERT INTO fiches
        (
            option,
            discipline,
            niveau,
            duree,
            theme,
            lecon,
            contenu,
            statut,
            creation,
            modification
        )
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            option,
            discipline,
            niveau,
            duree,
            theme,
            lecon,
            json.dumps(
                contenu,
                ensure_ascii=False
            ),
            statut,
            moment,
            moment
        ), commit=True)

    def update_fiche(
        self,
        fid,
        option,
        discipline,
        niveau,
        duree,
        theme,
        lecon,
        contenu,
        statut
    ):

        self.execute("""
        UPDATE fiches
        SET
            option=?,
            discipline=?,
            niveau=?,
            duree=?,
            theme=?,
            lecon=?,
            contenu=?,
            statut=?,
            modification=?
        WHERE id=?
        """, (
            option,
            discipline,
            niveau,
            duree,
            theme,
            lecon,
            json.dumps(
                contenu,
                ensure_ascii=False
            ),
            statut,
            maintenant(),
            fid
        ), commit=True)

    def get_fiche(self, fid):

        row = self.execute("""
        SELECT * FROM fiches WHERE id=?
        """, (fid,)).fetchone()

        if not row:
            return None

        data = dict(row)

        try:
            data["contenu"] = json.loads(
                data["contenu"]
            )
        except Exception:
            data["contenu"] = {}

        return data

    def get_fiches(self, recherche=""):

        if recherche.strip():

            q = "%" + recherche.strip() + "%"

            return self.execute("""
            SELECT *
            FROM fiches
            WHERE option LIKE ?
               OR discipline LIKE ?
               OR niveau LIKE ?
               OR theme LIKE ?
               OR lecon LIKE ?
               OR statut LIKE ?
            ORDER BY id DESC
            """, (
                q, q, q, q, q, q
            )).fetchall()

        return self.execute("""
        SELECT *
        FROM fiches
        ORDER BY id DESC
        """).fetchall()

    def delete_fiche(self, fid):

        self.execute("""
        DELETE FROM fiches WHERE id=?
        """, (fid,), commit=True)

    # --------------------------------------------------------
    # STATISTIQUES
    # --------------------------------------------------------

    def total_fiches(self):

        return self.execute("""
        SELECT COUNT(*) FROM fiches
        """).fetchone()[0]

    def total_finalisees(self):

        return self.execute("""
        SELECT COUNT(*)
        FROM fiches
        WHERE statut='Finalisée'
        """).fetchone()[0]

    def total_brouillons(self):

        return self.execute("""
        SELECT COUNT(*)
        FROM fiches
        WHERE statut='Brouillon'
        """).fetchone()[0]

    def total_canevas(self):

        return self.execute("""
        SELECT COUNT(*) FROM canevas
        """).fetchone()[0]

    # --------------------------------------------------------
    # CANEVAS INITIAUX
    # --------------------------------------------------------

    def create_default_canevas(self):

        if self.total_canevas() > 0:
            return

        rubriques = [
            {
                "nom": "Objectif général",
                "obligatoire": True
            },
            {
                "nom": "Objectifs spécifiques",
                "obligatoire": True
            },
            {
                "nom": "Prérequis",
                "obligatoire": False
            },
            {
                "nom": "Matériel didactique",
                "obligatoire": False
            },
            {
                "nom": "Introduction",
                "obligatoire": True
            },
            {
                "nom": "Déroulement de la leçon",
                "obligatoire": True
            },
            {
                "nom": "Synthèse",
                "obligatoire": True
            },
            {
                "nom": "Évaluation",
                "obligatoire": True
            },
            {
                "nom": "Remédiation",
                "obligatoire": False
            },
            {
                "nom": "Devoir",
                "obligatoire": False
            },
            {
                "nom": "Références",
                "obligatoire": False
            }
        ]

        for discipline in [
            "Mathématiques",
            "Français",
            "Informatique",
            "Histoire",
            "Géographie",
            "Sciences"
        ]:

            self.save_canevas(
                "Général",
                discipline,
                "Modèle générique configurable.",
                rubriques
            )


# ============================================================
# ACCUEIL
# ============================================================

class AccueilScreen(Screen):

    def on_pre_enter(self):
        self.refresh()

    def refresh(self):

        db = App.get_running_app().db

        self.ids.total.text = (
            str(db.total_fiches())
            + "\nPréparations"
        )

        self.ids.finales.text = (
            str(db.total_finalisees())
            + "\nFinalisées"
        )

        self.ids.brouillons.text = (
            str(db.total_brouillons())
            + "\nBrouillons"
        )

        self.ids.canevas.text = (
            str(db.total_canevas())
            + "\nCanevas"
        )

    def new_fiche(self):

        screen = self.manager.get_screen(
            "nouvelle"
        )

        screen.reset()

        self.manager.current = "nouvelle"


# ============================================================
# PROFIL
# ============================================================

class ProfilScreen(Screen):

    def on_pre_enter(self):
        self.load()

    def load(self):

        row = App.get_running_app().db.get_profil()

        if not row:
            return

        self.ids.nom.text = safe_text(row["nom"])
        self.ids.ecole.text = safe_text(row["ecole"])
        self.ids.fonction.text = safe_text(row["fonction"])
        self.ids.option.text = safe_text(row["option"])
        self.ids.telephone.text = safe_text(row["telephone"])
        self.ids.email.text = safe_text(row["email"])

    def save(self):

        App.get_running_app().db.save_profil({
            "nom": self.ids.nom.text,
            "ecole": self.ids.ecole.text,
            "fonction": self.ids.fonction.text,
            "option": self.ids.option.text,
            "telephone": self.ids.telephone.text,
            "email": self.ids.email.text
        })

        App.get_running_app().message(
            "Profil",
            "Profil enregistré avec succès."
        )


# ============================================================
# NOUVELLE FICHE
# ============================================================

class NouvelleScreen(Screen):

    fiche_id = None

    def reset(self):

        self.fiche_id = None
        self.build_form()

    def build_form(self, data=None):

        self.ids.form.clear_widgets()

        self.inputs = {}
        self.dynamic = {}
        self.dynamic_box = None

        titre = (
            "MODIFICATION DE LA PRÉPARATION"
            if data
            else
            "NOUVELLE PRÉPARATION"
        )

        self.ids.form.add_widget(
            Label(
                text=titre,
                font_size=dp(23),
                bold=True,
                size_hint_y=None,
                height=dp(50)
            )
        )

        fields = [
            ("option", "Option"),
            ("discipline", "Discipline"),
            ("niveau", "Classe / Niveau"),
            ("duree", "Durée"),
            ("theme", "Thème"),
            ("lecon", "Titre de la leçon")
        ]

        for key, hint in fields:

            value = ""

            if data:
                value = safe_text(
                    data.get(key, "")
                )

            field = TextInput(
                text=value,
                hint_text=hint,
                multiline=False,
                size_hint_y=None,
                height=dp(52)
            )

            self.inputs[key] = field

            self.ids.form.add_widget(field)

        self.ids.form.add_widget(
            Button(
                text="🧩 Charger le canevas",
                size_hint_y=None,
                height=dp(55),
                on_release=lambda x:
                self.load_canevas()
            )
        )

        self.dynamic_box = GridLayout(
            cols=1,
            spacing=dp(8),
            size_hint_y=None
        )

        self.dynamic_box.bind(
            minimum_height=
            self.dynamic_box.setter(
                "height"
            )
        )

        self.ids.form.add_widget(
            self.dynamic_box
        )

        self.ids.form.add_widget(
            Button(
                text="💾 Enregistrer comme brouillon",
                size_hint_y=None,
                height=dp(58),
                on_release=lambda x:
                self.save("Brouillon")
            )
        )

        self.ids.form.add_widget(
            Button(
                text="✅ Finaliser",
                size_hint_y=None,
                height=dp(58),
                on_release=lambda x:
                self.save("Finalisée")
            )
        )

    def load_canevas(self):

        option = self.inputs[
            "option"
        ].text.strip()

        discipline = self.inputs[
            "discipline"
        ].text.strip()

        if not option or not discipline:

            return App.get_running_app().message(
                "Canevas",
                "Veuillez saisir l'option et la discipline."
            )

        canevas = App.get_running_app().db.get_canevas(
            option,
            discipline
        )

        self.dynamic_box.clear_widgets()
        self.dynamic = {}

        if not canevas:

            self.dynamic_box.add_widget(
                Label(
                    text=(
                        "Aucun canevas trouvé.\n"
                        "Créez d'abord ce canevas "
                        "dans Gestion des canevas."
                    ),
                    size_hint_y=None,
                    height=dp(80)
                )
            )

            return

        for rubrique in canevas["rubriques"]:

            nom = rubrique["nom"]
            obligatoire = rubrique.get(
                "obligatoire",
                False
            )

            hint = nom

            if obligatoire:
                hint += " *"

            field = TextInput(
                hint_text=hint,
                multiline=True,
                size_hint_y=None,
                height=dp(120)
            )

            self.dynamic[nom] = (
                field,
                obligatoire
            )

            self.dynamic_box.add_widget(
                Label(
                    text=hint,
                    bold=True,
                    size_hint_y=None,
                    height=dp(35)
                )
            )

            self.dynamic_box.add_widget(
                field
            )

    def validate_dynamic(self):

        contenu = {}

        for nom, pair in self.dynamic.items():

            field = pair[0]
            obligatoire = pair[1]

            value = field.text.strip()

            if obligatoire and not value:

                return (
                    False,
                    "La rubrique obligatoire "
                    + "« "
                    + nom
                    + " » est vide."
                )

            contenu[nom] = value

        return True, contenu

    def save(self, statut):

        option = self.inputs[
            "option"
        ].text.strip()

        discipline = self.inputs[
            "discipline"
        ].text.strip()

        niveau = self.inputs[
            "niveau"
        ].text.strip()

        duree = self.inputs[
            "duree"
        ].text.strip()

        theme = self.inputs[
            "theme"
        ].text.strip()

        lecon = self.inputs[
            "lecon"
        ].text.strip()

        if not option:
            return App.get_running_app().message(
                "Validation",
                "L'option est obligatoire."
            )

        if not discipline:
            return App.get_running_app().message(
                "Validation",
                "La discipline est obligatoire."
            )

        if not theme:
            return App.get_running_app().message(
                "Validation",
                "Le thème est obligatoire."
            )

        if not lecon:
            return App.get_running_app().message(
                "Validation",
                "Le titre de la leçon est obligatoire."
            )

        ok, contenu = self.validate_dynamic()

        if not ok:

            return App.get_running_app().message(
                "Validation",
                contenu
            )

        db = App.get_running_app().db

        if self.fiche_id:

            db.update_fiche(
                self.fiche_id,
                option,
                discipline,
                niveau,
                duree,
                theme,
                lecon,
                contenu,
                statut
            )

            message = "Préparation modifiée avec succès."

        else:

            db.add_fiche(
                option,
                discipline,
                niveau,
                duree,
                theme,
                lecon,
                contenu,
                statut
            )

            message = "Préparation enregistrée avec succès."

        self.fiche_id = None

        App.get_running_app().message(
            "LabMatrice Prof",
            message
        )

        self.manager.current = "fiches"

    def edit(self, fid):

        data = App.get_running_app().db.get_fiche(
            fid
        )

        if not data:
            return

        self.fiche_id = fid

        self.build_form(data)

        self.load_canevas()

        for nom, valeur in data[
            "contenu"
        ].items():

            if nom in self.dynamic:

                self.dynamic[nom][0].text = safe_text(
                    valeur
                )


# ============================================================
# LISTE DES FICHES
# ============================================================

class FichesScreen(Screen):

    def on_pre_enter(self):
        self.refresh()

    def refresh(self):

        rows = (
            App.get_running_app()
            .db
            .get_fiches(
                self.ids.recherche.text
            )
        )

        self.ids.liste.clear_widgets()

        if not rows:

            self.ids.liste.add_widget(
                Label(
                    text="Aucune préparation.",
                    size_hint_y=None,
                    height=dp(60)
                )
            )

            return

        for row in rows:

            card = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(205),
                spacing=dp(3)
            )

            card.add_widget(
                Label(
                    text=(
                        row["lecon"]
                        + "\n"
                        + row["discipline"]
                        + " • "
                        + row["niveau"]
                    ),
                    bold=True,
                    font_size=dp(16),
                    size_hint_y=None,
                    height=dp(60)
                )
            )

            card.add_widget(
                Label(
                    text=(
                        "Thème : "
                        + row["theme"]
                        + "\n"
                        + "Statut : "
                        + row["statut"]
                    ),
                    size_hint_y=None,
                    height=dp(55)
                )
            )

            actions = BoxLayout(
                size_hint_y=None,
                height=dp(48),
                spacing=dp(4)
            )

            voir = Button(
                text="Voir"
            )

            voir.bind(
                on_release=lambda x,
                fid=row["id"]:
                self.view(fid)
            )

            modifier = Button(
                text="Modifier"
            )

            modifier.bind(
                on_release=lambda x,
                fid=row["id"]:
                self.edit(fid)
            )

            exporter = Button(
                text="Exporter"
            )

            exporter.bind(
                on_release=lambda x,
                fid=row["id"]:
                self.export(fid)
            )

            supprimer = Button(
                text="Supprimer"
            )

            supprimer.bind(
                on_release=lambda x,
                fid=row["id"]:
                self.delete(fid)
            )

            actions.add_widget(voir)
            actions.add_widget(modifier)
            actions.add_widget(exporter)
            actions.add_widget(supprimer)

            card.add_widget(actions)

            self.ids.liste.add_widget(card)

    def view(self, fid):

        screen = self.manager.get_screen(
            "detail"
        )

        screen.show(fid)

        self.manager.current = "detail"

    def edit(self, fid):

        screen = self.manager.get_screen(
            "nouvelle"
        )

        screen.edit(fid)

        self.manager.current = "nouvelle"

    def delete(self, fid):

        App.get_running_app().db.delete_fiche(
            fid
        )

        self.refresh()

    def export(self, fid):

        data = App.get_running_app().db.get_fiche(
            fid
        )

        if not data:
            return

        app = App.get_running_app()
        export_folder = get_export_dir(app)

        nom = (
            data["lecon"]
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
        )

        txt_path = os.path.join(
            export_folder,
            "Preparation_" + nom + ".txt"
        )

        html_path = os.path.join(
            export_folder,
            "Preparation_" + nom + ".html"
        )

        lignes = []

        lignes.append(
            "========================================"
        )

        lignes.append(
            "LABMATRICE PROF"
        )

        lignes.append(
            "PREPARATION DE LEÇON"
        )

        lignes.append(
            "========================================"
        )

        lignes.append("")

        lignes.append(
            "Option : " + data["option"]
        )

        lignes.append(
            "Discipline : " + data["discipline"]
        )

        lignes.append(
            "Niveau : " + data["niveau"]
        )

        lignes.append(
            "Durée : " + data["duree"]
        )

        lignes.append(
            "Thème : " + data["theme"]
        )

        lignes.append(
            "Leçon : " + data["lecon"]
        )

        lignes.append("")

        for rubrique, valeur in data[
            "contenu"
        ].items():

            lignes.append(
                "----------------------------------------"
            )

            lignes.append(
                rubrique.upper()
            )

            lignes.append(
                "----------------------------------------"
            )

            lignes.append(
                safe_text(valeur)
            )

            lignes.append("")

        with open(
            txt_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                "\n".join(lignes)
            )

        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            "<title>Préparation</title>",
            "<style>",
            "body{font-family:Arial;margin:40px;}",
            "h1{text-align:center;}",
            "h2{margin-top:30px;}",
            ".meta{line-height:1.8;}",
            ".bloc{margin-top:20px;}",
            "</style>",
            "</head>",
            "<body>",
            "<h1>LABMATRICE PROF</h1>",
            "<h2>Préparation de leçon</h2>",
            "<div class='meta'>",
            "<b>Option :</b> "
            + html.escape(data["option"])
            + "<br>",
            "<b>Discipline :</b> "
            + html.escape(data["discipline"])
            + "<br>",
            "<b>Niveau :</b> "
            + html.escape(data["niveau"])
            + "<br>",
            "<b>Durée :</b> "
            + html.escape(data["duree"])
            + "<br>",
            "<b>Thème :</b> "
            + html.escape(data["theme"])
            + "<br>",
            "<b>Leçon :</b> "
            + html.escape(data["lecon"]),
            "</div>"
        ]

        for rubrique, valeur in data[
            "contenu"
        ].items():

            html_parts.extend([
                "<div class='bloc'>",
                "<h2>"
                + html.escape(rubrique)
                + "</h2>",
                "<p>"
                + html.escape(
                    safe_text(valeur)
                ).replace(
                    "\n",
                    "<br>"
                ),
                "</p>",
                "</div>"
            ])

        html_parts.extend([
            "</body>",
            "</html>"
        ])

        with open(
            html_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                "\n".join(html_parts)
            )

        app.message(
            "Export terminé",
            "Deux fichiers ont été créés :\n\n"
            + txt_path
            + "\n\n"
            + html_path
        )


# ============================================================
# DÉTAIL
# ============================================================

class DetailScreen(Screen):

    fiche_id = None

    def show(self, fid):

        self.fiche_id = fid

        data = App.get_running_app().db.get_fiche(
            fid
        )

        if not data:
            return

        lignes = []

        lignes.append(
            "LABMATRICE PROF V9"
        )

        lignes.append(
            "======================================"
        )

        lignes.append(
            "PRÉPARATION DE LEÇON"
        )

        lignes.append("")

        lignes.append(
            "Option : "
            + data["option"]
        )

        lignes.append(
            "Discipline : "
            + data["discipline"]
        )

        lignes.append(
            "Niveau : "
            + data["niveau"]
        )

        lignes.append(
            "Durée : "
            + data["duree"]
        )

        lignes.append(
            "Thème : "
            + data["theme"]
        )

        lignes.append(
            "Leçon : "
            + data["lecon"]
        )

        lignes.append(
            "Statut : "
            + data["statut"]
        )

        lignes.append("")

        for rubrique, valeur in data[
            "contenu"
        ].items():

            lignes.append(
                "======================================"
            )

            lignes.append(
                rubrique.upper()
            )

            lignes.append(
                "======================================"
            )

            lignes.append(
                safe_text(valeur)
            )

            lignes.append("")

        self.ids.contenu.text = "\n".join(
            lignes
        )


# ============================================================
# ASSISTANT
# ============================================================

class AssistantScreen(Screen):

    def generate(self):

        option = self.ids.option.text.strip()
        discipline = self.ids.discipline.text.strip()
        niveau = self.ids.niveau.text.strip()
        duree = self.ids.duree.text.strip()
        theme = self.ids.theme.text.strip()
        lecon = self.ids.lecon.text.strip()
        objectif = self.ids.objectif.text.strip()

        if not option or not discipline:

            return App.get_running_app().message(
                "Assistant",
                "Option et discipline obligatoires."
            )

        if not lecon:

            return App.get_running_app().message(
                "Assistant",
                "Le titre de la leçon est obligatoire."
            )

        canevas = App.get_running_app().db.get_canevas(
            option,
            discipline
        )

        if not canevas:

            return App.get_running_app().message(
                "Assistant",
                "Aucun canevas trouvé."
            )

        lignes = []

        lignes.append(
            "LABMATRICE PROF"
        )

        lignes.append(
            "PROPOSITION DE PRÉPARATION"
        )

        lignes.append(
            "======================================"
        )

        lignes.append(
            "Option : " + option
        )

        lignes.append(
            "Discipline : " + discipline
        )

        lignes.append(
            "Niveau : " + niveau
        )

        lignes.append(
            "Durée : " + duree
        )

        lignes.append(
            "Thème : " + theme
        )

        lignes.append(
            "Leçon : " + lecon
        )

        for rubrique in canevas[
            "rubriques"
        ]:

            nom = rubrique["nom"]

            lignes.append("")

            lignes.append(
                nom.upper()
            )

            lignes.append(
                "-" * 38
            )

            lignes.append(
                self.generate_rubrique(
                    nom,
                    niveau,
                    theme,
                    lecon,
                    objectif
                )
            )

        self.ids.resultat.text = (
            "\n".join(lignes)
        )

    def generate_rubrique(
        self,
        nom,
        niveau,
        theme,
        lecon,
        objectif
    ):

        r = nom.lower()

        if "objectif" in r:

            if objectif:
                return objectif

            return (
                "À la fin de cette leçon, "
                "l'apprenant devra être capable "
                "de comprendre et d'appliquer "
                "les notions relatives à "
                "« "
                + lecon
                + " »."
            )

        if "prérequis" in r:

            return (
                "Identifier les connaissances "
                "antérieures nécessaires à la "
                "compréhension de la nouvelle "
                "notion."
            )

        if "matériel" in r:

            return (
                "Tableau, craie ou marqueur, "
                "manuel, supports didactiques "
                "et exemples adaptés."
            )

        if "introduction" in r:

            return (
                "Présenter une situation de "
                "départ liée au thème « "
                + theme
                + " ». Faire participer les "
                "apprenants et introduire "
                "progressivement la notion."
            )

        if "déroulement" in r:

            return (
                "1. Rappel des connaissances "
                "antérieures.\n"
                "2. Présentation de la situation "
                "d'apprentissage.\n"
                "3. Observation et analyse.\n"
                "4. Explication de la notion.\n"
                "5. Participation des apprenants.\n"
                "6. Exercices d'application.\n"
                "7. Correction."
            )

        if "synthèse" in r:

            return (
                "Faire ressortir avec les "
                "apprenants les notions essentielles "
                "retenues pendant la séance."
            )

        if "évaluation" in r:

            return (
                "Prévoir des questions ou exercices "
                "permettant de vérifier l'atteinte "
                "des objectifs."
            )

        if "remédiation" in r:

            return (
                "Identifier les difficultés "
                "rencontrées et proposer des "
                "activités correctives adaptées."
            )

        if "devoir" in r:

            return (
                "Prévoir un exercice d'application "
                "permettant de consolider les "
                "apprentissage."
            )

        if "référence" in r:

            return (
                "Indiquer les manuels, programmes, "
                "guides ou autres documents "
                "pédagogiques utilisés."
            )

        return (
            "Développer cette rubrique en fonction "
            "de la leçon « "
            + lecon
            + " »."
        )

    def use_result(self):

        screen = self.manager.get_screen(
            "nouvelle"
        )

        screen.reset()

        screen.inputs[
            "option"
        ].text = self.ids.option.text

        screen.inputs[
            "discipline"
        ].text = self.ids.discipline.text

        screen.inputs[
            "niveau"
        ].text = self.ids.niveau.text

        screen.inputs[
            "duree"
        ].text = self.ids.duree.text

        screen.inputs[
            "theme"
        ].text = self.ids.theme.text

        screen.inputs[
            "lecon"
        ].text = self.ids.lecon.text

        screen.load_canevas()

        for nom, pair in screen.dynamic.items():

            pair[0].text = self.generate_rubrique(
                nom,
                self.ids.niveau.text,
                self.ids.theme.text,
                self.ids.lecon.text,
                self.ids.objectif.text
            )

        self.manager.current = "nouvelle"


# ============================================================
# CANEVAS
# ============================================================

class CanevasScreen(Screen):

    def on_pre_enter(self):
        self.show_list()

    def load_current(self):

        option = self.ids.option.text.strip()
        discipline = self.ids.discipline.text.strip()

        if not option or not discipline:

            return self.show_list()

        canevas = App.get_running_app().db.get_canevas(
            option,
            discipline
        )

        self.editor(
            option,
            discipline,
            canevas
        )

    def show_list(self):

        container = self.ids.contenu

        container.clear_widgets()

        container.add_widget(
            Label(
                text="GESTION DES CANEVAS",
                font_size=dp(23),
                bold=True,
                size_hint_y=None,
                height=dp(50)
            )
        )

        rows = (
            App.get_running_app()
            .db
            .get_all_canevas()
        )

        for row in rows:

            line = BoxLayout(
                size_hint_y=None,
                height=dp(58),
                spacing=dp(4)
            )

            line.add_widget(
                Label(
                    text=(
                        row["option"]
                        + " / "
                        + row["discipline"]
                    )
                )
            )

            edit = Button(
                text="Modifier",
                size_hint_x=None,
                width=dp(100)
            )

            edit.bind(
                on_release=lambda x,
                o=row["option"],
                d=row["discipline"]:
                self.editor(
                    o,
                    d,
                    App.get_running_app()
                    .db
                    .get_canevas(o, d)
                )
            )

            line.add_widget(edit)

            delete = Button(
                text="X",
                size_hint_x=None,
                width=dp(45)
            )

            delete.bind(
                on_release=lambda x,
                cid=row["id"]:
                self.delete_canevas(cid)
            )

            line.add_widget(delete)

            container.add_widget(line)

        container.add_widget(
            Button(
                text="➕ Nouveau canevas",
                size_hint_y=None,
                height=dp(58),
                on_release=lambda x:
                self.editor(
                    "",
                    "",
                    None
                )
            )
        )

        container.add_widget(
            Button(
                text="📤 Exporter tous les canevas",
                size_hint_y=None,
                height=dp(58),
                on_release=lambda x:
                self.export_all()
            )
        )

        container.add_widget(
            Button(
                text="📥 Importer un canevas JSON",
                size_hint_y=None,
                height=dp(58),
                on_release=lambda x:
                self.import_json_popup()
            )
        )

    def delete_canevas(self, cid):

        App.get_running_app().db.delete_canevas(
            cid
        )

        self.show_list()

    def editor(
        self,
        option,
        discipline,
        canevas
    ):

        container = self.ids.contenu

        container.clear_widgets()

        container.add_widget(
            Label(
                text="ÉDITEUR DE CANEVAS",
                font_size=dp(23),
                bold=True,
                size_hint_y=None,
                height=dp(50)
            )
        )

        option_input = TextInput(
            text=option,
            hint_text="Option",
            multiline=False,
            size_hint_y=None,
            height=dp(52)
        )

        discipline_input = TextInput(
            text=discipline,
            hint_text="Discipline",
            multiline=False,
            size_hint_y=None,
            height=dp(52)
        )

        description = TextInput(
            text=(
                canevas["description"]
                if canevas
                else ""
            ),
            hint_text="Description",
            multiline=True,
            size_hint_y=None,
            height=dp(90)
        )

        container.add_widget(option_input)
        container.add_widget(discipline_input)
        container.add_widget(description)

        rubriques = []

        if canevas:

            initial = canevas[
                "rubriques"
            ]

        else:

            initial = [
                {
                    "nom": "Objectif général",
                    "obligatoire": True
                },
                {
                    "nom": "Objectifs spécifiques",
                    "obligatoire": True
                }
            ]

        for rubrique in initial:

            self.add_rubrique(
                container,
                rubriques,
                rubrique["nom"],
                rubrique.get(
                    "obligatoire",
                    False
                )
            )

        container.add_widget(
            Button(
                text="➕ Ajouter une rubrique",
                size_hint_y=None,
                height=dp(55),
                on_release=lambda x:
                self.add_rubrique(
                    container,
                    rubriques
                )
            )
        )

        def save():

            o = option_input.text.strip()
            d = discipline_input.text.strip()

            if not o or not d:

                return App.get_running_app().message(
                    "Canevas",
                    "Option et discipline obligatoires."
                )

            result = []

            for nom, required in rubriques:

                name = nom.text.strip()

                if not name:
                    continue

                result.append({
                    "nom": name,
                    "obligatoire":
                    required.text == "OBLIGATOIRE"
                })

            if not result:

                return App.get_running_app().message(
                    "Canevas",
                    "Ajoutez au moins une rubrique."
                )

            App.get_running_app().db.save_canevas(
                o,
                d,
                description.text.strip(),
                result
            )

            App.get_running_app().message(
                "Canevas",
                "Canevas enregistré avec succès."
            )

            self.show_list()

        container.add_widget(
            Button(
                text="💾 Enregistrer",
                size_hint_y=None,
                height=dp(58),
                on_release=lambda x:
                save()
            )
        )

        container.add_widget(
            Button(
                text="↩ Retour",
                size_hint_y=None,
                height=dp(50),
                on_release=lambda x:
                self.show_list()
            )
        )

    def add_rubrique(
        self,
        container,
        rubriques,
        nom="",
        obligatoire=True
    ):

        line = BoxLayout(
            size_hint_y=None,
            height=dp(55),
            spacing=dp(4)
        )

        name = TextInput(
            text=nom,
            hint_text="Nom de la rubrique",
            multiline=False
        )

        required = Button(
            text=(
                "OBLIGATOIRE"
                if obligatoire
                else "FACULTATIVE"
            )
        )

        delete = Button(
            text="X",
            size_hint_x=None,
            width=dp(45)
        )

        def toggle(btn):

            if btn.text == "OBLIGATOIRE":
                btn.text = "FACULTATIVE"
            else:
                btn.text = "OBLIGATOIRE"

        required.bind(
            on_release=toggle
        )

        def remove(btn):

            if line in container.children:
                container.remove_widget(line)

            pair = (
                name,
                required
            )

            if pair in rubriques:
                rubriques.remove(pair)

        delete.bind(
            on_release=remove
        )

        line.add_widget(name)
        line.add_widget(required)
        line.add_widget(delete)

        pair = (
            name,
            required
        )

        rubriques.append(pair)

        container.add_widget(line)

    # --------------------------------------------------------
    # EXPORT CANEVAS
    # --------------------------------------------------------

    def export_all(self):

        rows = (
            App.get_running_app()
            .db
            .get_all_canevas()
        )

        result = []

        for row in rows:

            try:
                rubriques = json.loads(
                    row["rubriques"]
                )
            except Exception:
                rubriques = []

            result.append({
                "format":
                "LabMatriceProf-Canevas",

                "version": 1,

                "option":
                row["option"],

                "discipline":
                row["discipline"],

                "description":
                row["description"],

                "rubriques":
                rubriques
            })

        app = App.get_running_app()
        export_folder = get_export_dir(app)

        path = os.path.join(
            export_folder,
            "LabMatriceProf_Canevas.json"
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                result,
                f,
                ensure_ascii=False,
                indent=4
            )

        App.get_running_app().message(
            "Export",
            "Fichier créé :\n\n"
            + path
        )

    # --------------------------------------------------------
    # IMPORT JSON
    # --------------------------------------------------------

    def import_json_popup(self):

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        layout.add_widget(
            Label(
                text=(
                    "Entrez le chemin complet du "
                    "fichier JSON."
                )
            )
        )

        path_input = TextInput(
            hint_text="/storage/emulated/0/Download/..."
        )

        layout.add_widget(
            path_input
        )

        actions = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(5)
        )

        ok = Button(
            text="Importer"
        )

        cancel = Button(
            text="Annuler"
        )

        actions.add_widget(ok)
        actions.add_widget(cancel)

        layout.add_widget(actions)

        popup = Popup(
            title="Importer un canevas",
            content=layout,
            size_hint=(0.9, 0.5)
        )

        cancel.bind(
            on_release=popup.dismiss
        )

        def importer(btn):

            path = path_input.text.strip()

            if not os.path.exists(path):

                return App.get_running_app().message(
                    "Import",
                    "Fichier introuvable."
                )

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    data = json.load(f)

                if isinstance(data, dict):
                    data = [data]

                count = 0

                for item in data:

                    option = item.get(
                        "option",
                        ""
                    )

                    discipline = item.get(
                        "discipline",
                        ""
                    )

                    rubriques = item.get(
                        "rubriques",
                        []
                    )

                    if not option or not discipline:
                        continue

                    App.get_running_app().db.save_canevas(
                        option,
                        discipline,
                        item.get(
                            "description",
                            ""
                        ),
                        rubriques
                    )

                    count += 1

                popup.dismiss()

                self.show_list()

                App.get_running_app().message(
                    "Import",
                    str(count)
                    + " canevas importé(s)."
                )

            except Exception as e:

                App.get_running_app().message(
                    "Import",
                    "Erreur : "
                    + str(e)
                )

        ok.bind(
            on_release=importer
        )

        popup.open()


# ============================================================
# STATISTIQUES
# ============================================================

class StatsScreen(Screen):

    def on_pre_enter(self):

        db = App.get_running_app().db

        total = db.total_fiches()
        finales = db.total_finalisees()
        brouillons = db.total_brouillons()
        canevas = db.total_canevas()

        result = []

        result.append(
            "📊 STATISTIQUES LABMATRICE PROF"
        )

        result.append(
            "======================================"
        )

        result.append(
            "Total préparations : "
            + str(total)
        )

        result.append(
            "Préparations finalisées : "
            + str(finales)
        )

        result.append(
            "Brouillons : "
            + str(brouillons)
        )

        result.append(
            "Canevas : "
            + str(canevas)
        )

        result.append("")
        result.append(
            "PRÉPARATIONS PAR DISCIPLINE"
        )

        result.append(
            "--------------------------------------"
        )

        rows = db.execute("""
        SELECT discipline, COUNT(*) AS total
        FROM fiches
        GROUP BY discipline
        ORDER BY total DESC
        """).fetchall()

        if rows:

            for row in rows:

                result.append(
                    "• "
                    + row["discipline"]
                    + " : "
                    + str(row["total"])
                )

        else:

            result.append(
                "Aucune donnée."
            )

        self.ids.resultat.text = (
            "\n".join(result)
        )


# ============================================================
# APPLICATION
# ============================================================

class LabMatriceProfApp(App):

    app_name = "LabMatrice Prof V9"

    def build(self):

        self.title = self.app_name

        database_path = os.path.join(
            self.user_data_dir,
            "labmatrice_prof_v9.db"
        )

        self.db = Database(
            database_path
        )

        Builder.load_string('''
#:import dp kivy.metrics.dp

<Header@BoxLayout>:
    size_hint_y: None
    height: dp(58)
    padding: dp(6)
    spacing: dp(5)

    Label:
        text: app.app_name
        bold: True
        font_size: dp(18)

    Button:
        text: "Accueil"
        size_hint_x: None
        width: dp(90)
        on_release:
            app.root.current = "accueil"

<AccueilScreen>:
    BoxLayout:
        orientation: "vertical"
        Header:
        ScrollView:
            GridLayout:
                cols: 1
                spacing: dp(10)
                padding: dp(14)
                size_hint_y: None
                height: self.minimum_height

                Label:
                    text: "LABMATRICE PROF"
                    font_size: dp(29)
                    bold: True
                    size_hint_y: None
                    height: dp(60)

                Label:
                    text: "Assistant pédagogique V9"
                    font_size: dp(17)
                    size_hint_y: None
                    height: dp(40)

                GridLayout:
                    cols: 2
                    spacing: dp(7)
                    size_hint_y: None
                    height: dp(170)

                    Label:
                        id: total
                        text: "0\\nPréparations"
                        halign: "center"
                        valign: "middle"
                        text_size: self.size

                    Label:
                        id: finales
                        text: "0\\nFinalisées"
                        halign: "center"
                        valign: "middle"
                        text_size: self.size

                    Label:
                        id: brouillons
                        text: "0\\nBrouillons"
                        halign: "center"
                        valign: "middle"
                        text_size: self.size

                    Label:
                        id: canevas
                        text: "0\\nCanevas"
                        halign: "center"
                        valign: "middle"
                        text_size: self.size

                Button:
                    text: "➕ Nouvelle préparation"
                    size_hint_y: None
                    height: dp(58)
                    on_release:
                        root.new_fiche()

                Button:
                    text: "📚 Mes préparations"
                    size_hint_y: None
                    height: dp(58)
                    on_release:
                        app.root.current = "fiches"

                Button:
                    text: "🤖 Assistant pédagogique"
                    size_hint_y: None
                    height: dp(58)
                    on_release:
                        app.root.current = "assistant"

                Button:
                    text: "🧩 Gestion des canevas"
                    size_hint_y: None
                    height: dp(58)
                    on_release:
                        app.root.current = "canevas"

                Button:
                    text: "👤 Profil enseignant"
                    size_hint_y: None
                    height: dp(58)
                    on_release:
                        app.root.current = "profil"

                Button:
                    text: "📊 Statistiques"
                    size_hint_y: None
                    height: dp(58)
                    on_release:
                        app.root.current = "stats"

<ProfilScreen>:
    BoxLayout:
        orientation: "vertical"
        Header:
        ScrollView:
            GridLayout:
                cols: 1
                spacing: dp(8)
                padding: dp(14)
                size_hint_y: None
                height: self.minimum_height

                Label:
                    text: "PROFIL ENSEIGNANT"
                    font_size: dp(23)
                    bold: True
                    size_hint_y: None
                    height: dp(50)

                TextInput:
                    id: nom
                    hint_text: "Nom complet"
                    multiline: False
                    size_hint_y: None
                    height: dp(52)

                TextInput:
                    id: ecole
                    hint_text: "Établissement"
                    multiline: False
                    size_hint_y: None
                    height: dp(52)

                TextInput:
                    id: fonction
                    hint_text: "Fonction"
                    multiline: False
                    size_hint_y: None
                    height: dp(52)

                TextInput:
                    id: option
                    hint_text: "Option"
                    multiline: False
                    size_hint_y: None
                    height: dp(52)

                TextInput:
                    id: telephone
                    hint_text: "Téléphone"
                    multiline: False
                    size_hint_y: None
                    height: dp(52)

                TextInput:
                    id: email
                    hint_text: "Email"
                    multiline: False
                    size_hint_y: None
                    height: dp(52)

                Button:
                    text: "💾 Enregistrer"
                    size_hint_y: None
                    height: dp(58)
                    on_release:
                        root.save()

<NouvelleScreen>:
    BoxLayout:
        orientation: "vertical"
        Header:
        ScrollView:
            GridLayout:
                id: form
                cols: 1
                spacing: dp(8)
                padding: dp(12)
                size_hint_y: None
                height: self.minimum_height

<FichesScreen>:
    BoxLayout:
        orientation: "vertical"
        Header:
        BoxLayout:
            size_hint_y: None
            height: dp(55)
            spacing: dp(5)
            padding: dp(5)

            TextInput:
                id: recherche
                hint_text: "Rechercher une préparation..."
                multiline: False
                on_text_validate:
                    root.refresh()

            Button:
                text: "🔎"
                size_hint_x: None
                width: dp(60)
                on_release:
                    root.refresh()

        ScrollView:
            GridLayout:
                id: liste
                cols: 1
                spacing: dp(8)
                padding: dp(8)
                size_hint_y: None
                height: self.minimum_height

<DetailScreen>:
    BoxLayout:
        orientation: "vertical"
        Header:
        ScrollView:
            Label:
                id: contenu
                text: ""
                size_hint_y: None
                height: 1500
                text_size: self.width, None
                padding: dp(15), dp(15)

<AssistantScreen>:
    BoxLayout:
        orientation: "vertical"
        Header:
        ScrollView:
            GridLayout:
                cols: 1
                spacing: dp(8)
                padding: dp(12)
                size_hint_y: None
                height: self.minimum_height

                Label:
                    text: "ASSISTANT PÉDAGOGIQUE LOCAL"
                    font_size: dp(23)
                    bold: True
                    size_hint_y: None
                    height: dp(55)

                Label:
                    text: "Génération automatique basée sur le canevas enregistré.\\nCette fonction fonctionne hors connexion."
                    size_hint_y: None
                    height: dp(60)
                    text_size: self.width, None

                TextInput:
                    id: option
                    hint_text: "Option"
                    multiline: False
                    size_hint_y: None
                    height: dp(50)

                TextInput:
                    id: discipline
                    hint_text: "Discipline"
                    multiline: False
                    size_hint_y: None
                    height: dp(50)

                TextInput:
                    id: niveau
                    hint_text: "Classe / Niveau"
                    multiline: False
                    size_hint_y: None
                    height: dp(50)

                TextInput:
                    id: duree
                    hint_text: "Durée"
                    multiline: False
                    size_hint_y: None
                    height: dp(50)

                TextInput:
                    id: theme
                    hint_text: "Thème"
                    multiline: False
                    size_hint_y: None
                    height: dp(50)

                TextInput:
                    id: lecon
                    hint_text: "Titre de la leçon"
                    multiline: False
                    size_hint_y: None
                    height: dp(50)

                TextInput:
                    id: objectif
                    hint_text: "Objectif principal"
                    multiline: True
                    size_hint_y: None
                    height: dp(90)

                Button:
                    text: "🤖 Générer"
                    size_hint_y: None
                    height: dp(58)
                    on_release:
                        root.generate()

                Label:
                    id: resultat
                    text: ""
                    size_hint_y: None
                    height: dp(900)
                    text_size: self.width, None

                Button:
                    text: "✏️ Utiliser dans une fiche"
                    size_hint_y: None
                    height: dp(58)
                    on_release:
                        root.use_result()

<CanevasScreen>:
    BoxLayout:
        orientation: "vertical"
        Header:
        BoxLayout:
            size_hint_y: None
            height: dp(58)
            spacing: dp(5)
            padding: dp(5)

            TextInput:
                id: option
                hint_text: "Option"
                multiline: False

            TextInput:
                id: discipline
                hint_text: "Discipline"
                multiline: False

            Button:
                text: "Charger"
                size_hint_x: None
                width: dp(95)
                on_release:
                    root.load_current()

        ScrollView:
            GridLayout:
                id: contenu
                cols: 1
                spacing: dp(8)
                padding: dp(10)
                size_hint_y: None
                height: self.minimum_height

<StatsScreen>:
    BoxLayout:
        orientation: "vertical"
        Header:
        ScrollView:
            Label:
                id: resultat
                text: ""
                font_size: dp(17)
                text_size: self.width, None
                size_hint_y: None
                height: 900
                padding: dp(15), dp(15)
''')

        manager = ScreenManager()

        manager.add_widget(
            AccueilScreen(
                name="accueil"
            )
        )

        manager.add_widget(
            ProfilScreen(
                name="profil"
            )
        )

        manager.add_widget(
            NouvelleScreen(
                name="nouvelle"
            )
        )

        manager.add_widget(
            FichesScreen(
                name="fiches"
            )
        )

        manager.add_widget(
            DetailScreen(
                name="detail"
            )
        )

        manager.add_widget(
            AssistantScreen(
                name="assistant"
            )
        )

        manager.add_widget(
            CanevasScreen(
                name="canevas"
            )
        )

        manager.add_widget(
            StatsScreen(
                name="stats"
            )
        )

        return manager

    def message(
        self,
        titre,
        message
    ):

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10)
        )

        label = Label(
            text=str(message),
            text_size=(dp(310), None)
        )

        layout.add_widget(label)

        button = Button(
            text="OK",
            size_hint_y=None,
            height=dp(50)
        )

        layout.add_widget(button)

        popup = Popup(
            title=titre,
            content=layout,
            size_hint=(0.9, 0.45)
        )

        button.bind(
            on_release=popup.dismiss
        )

        popup.open()


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    LabMatriceProfApp().run()
