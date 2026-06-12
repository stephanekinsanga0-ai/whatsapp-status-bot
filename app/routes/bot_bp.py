from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
import os
from datetime import datetime
from app import db
from app.models.models import User, Status
from app.services.whatsapp_service import WhatsAppService

bp = Blueprint('bot', __name__, url_prefix='/api/bot')

@bp.route('/webhook', methods=['POST', 'GET'])
def webhook():
    """Webhook WhatsApp Business API"""
    
    if request.method == 'GET':
        # Vérifier le webhook
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if verify_token == os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN'):
            return challenge
        return 'Invalid token', 403
    
    if request.method == 'POST':
        # Traiter les événements WhatsApp
        data = request.get_json()
        
        try:
            if 'entry' in data:
                for entry in data['entry']:
                    if 'changes' in entry:
                        for change in entry['changes']:
                            if change['field'] == 'messages':
                                value = change['value']
                                if 'messages' in value:
                                    for message in value['messages']:
                                        WhatsAppService.handle_message(message, value)
                            
                            elif change['field'] == 'statuses':
                                value = change['value']
                                if 'statuses' in value:
                                    for status in value['statuses']:
                                        WhatsAppService.handle_status(status)
            
            return jsonify({'status': 'ok'}), 200
        
        except Exception as e:
            print(f"Erreur webhook: {str(e)}")
            return jsonify({'status': 'error', 'error': str(e)}), 500


@bp.route('/auto-like/start', methods=['POST'])
@jwt_required()
def start_auto_like():
    """Démarrer l'auto-like pour l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        # Vérifier les limites d'abonnement
        if user.subscription.tier.value == 'free':
            # Vérifier la limite de 20 statuts par jour
            remaining = user.subscription.get_remaining_limit()
            if remaining <= 0:
                return jsonify({'error': 'Limite de 20 statuts par jour atteinte. Passez à Premium pour un accès illimité.'}), 403
        
        data = request.get_json()
        contact_phone = data.get('contact_phone')
        
        if not contact_phone:
            return jsonify({'error': 'Numéro de téléphone requis'}), 400
        
        # Démarrer l'auto-like
        result = WhatsAppService.start_auto_like(user_id, contact_phone)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify({'error': result.get('error', 'Erreur lors du démarrage')}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/auto-like/stop', methods=['POST'])
@jwt_required()
def stop_auto_like():
    """Arrêter l'auto-like"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        data = request.get_json()
        contact_phone = data.get('contact_phone')
        
        if not contact_phone:
            return jsonify({'error': 'Numéro de téléphone requis'}), 400
        
        result = WhatsAppService.stop_auto_like(user_id, contact_phone)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify({'error': result.get('error', 'Erreur lors de l\'arrêt')}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/statuses', methods=['GET'])
@jwt_required()
def get_statuses():
    """Obtenir la liste des statuts"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_filter = request.args.get('status', 'all')
        
        query = Status.query.filter_by(user_id=user_id)
        
        if status_filter != 'all':
            query = query.filter_by(status=status_filter)
        
        statuses = query.order_by(Status.created_at.desc()).paginate(
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'statuses': [s.to_dict() for s in statuses.items],
            'total': statuses.total,
            'pages': statuses.pages,
            'current_page': page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Obtenir les statistiques d'utilisation"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        # Compter les statuts traités
        total_statuses = Status.query.filter_by(user_id=user_id).count()
        liked_statuses = Status.query.filter_by(user_id=user_id, liked=True).count()
        failed_statuses = Status.query.filter_by(user_id=user_id, status='failed').count()
        
        # Compter les statuts d'aujourd'hui
        from datetime import date, datetime as dt, timedelta
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        today_statuses = Status.query.filter(
            Status.user_id == user_id,
            Status.created_at >= dt(today.year, today.month, today.day),
            Status.created_at < dt(tomorrow.year, tomorrow.month, tomorrow.day)
        ).count()
        
        return jsonify({
            'total_statuses': total_statuses,
            'liked_statuses': liked_statuses,
            'failed_statuses': failed_statuses,
            'today_statuses': today_statuses,
            'subscription_tier': user.subscription.tier.value,
            'remaining_limit': user.subscription.get_remaining_limit() if user.subscription.tier.value == 'free' else 'unlimited'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
