from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum

class UserRole(Enum):
    """Rôles des utilisateurs"""
    USER = "user"
    ADMIN = "admin"

class User(db.Model):
    """Modèle utilisateur"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Profil
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    profile_picture = db.Column(db.String(500))
    
    # Statut
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relations
    subscription = db.relationship('Subscription', backref='user', uselist=False, cascade='all, delete-orphan')
    statuses = db.relationship('Status', backref='user', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hasher et stocker le mot de passe"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifier le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
        }


class SubscriptionTier(Enum):
    """Niveaux d'abonnement"""
    FREE = "free"
    PREMIUM = "premium"

class Subscription(db.Model):
    """Modèle d'abonnement"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    tier = db.Column(db.Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    
    # Limites
    status_limit = db.Column(db.Integer)  # None = illimité
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # None = pas d'expiration
    
    is_active = db.Column(db.Boolean, default=True)
    
    def is_expired(self):
        """Vérifier si l'abonnement a expiré"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def get_remaining_limit(self):
        """Obtenir la limite restante pour le jour"""
        if self.tier == SubscriptionTier.PREMIUM:
            return float('inf')
        
        from datetime import date, timedelta
        from sqlalchemy import and_
        
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        count = Status.query.filter(
            and_(
                Status.user_id == self.user_id,
                Status.created_at >= datetime(today.year, today.month, today.day),
                Status.created_at < datetime(tomorrow.year, tomorrow.month, tomorrow.day)
            )
        ).count()
        
        limit = 20  # FREE_TIER_LIMIT
        return max(0, limit - count)
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'tier': self.tier.value,
            'status_limit': self.status_limit,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
        }


class Status(db.Model):
    """Modèle pour les statuts WhatsApp"""
    __tablename__ = 'statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Données du statut
    whatsapp_status_id = db.Column(db.String(255), unique=True, index=True)
    contact_name = db.Column(db.String(255))
    contact_phone = db.Column(db.String(20))
    
    # Médias
    media_url = db.Column(db.String(500))
    media_type = db.Column(db.String(50))  # image, video, text
    
    # Interactions
    liked = db.Column(db.Boolean, default=False)
    liked_at = db.Column(db.DateTime)
    
    # Statut
    viewed = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default='pending')  # pending, liked, failed
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'media_type': self.media_type,
            'liked': self.liked,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
        }
