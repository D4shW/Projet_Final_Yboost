const express = require('express');
const path = require('path');
const sqlite3 = require('sqlite3').verbose(); // Importation du module de base de données

const app = express();
const PORT = 3000;

// Connexion à une base de données SQLite en mémoire (temporaire pour le challenge)
const db = new sqlite3.Database(':memory:');

// Initialisation de la base de données avec des données fictives pour l'ANTS
db.serialize(() => {
    // Création d'une table d'utilisateurs
    db.run("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, password TEXT, role TEXT)");

    // Insertion d'un compte administrateur fictif que le joueur tentera de pirater
    db.run("INSERT INTO users (email, password, role) VALUES ('admin@ants.gouv.fr', 'SuperMotDePasseTresSecret2026!', 'admin')");
});

// Middlewares pour lire les formulaires et les fichiers statiques
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname, 'Connexion – France Titres (ANTS)_files')));

// Route principale qui affiche la page d'accueil / connexion
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'Connexion – France Titres (ANTS).html'));
});

// Route de connexion VULNÉRABLE à l'injection SQL
app.post('/login', (req, res) => {
    // Récupération des saisies de l'utilisateur
    const email = req.body.username || req.body.login || req.body.email;
    const password = req.body.password;

    console.log(`[Tentative] Email saisi : ${email}`);
    console.log(`[Tentative] Mot de passe saisi : ${password}`);

    // LA FAILLE : Construction de la requête SQL par concaténation de chaînes de caractères brutes.
    // Les variables de l'utilisateur sont insérées directement sans nettoyage ni requêtes préparées.
    const query = "SELECT * FROM users WHERE email = '" + email + "' AND password = '" + password + "'";

    console.log(`[SQL Exécuté] : ${query}`);

    // Exécution de la requête sur la base de données
    db.get(query, (err, row) => {
        if (err) {
            // En cas d'erreur de syntaxe SQL (ex: si le joueur met une apostrophe seule), on l'affiche.
            // C'est typique d'une injection SQL basée sur les erreurs (Error-based SQLi).
            return res.status(500).json({
                status: "error",
                message: "Erreur interne du serveur de base de données.",
                details: err.message
            });
        }

        if (row) {
            // Si la base de données retourne un utilisateur, la connexion réussit
            res.json({
                status: "success",
                message: `Bienvenue ${row.email}. Connexion réussie en tant que ${row.role} !`
            });
        } else {
            // Si aucun utilisateur ne correspond
            res.status(401).json({
                status: "fail",
                message: "Identifiant ou mot de passe incorrect."
            });
        }
    });
});

app.listen(PORT, () => {
    console.log(`====================================================`);
    console.log(` Serveur Challenge ANTS (VULNÉRABLE SQLi) démarré !`);
    console.log(` Adresse : http://localhost:${PORT}`);
    console.log(`====================================================`);
});