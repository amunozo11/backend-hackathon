from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from configuracion.firebase_config import inicializar_firebase
from datetime import datetime

programa_bp = Blueprint('programa', __name__)
db = inicializar_firebase()
PROYECTOS = db.collection('proyectos')

@programa_bp.route('/proyectos', methods=['POST'])
def crear_proyecto():
    try:
        datos = request.get_json()
        doc_ref = PROYECTOS.add({
            'titulo': datos.get('titulo'),
            'descripcion': datos.get('descripcion'),
            'fase': datos.get('fase'),
            'estado': datos.get('estado'),
            'fecha_inicio': datos.get('fecha_inicio'),
            'fecha_fin': datos.get('fecha_fin'),
            'director_id': datos.get('director_id'),
            'fecha_creacion': firestore.SERVER_TIMESTAMP,
            'comentarios': []
        })
        
        return jsonify({
            'mensaje': 'Proyecto creado exitosamente',
            'id': doc_ref[1].id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@programa_bp.route('/proyectos', methods=['GET'])
def listar_proyectos():
    try:
        proyectos = PROYECTOS.get()
        return jsonify([{
            'id': p.id,
            **p.to_dict()
        } for p in proyectos])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@programa_bp.route('/proyectos/<proyecto_id>/progreso', methods=['GET'])
def ver_progreso(proyecto_id):
    try:
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
        
        return jsonify({
            'id': proyecto.id,
            **proyecto.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# servicios/servicio_programa.py

@programa_bp.route('/proyectos/<proyecto_id>/comentario', methods=['POST'])
def agregar_comentario(proyecto_id):
    try:
        datos = request.get_json()
        comentario = {
            'texto': datos.get('texto'),
            'fecha': str(datetime.now()),  # Cambiado de SERVER_TIMESTAMP
            'autor_id': datos.get('autor_id')
        }
        
        PROYECTOS.document(proyecto_id).update({
            'comentarios': firestore.ArrayUnion([comentario])
        })
        
        return jsonify({'mensaje': 'Comentario agregado exitosamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@programa_bp.route('/estadisticas', methods=['GET'])
def obtener_estadisticas():
    try:
        proyectos = PROYECTOS.get()
        datos = {
            'total_proyectos': 0,
            'por_estado': {},
            'por_fase': {}
        }
        
        for proyecto in proyectos:
            datos['total_proyectos'] += 1
            p = proyecto.to_dict()
            
            estado = p.get('estado', 'sin_estado')
            fase = p.get('fase', 'sin_fase')
            
            datos['por_estado'][estado] = datos['por_estado'].get(estado, 0) + 1
            datos['por_fase'][fase] = datos['por_fase'].get(fase, 0) + 1
        
        return jsonify(datos)
    except Exception as e:
        return jsonify({'error': str(e)}), 400