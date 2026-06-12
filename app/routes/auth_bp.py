from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from app import db
from app.models.models import User, Subscription, SubscriptionTier
import re

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def validate_email(email):
    """Valider le format d'email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Valider la force du mot de passe"""
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    if not any(char.isupper() for char in password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    if not any(char.isdigit() for char in password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    return True, ""

@bp.route('/register', methods=['POST'])
def register():
    """Enregistrer un nouvel utilisateur"""
    try:
        data = request.get_json()
        
        # Validation des données
        if not data:
            return jsonify({'error': 'Données manquantes'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Tous les champs sont obligatoires'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Email invalide'}), 400
        
        valid, msg = validate_password(password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Le nom d\'utilisateur doit contenir au moins 3 caractères'}), 400
        
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Ce nom d\'utilisateur existe déjà'}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Cet email est déjà utilisé'}), 409
        
        # Créer l'utilisateur
        user = User(
            username=username,
            email=email,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', '')
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()  # Pour obtenir l'ID de l'utilisateur
        
        # Créer un abonnement gratuit par défaut
        subscription = Subscription(
            user_id=user.id,
            tier=SubscriptionTier.FREE,
            status_limit=20,
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return jsonify({
            'message': 'Utilisateur créé avec succès',
            'user': user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/login', methods=['POST'])
def login():
    """Connecter un utilisateur"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données manquantes'}), 400
        
        username_or_email = data.get('username_or_email', '').strip()
        password = data.get('password', '')
        
        if not username_or_email or not password:
            return jsonify({'error': 'Identifiants ou mot de passe manquants'}), 400
        
        # Chercher l'utilisateur par username ou email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Identifiants ou mot de passe incorrects'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Ce compte a été désactivé'}), 403
        
        # Mettre à jour la dernière connexion
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Créer le token JWT
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(days=1)
        )
        
        return jsonify({
            'message': 'Connexion réussie',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Obtenir le profil de l'utilisateur connecté"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        profile = user.to_dict()
        if user.subscription:
            profile['subscription'] = user.subscription.to_dict()
        
        return jsonify(profile), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Mettre à jour le profil de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        data = request.get_json()
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        
        if 'last_name' in data:
            user.last_name = data['last_name']
        
        if 'phone' in data:
            phone = data['phone'].strip()
            if phone and User.query.filter_by(phone=phone).filter(User.id != user_id).first():
                return jsonify({'error': 'Ce numéro de téléphone est déjà utilisé'}), 409
            user.phone = phone if phone else None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profil mis à jour avec succès',
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Changer le mot de passe de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        data = request.get_json()
        
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Les mots de passe sont obligatoires'}), 400
        
        if not user.check_password(old_password):
            return jsonify({'error': 'Ancien mot de passe incorrect'}), 401
        
        valid, msg = validate_password(new_password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'message': 'Mot de passe changé avec succès'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Déconnecter l'utilisateur"""
    # En théorie, avec JWT, il n'y a pas vraiment de logout côté serveur
    # Mais on peut enregistrer la déconnexion pour les logs
    return jsonify({'message': 'Déconnexion réussie'}), 200
