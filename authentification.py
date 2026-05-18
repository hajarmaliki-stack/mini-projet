import tkinter as tk
from tkinter import messagebox
import hashlib
import sqlite3
import os

# ─── Base de données ────────────────────────────────────────────────────────

DB_PATH = "users.db"

def init_db():
    """Crée la base de données et un compte admin par défaut."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            role     TEXT    NOT NULL DEFAULT 'admin'
        )
    """)
    # Compte admin par défaut : admin / admin123
    mot_de_passe_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("""
        INSERT OR IGNORE INTO utilisateurs (username, password, role)
        VALUES (?, ?, ?)
    """, ("admin", mot_de_passe_hash, "admin"))
    conn.commit()
    conn.close()


def verifier_identifiants(username: str, password: str) -> bool:
    """Retourne True si l'utilisateur existe et le mot de passe est correct."""
    mot_de_passe_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id FROM utilisateurs WHERE username=? AND password=? AND role='admin'",
        (username, mot_de_passe_hash)
    )
    resultat = c.fetchone()
    conn.close()
    return resultat is not None


# ─── Interface graphique ─────────────────────────────────────────────────────

class FenetreConnexion:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Connexion Administrateur")
        self.root.resizable(False, False)
        self._centrer_fenetre(360, 220)
        self._construire_ui()

    # ── Centrage ──────────────────────────────────────────────────────────────
    def _centrer_fenetre(self, largeur: int, hauteur: int):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - largeur)  // 2
        y = (self.root.winfo_screenheight() - hauteur) // 2
        self.root.geometry(f"{largeur}x{hauteur}+{x}+{y}")

    # ── Construction des widgets ──────────────────────────────────────────────
    def _construire_ui(self):
        # ── Cadre principal avec relief classique ──
        cadre = tk.Frame(self.root, relief="groove", bd=2, padx=18, pady=16)
        cadre.pack(fill="both", expand=True, padx=10, pady=10)

        # Titre
        tk.Label(
            cadre,
            text="Espace Administrateur",
            font=("Arial", 11, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 14))

        # ── Champ Identifiant ──
        tk.Label(cadre, text="Identifiant :", anchor="w").grid(
            row=1, column=0, sticky="w", pady=4
        )
        self.var_user = tk.StringVar()
        self.champ_user = tk.Entry(cadre, textvariable=self.var_user, width=24)
        self.champ_user.grid(row=1, column=1, padx=(8, 0), pady=4)

        # ── Champ Mot de passe ──
        tk.Label(cadre, text="Mot de passe :", anchor="w").grid(
            row=2, column=0, sticky="w", pady=4
        )
        self.var_mdp = tk.StringVar()
        self.champ_mdp = tk.Entry(
            cadre, textvariable=self.var_mdp, show="●", width=24
        )
        self.champ_mdp.grid(row=2, column=1, padx=(8, 0), pady=4)

        # ── Case « Afficher le mot de passe » ──
        self.voir_mdp = tk.BooleanVar(value=False)
        tk.Checkbutton(
            cadre,
            text="Afficher le mot de passe",
            variable=self.voir_mdp,
            command=self._toggle_mdp,
        ).grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(2, 10))

        # ── Boutons ──
        cadre_boutons = tk.Frame(cadre)
        cadre_boutons.grid(row=4, column=0, columnspan=2)

        tk.Button(
            cadre_boutons,
            text="Connexion",
            width=12,
            command=self._connexion,
            default="active",
        ).pack(side="left", padx=6)

        tk.Button(
            cadre_boutons,
            text="Effacer",
            width=10,
            command=self._effacer,
        ).pack(side="left", padx=6)

        # ── Raccourcis clavier ──
        self.root.bind("<Return>", lambda _: self._connexion())
        self.root.bind("<Escape>", lambda _: self.root.destroy())

        # Focus initial
        self.champ_user.focus_set()

    # ── Actions ───────────────────────────────────────────────────────────────
    def _toggle_mdp(self):
        self.champ_mdp.config(show="" if self.voir_mdp.get() else "●")

    def _effacer(self):
        self.var_user.set("")
        self.var_mdp.set("")
        self.champ_user.focus_set()

    def _connexion(self):
        username = self.var_user.get().strip()
        password = self.var_mdp.get()

        if not username or not password:
            messagebox.showwarning(
                "Champs vides",
                "Veuillez saisir l'identifiant et le mot de passe.",
                parent=self.root,
            )
            return

        if verifier_identifiants(username, password):
            messagebox.showinfo(
                "Connexion réussie",
                f"Bienvenue, {username} !",
                parent=self.root,
            )
            self.root.destroy()
            ouvrir_application_principale(username)
        else:
            messagebox.showerror(
                "Échec de connexion",
                "Identifiant ou mot de passe incorrect.",
                parent=self.root,
            )
            self.var_mdp.set("")
            self.champ_mdp.focus_set()


# ─── Application principale (placeholder) ────────────────────────────────────

def ouvrir_application_principale(username: str):
    """Lance la fenêtre principale après authentification réussie."""
    app = tk.Tk()
    app.title("Application principale")
    app.geometry("400x260")
    tk.Label(
        app,
        text=f"Connecté en tant que : {username}",
        font=("Arial", 12, "bold"),
        pady=30,
    ).pack()
    tk.Label(
        app,
        text="Remplacez cette fenêtre par votre application.",
        fg="gray",
    ).pack()
    tk.Button(app, text="Quitter", command=app.destroy, width=12).pack(pady=20)
    app.mainloop()


# ─── Point d'entrée ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    FenetreConnexion(root)
    root.mainloop()
