import requests
import os
from datetime import datetime, timedelta
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app import db

class PaymentService:
    """Service centralisé pour les paiements"""
    
    @staticmethod
    def process_payment(user_id, amount, payment_method, bank_account=None, currency='USD'):
        """Traiter un paiement selon la méthode"""
        
        if payment_method == PaymentMethod.PAYPAL:
            return PayPalService.process_payment(user_id, amount, currency)
        
        elif payment_method == PaymentMethod.ORANGE_MONEY_RDC:
            return OrangeMoneyService.process_payment(user_id, amount, currency, bank_account)
        
        elif payment_method == PaymentMethod.VODACOM_RDC:
            return VodacomService.process_payment(user_id, amount, currency, bank_account)
        
        else:
            raise ValueError(f"Méthode de paiement non supportée: {payment_method}")
    
    @staticmethod
    def verify_payment(transaction_id, payment_method):
        """Vérifier le statut d'un paiement"""
        
        if payment_method == PaymentMethod.PAYPAL:
            return PayPalService.verify_payment(transaction_id)
        
        elif payment_method == PaymentMethod.ORANGE_MONEY_RDC:
            return OrangeMoneyService.verify_payment(transaction_id)
        
        elif payment_method == PaymentMethod.VODACOM_RDC:
            return VodacomService.verify_payment(transaction_id)


