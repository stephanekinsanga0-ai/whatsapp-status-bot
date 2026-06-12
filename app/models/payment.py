from app import db
from datetime import datetime
from enum import Enum

class PaymentMethod(Enum):
    """Modes de paiement disponibles"""
    PAYPAL = "paypal"
    ORANGE_MONEY_RDC = "orange_money_rdc"
    VODACOM_RDC = "vodacom_rdc"

class PaymentStatus(Enum):
    """Statuts du paiement"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Payment(db.Model):
    """Modèle pour les paiements"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Détails du paiement
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    
    # Statut
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Références externes
    transaction_id = db.Column(db.String(255), unique=True, index=True)
    reference_id = db.Column(db.String(255), index=True)
    
    # Détails du paiement
    details = db.Column(db.JSON)  # Stockage flexible pour les détails API
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Notes
    notes = db.Column(db.Text)
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method.value,
            'status': self.status.value,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
