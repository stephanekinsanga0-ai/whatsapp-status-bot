from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.models import User, Status
from datetime import date, datetime, timedelta

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """Obtenir un aperçu du tableau de bord"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        # Statistiques globales
        total_statuses = Status.query.filter_by(user_id=user_id).count()
        liked_statuses = Status.query.filter_by(user_id=user_id, liked=True).count()
        
        # Statistiques aujourd'hui
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        today_statuses = Status.query.filter(
            Status.user_id == user_id,
            Status.created_at >= datetime(today.year, today.month, today.day),
            Status.created_at < datetime(tomorrow.year, tomorrow.month, tomorrow.day)
        ).count()
        
        today_liked = Status.query.filter(
            Status.user_id == user_id,
            Status.liked == True,
            Status.created_at >= datetime(today.year, today.month, today.day),
            Status.created_at < datetime(tomorrow.year, tomorrow.month, tomorrow.day)
        ).count()
        
        # Taux de succès
        success_rate = (liked_statuses / total_statuses * 100) if total_statuses > 0 else 0
        
        return jsonify({
            'user': user.to_dict(),
            'subscription': user.subscription.to_dict() if user.subscription else None,
            'statistics': {
                'total_statuses': total_statuses,
                'liked_statuses': liked_statuses,
                'success_rate': round(success_rate, 2),
                'today': {
                    'statuses': today_statuses,
                    'liked': today_liked,
                    'remaining_limit': user.subscription.get_remaining_limit() if user.subscription else 0
                }
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/activity', methods=['GET'])
@jwt_required()
def get_activity():
    """Obtenir l'historique d'activité"""
    try:
        user_id = get_jwt_identity()
        days = request.args.get('days', 7, type=int)
        
        # Derniers N jours
        start_date = datetime.utcnow() - timedelta(days=days)
        
        statuses = Status.query.filter(
            Status.user_id == user_id,
            Status.created_at >= start_date
        ).order_by(Status.created_at.desc()).limit(100).all()
        
        # Grouper par jour
        activity_by_day = {}
        for status in statuses:
            day = status.created_at.date().isoformat()
            if day not in activity_by_day:
                activity_by_day[day] = {'total': 0, 'liked': 0}
            
            activity_by_day[day]['total'] += 1
            if status.liked:
                activity_by_day[day]['liked'] += 1
        
        return jsonify({
            'activity': activity_by_day,
            'total_records': len(statuses)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/contacts', methods=['GET'])
@jwt_required()
def get_contacts():
    """Obtenir la liste des contacts"""
    try:
        user_id = get_jwt_identity()
        
        # Récupérer les contacts uniques
        contacts = db.session.query(
            Status.contact_phone,
            Status.contact_name,
            db.func.count(Status.id).label('total'),
            db.func.sum(db.case((Status.liked == True, 1), else_=0)).label('liked')
        ).filter_by(user_id=user_id).group_by(
            Status.contact_phone,
            Status.contact_name
        ).all()
        
        contacts_list = []
        for contact in contacts:
            contacts_list.append({
                'phone': contact[0],
                'name': contact[1],
                'total_statuses': contact[2],
                'liked_statuses': contact[3] or 0
            })
        
        return jsonify({
            'contacts': contacts_list,
            'total_contacts': len(contacts_list)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/performance', methods=['GET'])
@jwt_required()
def get_performance():
    """Obtenir les métriques de performance"""
    try:
        user_id = get_jwt_identity()
        
        # Performance par jour de la semaine
        all_statuses = Status.query.filter_by(user_id=user_id).all()
        
        performance_by_weekday = {
            'Monday': {'total': 0, 'liked': 0},
            'Tuesday': {'total': 0, 'liked': 0},
            'Wednesday': {'total': 0, 'liked': 0},
            'Thursday': {'total': 0, 'liked': 0},
            'Friday': {'total': 0, 'liked': 0},
            'Saturday': {'total': 0, 'liked': 0},
            'Sunday': {'total': 0, 'liked': 0}
        }
        
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for status in all_statuses:
            weekday = weekdays[status.created_at.weekday()]
            performance_by_weekday[weekday]['total'] += 1
            if status.liked:
                performance_by_weekday[weekday]['liked'] += 1
        
        # Performance par heure
        performance_by_hour = {}
        for i in range(24):
            performance_by_hour[f"{i:02d}:00"] = {'total': 0, 'liked': 0}
        
        for status in all_statuses:
            hour = f"{status.created_at.hour:02d}:00"
            performance_by_hour[hour]['total'] += 1
            if status.liked:
                performance_by_hour[hour]['liked'] += 1
        
        return jsonify({
            'by_weekday': performance_by_weekday,
            'by_hour': performance_by_hour
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/export', methods=['GET'])
@jwt_required()
def export_data():
    """Exporter les données au format CSV"""
    try:
        user_id = get_jwt_identity()
        
        statuses = Status.query.filter_by(user_id=user_id).order_by(
            Status.created_at.desc()
        ).all()
        
        # Créer le CSV
        csv_data = "Date,Contact,Status,Liked\n"
        for status in statuses:
            csv_data += f"{status.created_at.isoformat()},{status.contact_name or status.contact_phone},\"@{status.whatsapp_status_id}\",{status.liked}\n"
        
        return jsonify({
            'data': csv_data,
            'filename': f"whatsapp_status_bot_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