class PayPalService:
    """Service PayPal"""
    
    BASE_URL = "https://api.sandbox.paypal.com" if os.getenv('PAYPAL_MODE') == 'sandbox' else "https://api.paypal.com"
    CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
    CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
    
    @staticmethod
    def get_access_token():
        """Obtenir un token d'accès PayPal"""
        auth = (PayPalService.CLIENT_ID, PayPalService.CLIENT_SECRET)
        headers = {'Accept': 'application/json'}
        data = {'grant_type': 'client_credentials'}
        
        response = requests.post(
            f"{PayPalService.BASE_URL}/v1/oauth2/token",
            auth=auth,
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            return response.json()['access_token']
        raise Exception("Erreur lors de l'authentification PayPal")
    
    @staticmethod
    def process_payment(user_id, amount, currency='USD'):
        """Créer un paiement PayPal"""
        try:
            token = PayPalService.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'intent': 'sale',
                'payer': {'payment_method': 'paypal'},
                'transactions': [{
                    'amount': {
                        'total': str(amount),
                        'currency': currency,
                        'details': {'subtotal': str(amount)}
                    },
                    'description': 'Premium Subscription - WhatsApp Status Bot'
                }],
                'redirect_urls': {
                    'return_url': os.getenv('PAYPAL_RETURN_URL'),
                    'cancel_url': os.getenv('PAYPAL_CANCEL_URL')
                }
            }
            
            response = requests.post(
                f"{PayPalService.BASE_URL}/v1/payments/payment",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 201:
                data = response.json()
                
                # Créer l'enregistrement de paiement
                payment = Payment(
                    user_id=user_id,
                    amount=amount,
                    currency=currency,
                    payment_method=PaymentMethod.PAYPAL,
                    status=PaymentStatus.PENDING,
                    transaction_id=data['id'],
                    details={'links': data['links']},
                    reference_id=data['id']
                )
                db.session.add(payment)
                db.session.commit()
                
                # Retourner le lien d'approbation
                approval_link = next((link['href'] for link in data['links'] if link['rel'] == 'approval_url'), None)
                return {'success': True, 'approval_url': approval_link, 'transaction_id': data['id']}
            
            return {'success': False, 'error': response.text}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def verify_payment(transaction_id):
        """Vérifier un paiement PayPal"""
        try:
            token = PayPalService.get_access_token()
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(
                f"{PayPalService.BASE_URL}/v1/payments/payment/{transaction_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        
        except Exception as e:
            return None


class OrangeMoneyService:
    """Service Orange Money RDC"""
    
    API_URL = os.getenv('ORANGE_MONEY_RDC_API_URL', 'https://api.orange.cd/money')
    API_KEY = os.getenv('ORANGE_MONEY_RDC_API_KEY')
    MERCHANT_KEY = os.getenv('ORANGE_MONEY_RDC_MERCHANT_KEY')
    SANDBOX = os.getenv('ORANGE_MONEY_RDC_SANDBOX', 'true').lower() == 'true'
    PAYMENT_NUMBER = '0815376622'
    
    @staticmethod
    def process_payment(user_id, amount, currency='USD', bank_account=None):
        """Traiter un paiement Orange Money"""
        try:
            headers = {
                'Authorization': f'Bearer {OrangeMoneyService.API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'merchant_key': OrangeMoneyService.MERCHANT_KEY,
                'amount': str(amount),
                'currency': 'CDF' if currency == 'USD' else currency,
                'description': 'Premium Subscription',
                'reference': f"WHATSAPP_BOT_{user_id}_{datetime.utcnow().timestamp()}",
                'country': 'CD',
                'sandbox': OrangeMoneyService.SANDBOX,
                'payment_number': OrangeMoneyService.PAYMENT_NUMBER,
                'bank_account': bank_account
            }
            
            response = requests.post(
                f"{OrangeMoneyService.API_URL}/v1/payment/create",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                payment = Payment(
                    user_id=user_id,
                    amount=amount,
                    currency='CDF',
                    payment_method=PaymentMethod.ORANGE_MONEY_RDC,
                    status=PaymentStatus.PENDING,
                    transaction_id=data.get('transaction_id'),
                    reference_id=data.get('reference'),
                    payment_number=OrangeMoneyService.PAYMENT_NUMBER,
                    bank_account=bank_account,
                    details=data
                )
                db.session.add(payment)
                db.session.commit()
                
                return {'success': True, 'transaction_id': data.get('transaction_id'), 'payment_url': data.get('payment_url')}
            
            return {'success': False, 'error': response.text}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def verify_payment(transaction_id):
        """Vérifier un paiement Orange Money"""
        try:
            headers = {
                'Authorization': f'Bearer {OrangeMoneyService.API_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{OrangeMoneyService.API_URL}/v1/payment/status/{transaction_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        
        except Exception as e:
            return None


class VodacomService:
    """Service Vodacom RDC"""
    
    API_URL = os.getenv('VODACOM_RDC_API_URL', 'https://api.vodacom.cd')
    API_KEY = os.getenv('VODACOM_RDC_API_KEY')
    MERCHANT_ID = os.getenv('VODACOM_RDC_MERCHANT_ID')
    SANDBOX = os.getenv('VODACOM_RDC_SANDBOX', 'true').lower() == 'true'
    PAYMENT_NUMBER = '0815376622'
    
    @staticmethod
    def process_payment(user_id, amount, currency='USD', bank_account=None):
        """Traiter un paiement Vodacom"""
        try:
            headers = {
                'Authorization': f'Bearer {VodacomService.API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'merchant_id': VodacomService.MERCHANT_ID,
                'amount': str(amount),
                'currency': 'CDF' if currency == 'USD' else currency,
                'reference': f"WHATSAPP_BOT_{user_id}_{datetime.utcnow().timestamp()}",
                'description': 'Premium Subscription - WhatsApp Status Bot',
                'country': 'CD',
                'sandbox': VodacomService.SANDBOX,
                'payment_number': VodacomService.PAYMENT_NUMBER,
                'bank_account': bank_account
            }
            
            response = requests.post(
                f"{VodacomService.API_URL}/v1/payment/create",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                payment = Payment(
                    user_id=user_id,
                    amount=amount,
                    currency='CDF',
                    payment_method=PaymentMethod.VODACOM_RDC,
                    status=PaymentStatus.PENDING,
                    transaction_id=data.get('transaction_id'),
                    reference_id=data.get('reference'),
                    payment_number=VodacomService.PAYMENT_NUMBER,
                    bank_account=bank_account,
                    details=data
                )
                db.session.add(payment)
                db.session.commit()
                
                return {'success': True, 'transaction_id': data.get('transaction_id'), 'payment_url': data.get('payment_url')}
            
            return {'success': False, 'error': response.text}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def verify_payment(transaction_id):
        """Vérifier un paiement Vodacom"""
        try:
            headers = {
                'Authorization': f'Bearer {VodacomService.API_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{VodacomService.API_URL}/v1/payment/status/{transaction_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        
        except Exception as e:
            return None
