# WhatsApp Status Bot 🤖

## Vue d'ensemble

Un bot WhatsApp Business multi-utilisateurs avec système d'auto-like de statuts, gestion des plans gratuit/premium et intégration de paiement pour la RDC.

### Fonctionnalités 🚀

#### Mode Gratuit
- ✅ Auto-like des statuts (max 20 par jour)
- ✅ Tableau de bord basique
- ✅ Statistiques de base
- ✅ Support via WhatsApp

#### Mode Premium (Illimité)
- ✅ Auto-like illimité
- ✅ Tableau de bord complet
- ✅ Analyses avancées
- ✅ Export de données
- ✅ Gestion multi-contacts
- ✅ Priorité support

### Modes de Paiement 💳

- **PayPal** - International
- **Orange Money RDC** - Numéro: 0815376622
- **Vodacom RDC** - Numéro: 0815376622

Tous supportent l'ajout de compte bancaire pour le paiement.

## Stack Technologique

- **Backend**: Python 3.9+
- **Framework**: Flask
- **Base de données**: PostgreSQL
- **API**: WhatsApp Business API
- **Paiements**: PayPal, Orange Money, Vodacom
- **Authentification**: JWT + OAuth2
- **Déploiement**: Docker, Heroku/AWS

## Installation

### Prérequis

- Python 3.9+
- PostgreSQL 12+
- Compte WhatsApp Business
- Clés API (PayPal, Orange Money, Vodacom)

### Étapes d'installation

```bash
# 1. Cloner le projet
git clone https://github.com/stephanekinsanga0-ai/whatsapp-status-bot.git
cd whatsapp-status-bot

# 2. Créer l'environnement virtuel
python -m venv venv

# Sur Linux/Mac:
source venv/bin/activate

# Sur Windows:
venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# 5. Initialiser la base de données
flask db upgrade

# 6. Lancer l'application
python run.py
```

L'application sera disponible sur `http://localhost:5000`

## Configuration

### Variables d'environnement

Copier `.env.example` en `.env` et remplir:

```env
# Serveur
FLASK_ENV=development
SECRET_KEY=votre_clé_secrète
DEBUG=False

# Base de données
DATABASE_URL=postgresql://user:password@localhost:5432/whatsapp_bot

# JWT
JWT_SECRET_KEY=votre_jwt_secret

# WhatsApp
WHATSAPP_API_TOKEN=votre_token
WHATSAPP_PHONE_NUMBER_ID=votre_phone_id
WHATSAPP_BUSINESS_ACCOUNT_ID=votre_account_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=votre_verify_token

# PayPal
PAYPAL_CLIENT_ID=votre_client_id
PAYPAL_CLIENT_SECRET=votre_secret

# Orange Money RDC
ORANGE_MONEY_RDC_API_KEY=votre_api_key
ORANGE_MONEY_RDC_MERCHANT_KEY=votre_merchant_key

# Vodacom RDC
VODACOM_RDC_API_KEY=votre_api_key
VODACOM_RDC_MERCHANT_ID=votre_merchant_id
```

## Structure du Projet

```
whatsapp-status-bot/
├── app/
│   ├── __init__.py                 # Factory Flask
│   ├── config.py                   # Configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── models.py              # User, Subscription, Status
│   │   └── payment.py             # Payment
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_bp.py             # Auth (register, login, profile)
│   │   ├── bot_bp.py              # Bot (webhook, auto-like)
│   │   ├── payment_bp.py          # Payments
│   │   └── dashboard_bp.py        # Dashboard
│   └── services/
│       ├── __init__.py
│       ├── payment_service.py     # PayPal, Orange, Vodacom
│       └── whatsapp_service.py    # WhatsApp interactions
├── requirements.txt
├── run.py
├── .env.example
├── .gitignore
└── README.md
```

## API Endpoints

### Authentification

```bash
# Inscription
POST /api/auth/register
{
  "username": "user123",
  "email": "user@example.com",
  "password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe"
}

# Connexion
POST /api/auth/login
{
  "username_or_email": "user@example.com",
  "password": "SecurePass123"
}

# Profil
GET /api/auth/profile
PUT /api/auth/profile
POST /api/auth/change-password
```

### Paiements

```bash
# Obtenir les méthodes
GET /api/payment/methods

# Mettre à niveau vers Premium
POST /api/payment/upgrade
{
  "payment_method": "ORANGE_MONEY_RDC",
  "bank_account": "123456789"
}

# Historique
GET /api/payment/transactions

# Détails abonnement
GET /api/payment/subscription
```

### Bot WhatsApp

```bash
# Démarrer auto-like
POST /api/bot/auto-like/start
{
  "contact_phone": "+243814000000"
}

# Arrêter auto-like
POST /api/bot/auto-like/stop
{
  "contact_phone": "+243814000000"
}

# Statuts traités
GET /api/bot/statuses

# Statistiques
GET /api/bot/stats

# Webhook
POST /api/bot/webhook
```

### Tableau de bord

```bash
# Aperçu
GET /api/dashboard/overview

# Activité
GET /api/dashboard/activity?days=7

# Contacts
GET /api/dashboard/contacts

# Performance
GET /api/dashboard/performance

# Export CSV
GET /api/dashboard/export
```

## Webhooks

### WhatsApp Webhook

Configurer l'URL webhook: `https://votre-domaine.com/api/bot/webhook`

Token de vérification: `WHATSAPP_WEBHOOK_VERIFY_TOKEN`

### Webhooks de paiement

- **PayPal**: `POST /api/payment/webhook/paypal`
- **Orange Money**: `POST /api/payment/webhook/orange-money`
- **Vodacom**: `POST /api/payment/webhook/vodacom`

## Déploiement

### Docker

```bash
# Build
docker build -t whatsapp-status-bot .

# Run
docker run -p 5000:5000 --env-file .env whatsapp-status-bot
```

### Docker Compose

```bash
# Lancer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

### Heroku

```bash
# Créer l'app
heroku create whatsapp-status-bot

# Config
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=votre_clé

# Push
git push heroku main
```

## Support & Contribution

Pour toute question ou contribution:
- 📧 Email: support@example.com
- 💬 WhatsApp: +243 815 376 622
- 🐛 Issues: GitHub Issues

## License

MIT License - Voir LICENSE pour les détails

## Auteur

[stephanekinsanga0-ai](https://github.com/stephanekinsanga0-ai)

---

**⚠️ Note**: Assurez-vous de configurer correctement les clés API avant de déployer en production.
