from flask import Flask
from flask_cors import CORS
from configuracion.firebase_config import inicializar_firebase
from servicios.servicio_email import auth_bp
from servicios.servicio_programa import programa_bp
from servicios.servicio_proyecto import proyecto_bp
from servicios.servicio_colaborador import colaborador_bp
from servicios.servicio_docente import docente_bp
from servicios.servicio_director import director_bp

app = Flask(__name__)
CORS(app)

# Configurar CORS para permitir solicitudes solo de tu frontend específico
CORS(app, origins=["http://localhost:5173"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Inicializar Firebase
db = inicializar_firebase()

# Registrar blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(programa_bp, url_prefix='/programa')
app.register_blueprint(proyecto_bp, url_prefix='/proyecto')
app.register_blueprint(colaborador_bp, url_prefix='/colaborador')
app.register_blueprint(docente_bp, url_prefix='/docente')
app.register_blueprint(director_bp, url_prefix='/director')

@app.route('/test')
def test():
    return {'mensaje': 'Servidor funcionando correctamente'}

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)