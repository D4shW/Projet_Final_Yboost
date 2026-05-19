"""
Initialise la base de données ANTS-Lab avec des utilisateurs fictifs.
Objectif CTF : exfiltrer l'intégralité de la BDD via la chaîne d'exploitation.
"""
import os
import sqlite3
import random

DB_PATH = "/app/data/ants.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

PRENOMS = [
    "Jean", "Marie", "Pierre", "Sophie", "Lucas", "Emma", "Hugo", "Léa",
    "Thomas", "Chloé", "Nicolas", "Camille", "Antoine", "Julie", "Maxime",
    "Sarah", "Alexandre", "Manon", "Romain", "Pauline", "Julien", "Clara",
    "Vincent", "Inès", "Damien", "Océane", "Florian", "Mathilde", "Benjamin",
    "Anaïs", "Sébastien", "Lola", "Mathieu", "Zoé", "Adrien", "Eva",
    "Quentin", "Margaux", "Baptiste", "Élise", "Théo", "Jade", "Arthur",
    "Louise", "Raphaël", "Alice", "Gabriel", "Charlotte", "Léo", "Rose"
]
NOMS = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit",
    "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel",
    "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier", "Morel",
    "Girard", "André", "Mercier", "Blanc", "Guerin", "Boyer", "Garnier",
    "Chevalier", "Francois", "Legrand", "Gauthier", "Roussel", "Lemoine"
]
VILLES = [
    "Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Lille",
    "Bordeaux", "Strasbourg", "Rennes", "Montpellier", "Le Havre", "Reims",
    "Saint-Étienne", "Toulon", "Grenoble", "Dijon", "Angers", "Nîmes"
]
TYPES_DOSSIER = [
    "Demande de passeport en cours d'instruction.",
    "CNI délivrée — duplicata en attente d'envoi.",
    "Permis de conduire — renouvellement demandé.",
    "Certificat d'immatriculation — changement de propriétaire.",
    "Dossier en attente de justificatif de domicile.",
    "Pièces complémentaires demandées au demandeur.",
    "Titre prêt à être retiré en mairie.",
    "Demande validée — envoi sous 10 jours ouvrés.",
    "Aucune note particulière.",
    "Dossier transmis à la préfecture.",
]

# Comptes fixes connus (pour SQLi et pour le compte de démo)
FIXED_USERS = [
    (1, "demo", "demo123", "user", "Dupont", "Marie", "1985-03-12",
     "ANTS-2024-0001", "12 rue de la République, Paris",
     "Demande de renouvellement de CNI en cours."),
    (2, "admin", "P@ssw0rd_4n7s_2025!", "admin", "Admin", "ANTS",
     "1970-01-01", "ANTS-ADMIN-0000", "Place Beauvau, Paris",
     "Compte administrateur — accès complet aux dossiers."),
]

# Nombre total de users à générer (modifiable selon la difficulté voulue)
TOTAL_USERS = 100


def init():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")
    c.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            nom TEXT,
            prenom TEXT,
            date_naissance TEXT,
            numero_titre TEXT,
            adresse TEXT,
            note_dossier TEXT
        )
    """)

    random.seed(42)  # seed fixe pour reproductibilité — change-le si tu veux randomiser entre instances
    rows = list(FIXED_USERS)

    # Génération des comptes utilisateurs fictifs (IDs 3 à TOTAL_USERS, contigus)
    for i in range(3, TOTAL_USERS + 1):
        prenom = random.choice(PRENOMS)
        nom = random.choice(NOMS)
        ville = random.choice(VILLES)
        rows.append((
            i,
            f"{prenom.lower()}.{nom.lower()}{random.randint(1, 99)}",
            f"pw_{random.randint(10000, 99999)}",
            "user",
            nom,
            prenom,
            f"19{random.randint(50, 99)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            f"ANTS-{random.randint(2020, 2025)}-{i:04d}",
            f"{random.randint(1, 200)} {random.choice(['rue', 'avenue', 'boulevard'])} "
            f"{random.choice(NOMS)}, {ville}",
            random.choice(TYPES_DOSSIER)
        ))

    c.executemany("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
    print(f"DB initialisée — {len(rows)} utilisateurs (IDs 1 à {TOTAL_USERS}).")


if __name__ == "__main__":
    init()
