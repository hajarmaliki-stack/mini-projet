import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3
import hashlib
import csv
import os

DB_PATH = "contacts.db"


# ─── Base de données ──────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Table des contacts
    c.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nom       TEXT NOT NULL,
            telephone TEXT NOT NULL
        )
    """)

    # Table des administrateurs
    c.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role     TEXT NOT NULL DEFAULT 'admin'
        )
    """)

    # Admin par défaut : admin / admin123
    mdp_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("""
        INSERT OR IGNORE INTO utilisateurs (username, password, role)
        VALUES (?, ?, 'admin')
    """, ("admin", mdp_hash))

    conn.commit()
    conn.close()


# ─── CRUD Contacts ─────────────────────────────────────────────────────────────

def get_contacts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, nom, telephone FROM contacts ORDER BY nom")
    rows = c.fetchall()
    conn.close()
    return rows

def ajouter_contact(nom, telephone):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO contacts (nom, telephone) VALUES (?, ?)", (nom, telephone))
    conn.commit()
    conn.close()

def modifier_contact(contact_id, nom, telephone):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE contacts SET nom=?, telephone=? WHERE id=?", (nom, telephone, contact_id))
    conn.commit()
    conn.close()

def supprimer_contact(contact_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM contacts WHERE id=?", (contact_id,))
    conn.commit()
    conn.close()

def exporter_csv(chemin):
    contacts = get_contacts()
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["ID", "Nom", "Téléphone"])
        writer.writerows(contacts)

def importer_csv(chemin):
    with open(chemin, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        compteur = 0
        for row in reader:
            nom = row.get("Nom", "").strip()
            tel = row.get("Téléphone", "").strip()
            if nom and tel:
                c.execute(
                    "INSERT OR IGNORE INTO contacts (nom, telephone) VALUES (?, ?)",
                    (nom, tel)
                )
                compteur += 1
        conn.commit()
        conn.close()
    return compteur


# ─── Authentification ─────────────────────────────────────────────────────────

def verifier_identifiants(username, password):
    mdp_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id FROM utilisateurs WHERE username=? AND password=? AND role='admin'",
        (username, mdp_hash)
    )
    res = c.fetchone()
    conn.close()
    return res is not None


# ─── Fenêtre de connexion ──────────────────────────────────────────────────────

class FenetreConnexion:
    def __init__(self, root):
        self.root = root
        self.root.title("Connexion – Allo !")
        self.root.resizable(False, False)
        self._centrer(360, 220)
        self._construire()

    def _centrer(self, w, h):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _construire(self):
        cadre = tk.Frame(self.root, relief="groove", bd=2, padx=18, pady=16)
        cadre.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(cadre, text="Espace Administrateur", font=("Arial", 11, "bold")
                 ).grid(row=0, column=0, columnspan=2, pady=(0, 14))

        tk.Label(cadre, text="Identifiant :").grid(row=1, column=0, sticky="w", pady=4)
        self.var_user = tk.StringVar()
        tk.Entry(cadre, textvariable=self.var_user, width=24
                 ).grid(row=1, column=1, padx=(8, 0), pady=4)

        tk.Label(cadre, text="Mot de passe :").grid(row=2, column=0, sticky="w", pady=4)
        self.var_mdp = tk.StringVar()
        self.champ_mdp = tk.Entry(cadre, textvariable=self.var_mdp, show="●", width=24)
        self.champ_mdp.grid(row=2, column=1, padx=(8, 0), pady=4)

        self.voir_mdp = tk.BooleanVar()
        tk.Checkbutton(cadre, text="Afficher le mot de passe",
                       variable=self.voir_mdp, command=self._toggle_mdp
                       ).grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(2, 10))

        f = tk.Frame(cadre)
        f.grid(row=4, column=0, columnspan=2)
        tk.Button(f, text="Connexion", width=12, command=self._connexion,
                  default="active").pack(side="left", padx=6)
        tk.Button(f, text="Effacer",   width=10, command=self._effacer
                  ).pack(side="left", padx=6)

        self.root.bind("<Return>", lambda _: self._connexion())
        self.root.bind("<Escape>", lambda _: self.root.destroy())

    def _toggle_mdp(self):
        self.champ_mdp.config(show="" if self.voir_mdp.get() else "●")

    def _effacer(self):
        self.var_user.set("")
        self.var_mdp.set("")

    def _connexion(self):
        u = self.var_user.get().strip()
        p = self.var_mdp.get()
        if not u or not p:
            messagebox.showwarning("Champs vides",
                                   "Veuillez remplir tous les champs.", parent=self.root)
            return
        if verifier_identifiants(u, p):
            self.root.destroy()
            lancer_app(u)
        else:
            messagebox.showerror("Échec", "Identifiant ou mot de passe incorrect.",
                                 parent=self.root)
            self.var_mdp.set("")


