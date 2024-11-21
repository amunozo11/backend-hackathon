from flask import Blueprint, request, jsonify
from firebase_admin import auth, firestore
from configuracion.firebase_config import inicializar_firebase

auth_bp = Blueprint('auth', __name__)
db = inicializar_firebase()
USUARIOS = db.collection('usuarios')

@auth_bp.route('/registro', methods=['POST'])
def registro():
    try:
        datos = request.get_json()
        email = datos.get('email')
        password = datos.get('password')
        nombre = datos.get('nombre')
        rol = datos.get('rol')

        # Validar rol
        roles_permitidos = ['admin', 'director_programa', 'lider_proyecto', 'colaborador', 'docente_guia']
        if rol not in roles_permitidos:
            return jsonify({
                'error': 'Rol inválido. Los roles permitidos son: admin, director_programa, lider_proyecto, colaborador, docente_guia'
            }), 400

        usuario = auth.create_user(
            email=email,
            password=password,
            display_name=nombre
        )

        # Por defecto los usuarios están pendientes de aprobación, excepto admin
        aprobado = rol == 'admin'
        
        USUARIOS.document(usuario.uid).set({
            'uid': usuario.uid,
            'email': email,
            'nombre': nombre,
            'rol': rol,
            'aprobado': aprobado,
            'fecha_registro': firestore.SERVER_TIMESTAMP
        })

        mensaje = 'Usuario registrado exitosamente'
        if not aprobado:
            mensaje += '. Pendiente de aprobación por un administrador'

        return jsonify({
            'mensaje': mensaje,
            'uid': usuario.uid,
            'aprobado': aprobado
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        datos = request.get_json()
        email = datos.get('email')
        password = datos.get('password')

        usuario = auth.get_user_by_email(email)
        usuario_data = USUARIOS.document(usuario.uid).get().to_dict()

        # Verificar si el usuario está aprobado
        if not usuario_data.get('aprobado', False) and usuario_data.get('rol') != 'admin':
            return jsonify({'error': 'Usuario pendiente de aprobación'}), 403

        return jsonify({
            'uid': usuario.uid,
            'email': email,
            'nombre': usuario_data.get('nombre'),
            'rol': usuario_data.get('rol')
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Credenciales inválidas'}), 401

@auth_bp.route('/admin/usuarios-pendientes', methods=['GET'])
def obtener_usuarios_pendientes():
    try:
        usuarios = USUARIOS.where('aprobado', '==', False).get()
        usuarios_data = [{
            'uid': user.id,
            'nombre': user.get('nombre'),
            'email': user.get('email'),
            'rol': user.get('rol')
        } for user in usuarios]
        return jsonify(usuarios_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/admin/aprobar/<uid>', methods=['POST'])
def aprobar_usuario(uid):
    try:
        USUARIOS.document(uid).update({
            'aprobado': True
        })
        return jsonify({'mensaje': 'Usuario aprobado exitosamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/admin/usuarios', methods=['GET'])
def listar_usuarios():
    try:
        usuarios = USUARIOS.get()
        usuarios_data = []
        for user in usuarios:
            data = user.to_dict()
            data['uid'] = user.id
            usuarios_data.append(data)
        return jsonify(usuarios_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400