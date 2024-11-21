# servicios/servicio_docente.py
from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from datetime import datetime
from configuracion.firebase_config import inicializar_firebase

docente_bp = Blueprint('docente', __name__)
db = inicializar_firebase()
PROYECTOS = db.collection('proyectos')

@docente_bp.route('/mis-proyectos/<docente_id>', methods=['GET'])
def obtener_proyectos(docente_id):
    try:
        print(f"Obteniendo proyectos para docente_id: {docente_id}")  # Log
        proyectos = PROYECTOS.where('docente_id', '==', docente_id).get()
        return jsonify([{
            'id': p.id,
            **p.to_dict()
        } for p in proyectos])
    except Exception as e:
        print(f"Error: {e}")  # Log del error
        return jsonify({'error': str(e)}), 400


@docente_bp.route('/<proyecto_id>/comentar', methods=['POST'])
def comentar_proyecto(proyecto_id):
   try:
       datos = request.get_json()
       comentario = {
           'texto': datos.get('texto'),
           'docente_id': datos.get('docente_id'),
           'fecha': str(datetime.now())
       }
       
       PROYECTOS.document(proyecto_id).update({
           'comentarios_docente': firestore.ArrayUnion([comentario])
       })
       return jsonify({'mensaje': 'Comentario agregado exitosamente'})
   except Exception as e:
       return jsonify({'error': str(e)}), 400

@docente_bp.route('/<proyecto_id>/tarea/<tarea_id>/comentar', methods=['POST'])
def comentar_tarea(proyecto_id, tarea_id):
   try:
       datos = request.get_json()
       nuevo_comentario = {
           'texto': datos.get('texto'),
           'docente_id': datos.get('docente_id'),
           'fecha': str(datetime.now())
       }
       
       proyecto = PROYECTOS.document(proyecto_id).get().to_dict()
       tareas = proyecto.get('tareas', [])
       
       for i, tarea in enumerate(tareas):
           if tarea.get('id') == tarea_id:
               if 'comentarios_docente' not in tarea:
                   tarea['comentarios_docente'] = []
               tarea['comentarios_docente'].append(nuevo_comentario)
               
       PROYECTOS.document(proyecto_id).update({'tareas': tareas})
       return jsonify({'mensaje': 'Comentario agregado a la tarea'})
   except Exception as e:
       return jsonify({'error': str(e)}), 400

@docente_bp.route('/docente/<id>', methods=['GET'])
def obtener_docente(id):
    try:
        docente_ref = db.collection('usuarios').document(id)
        docente = docente_ref.get()

        if docente.exists:
            return jsonify(docente.to_dict())
        else:
            return jsonify({'error': 'Docente no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# Script de prueba
def test_docente():
   BASE_URL = 'http://localhost:5000/docente'
   DOCENTE_ID = {"uid"}  # ID del docente

   # Ver proyectos asignados
   response = requests.get(f'{BASE_URL}/mis-proyectos/{DOCENTE_ID}')
   print('Proyectos asignados:', response.json())

   if response.json():
       proyecto = response.json()[0]
       proyecto_id = proyecto['id']
       
       # Comentar proyecto
       comentario = {
           "texto": "Buen avance en el proyecto",
           "docente_id": DOCENTE_ID
       }
       response = requests.post(f'{BASE_URL}/{proyecto_id}/comentar', json=comentario)
       print('\nComentar proyecto:', response.json())
       
       # Comentar tarea
       if proyecto.get('tareas'):
           tarea = proyecto['tareas'][0]
           comentario_tarea = {
               "texto": "La tarea cumple con los objetivos",
               "docente_id": DOCENTE_ID
           }
           response = requests.post(
               f'{BASE_URL}/{proyecto_id}/tarea/{tarea["id"]}/comentar', 
               json=comentario_tarea
           )
           print('\nComentar tarea:', response.json())

if __name__ == '__main__':
   import requests
   test_docente()