# ─── Application principale – Gestion des contacts ───────────────────────────

class AppContacts:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.contact_selectionne_id = None

        self.root.title("Allo !")
        self.root.resizable(False, False)
        self._centrer(420, 420)
        self._construire()
        self._charger_liste()

    def _centrer(self, w, h):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ── Construction de l'interface ───────────────────────────────────────────
    def _construire(self):
        # ── Barre de menu ──
        menubar = tk.Menu(self.root)
        menu_fichier = tk.Menu(menubar, tearoff=0)
        menu_fichier.add_command(label="Exporter en CSV", command=self._exporter_csv)
        menu_fichier.add_command(label="Importer depuis CSV", command=self._importer_csv)
        menu_fichier.add_separator()
        menu_fichier.add_command(label="Quitter", command=self.root.destroy)
        menubar.add_cascade(label="Fichier", menu=menu_fichier)
        self.root.config(menu=menubar)

        # ── Cadre infos contact ──
        cadre_info = tk.LabelFrame(self.root, text=" Contact ", relief="groove",
                                   bd=2, padx=10, pady=8)
        cadre_info.pack(fill="x", padx=10, pady=(10, 4))

        tk.Label(cadre_info, text="Nom :", width=8, anchor="w").grid(
            row=0, column=0, sticky="w", pady=4)
        self.var_nom = tk.StringVar()
        tk.Entry(cadre_info, textvariable=self.var_nom, width=28).grid(
            row=0, column=1, padx=(4, 0), pady=4)

        tk.Label(cadre_info, text="Tél :", width=8, anchor="w").grid(
            row=1, column=0, sticky="w", pady=4)
        self.var_tel = tk.StringVar()
        tk.Entry(cadre_info, textvariable=self.var_tel, width=28).grid(
            row=1, column=1, padx=(4, 0), pady=4)

        tk.Button(cadre_info, text="Effacer", width=10, command=self._effacer_champs
                  ).grid(row=2, column=1, sticky="e", pady=(4, 0))

        # ── Liste des contacts ──
        cadre_liste = tk.Frame(self.root, relief="groove", bd=2)
        cadre_liste.pack(fill="both", expand=True, padx=10, pady=4)

        scrollbar = tk.Scrollbar(cadre_liste, orient="vertical")
        self.listbox = tk.Listbox(
            cadre_liste,
            yscrollcommand=scrollbar.set,
            selectmode="single",
            activestyle="dotbox",
            font=("Courier", 10),
            height=10,
        )
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_selection)

        # ── Barre de recherche ──
        cadre_rech = tk.Frame(self.root)
        cadre_rech.pack(fill="x", padx=10, pady=(2, 4))
        tk.Label(cadre_rech, text="Rechercher :").pack(side="left")
        self.var_rech = tk.StringVar()
        self.var_rech.trace_add("write", lambda *_: self._charger_liste())
        tk.Entry(cadre_rech, textvariable=self.var_rech, width=22).pack(
            side="left", padx=(4, 0))

        # ── Boutons d'action ──
        cadre_btn = tk.Frame(self.root)
        cadre_btn.pack(pady=8)
        for texte, cmd in [
            ("Ajouter",    self._ajouter),
            ("Modifier",   self._modifier),
            ("Supprimer",  self._supprimer),
            ("Afficher",   self._afficher),
        ]:
            tk.Button(cadre_btn, text=texte, width=10, command=cmd
                      ).pack(side="left", padx=5)

        # Statut
        self.var_statut = tk.StringVar(value=f"Connecté : {self.username}")
        tk.Label(self.root, textvariable=self.var_statut, fg="gray",
                 anchor="w").pack(fill="x", padx=10, pady=(0, 4))

    # ── Chargement / filtrage ─────────────────────────────────────────────────
    def _charger_liste(self):
        self.listbox.delete(0, tk.END)
        self._contacts = get_contacts()
        filtre = self.var_rech.get().lower() if hasattr(self, "var_rech") else ""
        self._contacts_affiches = [
            c for c in self._contacts if filtre in c[1].lower()
        ]
        for _, nom, tel in self._contacts_affiches:
            self.listbox.insert(tk.END, f"{nom:<25} {tel}")
        self.var_statut.set(
            f"Connecté : {self.username}  |  {len(self._contacts_affiches)} contact(s)"
        )

    def _on_selection(self, event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        contact_id, nom, tel = self._contacts_affiches[idx]
        self.contact_selectionne_id = contact_id
        self.var_nom.set(nom)
        self.var_tel.set(tel)

    # ── Actions CRUD ─────────────────────────────────────────────────────────
    def _effacer_champs(self):
        self.var_nom.set("")
        self.var_tel.set("")
        self.contact_selectionne_id = None
        self.listbox.selection_clear(0, tk.END)

    def _ajouter(self):
        nom = self.var_nom.get().strip()
        tel = self.var_tel.get().strip()
        if not nom or not tel:
            messagebox.showwarning("Champs vides",
                                   "Veuillez saisir le nom et le téléphone.",
                                   parent=self.root)
            return
        ajouter_contact(nom, tel)
        self._effacer_champs()
        self._charger_liste()

    def _modifier(self):
        if self.contact_selectionne_id is None:
            messagebox.showinfo("Aucune sélection",
                                "Sélectionnez un contact à modifier.",
                                parent=self.root)
            return
        nom = self.var_nom.get().strip()
        tel = self.var_tel.get().strip()
        if not nom or not tel:
            messagebox.showwarning("Champs vides",
                                   "Veuillez saisir le nom et le téléphone.",
                                   parent=self.root)
            return
        modifier_contact(self.contact_selectionne_id, nom, tel)
        self._effacer_champs()
        self._charger_liste()

    def _supprimer(self):
        if self.contact_selectionne_id is None:
            messagebox.showinfo("Aucune sélection",
                                "Sélectionnez un contact à supprimer.",
                                parent=self.root)
            return
        nom = self.var_nom.get()
        if not messagebox.askyesno("Confirmation",
                                   f"Supprimer « {nom} » ?",
                                   parent=self.root):
            return
        supprimer_contact(self.contact_selectionne_id)
        self._effacer_champs()
        self._charger_liste()

    def _afficher(self):
        if self.contact_selectionne_id is None:
            messagebox.showinfo("Aucune sélection",
                                "Sélectionnez un contact à afficher.",
                                parent=self.root)
            return
        nom = self.var_nom.get()
        tel = self.var_tel.get()
        messagebox.showinfo("Contact",
                            f"Nom       : {nom}\nTéléphone : {tel}",
                            parent=self.root)

    # ── CSV ───────────────────────────────────────────────────────────────────
    def _exporter_csv(self):
        chemin = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous", "*.*")],
            title="Exporter les contacts",
            parent=self.root,
        )
        if not chemin:
            return
        exporter_csv(chemin)
        messagebox.showinfo("Export réussi",
                            f"Contacts exportés dans :\n{chemin}",
                            parent=self.root)

    def _importer_csv(self):
        chemin = filedialog.askopenfilename(
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous", "*.*")],
            title="Importer des contacts",
            parent=self.root,
        )
        if not chemin:
            return
        try:
            n = importer_csv(chemin)
            messagebox.showinfo("Import réussi",
                                f"{n} contact(s) importé(s).",
                                parent=self.root)
            self._charger_liste()
        except Exception as e:
            messagebox.showerror("Erreur d'import", str(e), parent=self.root)


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def lancer_app(username):
    app = tk.Tk()
    AppContacts(app, username)
    app.mainloop()

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    FenetreConnexion(root)
    root.mainloop()
