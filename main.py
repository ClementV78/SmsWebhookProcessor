from flask import Flask, request, jsonify
import jwt
import os

app = Flask(__name__)

# Obtenir la clé de signature depuis une variable d'environnement
SIGNING_KEY = os.environ.get('SIGNING_KEY', 'clé_par_défaut')

@app.route('/', methods=['POST'])
def receive_webhook():
    print('Requête reçue')
    # Vérifier l'en-tête Authorization
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        print(f"Requête non autorisée: {auth_header}")
        return 'Unauthorized', 401

    token = auth_header[7:]  # Supprimer 'Bearer '

    # Valider le token JWT
    try:
        payload = jwt.decode(token, SIGNING_KEY, algorithms=['HS256'])
    except jwt.InvalidTokenError as e:
        print(f"Token invalide: {str(e)}")
        return f'Invalid token: {str(e)}', 401

    # Vérifier le type d'événement
    event_type = request.headers.get('X-Event-Type')
    print(f"Type d'événement: {event_type}")
    if event_type != 'message.phone.received':
        return 'Unsupported event type', 400

    # Traiter le contenu du webhook
    event_data = request.get_json()
    print(f"Contenu du webhook: {event_data}")
    if not event_data:
        return 'Invalid JSON payload', 400

    # Extraire les informations du message
    message_data = event_data.get('data', {})
    contact = message_data.get('contact')
    content = message_data.get('content')
    timestamp = message_data.get('timestamp')

    # Afficher les données reçues
    print(f"Nouveau message reçu de {contact} à {timestamp}: {content}")

    # Répondre avec un statut 200 OK
    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8181)
