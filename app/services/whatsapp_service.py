import requests
import os
from datetime import datetime
from app import db
from app.models.models import Status, User, Subscription

class WhatsAppService:
    """Service pour gérer l'auto-like WhatsApp"""
    
    API_TOKEN = os.getenv('WHATSAPP_API_TOKEN')
    PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    BUSINESS_ACCOUNT_ID = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
    BASE_URL = "https://graph.instagram.com/v18.0"
    
    @staticmethod
    def get_statuses(contact_phone):
        """Récupérer les statuts WhatsApp d'un contact"""
        try:
            headers = {
                'Authorization': f'Bearer {WhatsAppService.API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            # Utiliser l'API WhatsApp Business
            url = f"{WhatsAppService.BASE_URL}/{WhatsAppService.PHONE_NUMBER_ID}/statuses"
            
            params = {
                'recipient_type': 'individual',
                'recipient_id': contact_phone
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return response.json().get('data', [])
            
            return []
        
        except Exception as e:
            print(f"Erreur lors de la récupération des statuts: {str(e)}")
            return []
    
    @staticmethod
    def like_status(status_id, contact_phone):
        """Aimer un statut WhatsApp"""
        try:
            headers = {
                'Authorization': f'Bearer {WhatsAppService.API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            url = f"{WhatsAppService.BASE_URL}/{status_id}/reactions"
            
            payload = {
                'emoji': '❤️'
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return True
            
            return False
        
        except Exception as e:
            print(f"Erreur lors du like du statut: {str(e)}")
            return False
    
    @staticmethod
    def start_auto_like(user_id, contact_phone):
        """Démarrer l'auto-like pour un utilisateur"""
        try:
            user = User.query.get(user_id)
            
            if not user:
                return {'success': False, 'error': 'Utilisateur non trouvé'}
            
            # Récupérer les statuts du contact
            statuses = WhatsAppService.get_statuses(contact_phone)
            
            liked_count = 0
            failed_count = 0
            
            for status in statuses:
                status_id = status.get('id')
                
                # Créer l'enregistrement du statut
                db_status = Status(
                    user_id=user_id,
                    whatsapp_status_id=status_id,
                    contact_phone=contact_phone,
                    contact_name=status.get('sender_name', contact_phone),
                    media_url=status.get('media', {}).get('url'),
                    media_type=status.get('type', 'text'),
                    status='pending'
                )
                
                # Essayer d'aimer le statut
                if WhatsAppService.like_status(status_id, contact_phone):
                    db_status.liked = True
                    db_status.liked_at = datetime.utcnow()
                    db_status.status = 'liked'
                    liked_count += 1
                else:
                    db_status.status = 'failed'
                    failed_count += 1
                
                db.session.add(db_status)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Auto-like terminé: {liked_count} aimés, {failed_count} échoués',
                'liked_count': liked_count,
                'failed_count': failed_count,
                'total': len(statuses)
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def stop_auto_like(user_id, contact_phone):
        """Arrêter l'auto-like"""
        try:
            # Marquer les statuts du contact comme arrêtés
            statuses = Status.query.filter_by(
                user_id=user_id,
                contact_phone=contact_phone,
                status='pending'
            ).all()
            
            for status in statuses:
                status.status = 'cancelled'
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Auto-like arrêté pour {contact_phone}',
                'stopped_count': len(statuses)
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def handle_message(message_data, contact_data):
        """Traiter les messages WhatsApp entrants"""
        try:
            # Extraire les informations du message
            message_id = message_data.get('id')
            from_number = message_data.get('from')
            message_type = message_data.get('type')
            timestamp = message_data.get('timestamp')
            
            # Ici, vous pouvez ajouter votre logique pour répondre aux messages
            print(f"Nouveau message reçu: {message_id} de {from_number}")
            
        except Exception as e:
            print(f"Erreur lors du traitement du message: {str(e)}")
    
    @staticmethod
    def handle_status(status_data):
        """Traiter les changements de statut WhatsApp"""
        try:
            # Extraire les informations du statut
            status_id = status_data.get('id')
            status_value = status_data.get('status')
            timestamp = status_data.get('timestamp')
            
            print(f"Changement de statut: {status_id} -> {status_value}")
            
        except Exception as e:
            print(f"Erreur lors du traitement du statut: {str(e)}")
