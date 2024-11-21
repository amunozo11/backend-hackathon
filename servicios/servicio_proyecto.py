# servicios/servicio_proyecto.py
from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from datetime import datetime
from configuracion.firebase_config import inicializar_firebase

proyecto_bp = Blueprint('proyecto', __name__)
db = inicializar_firebase()
PROYECTOS = db.collection('proyectos')
USUARIOS = db.collection('usuarios')

@proyecto_bp.route('/crear', methods=['POST'])
def crear_proyecto():
   try:
       datos = request.get_json()
       

       docente_data = None
       if datos.get('docente_id'):
           docente_ref = USUARIOS.document(datos.get('docente_id')).get()
           if docente_ref.exists:
               docente_data = docente_ref.to_dict()
               docente_data['uid'] = docente_ref.id  # Añadir el ID del docente
           else:
               return jsonify({'error': 'Docente no encontrado'}), 404


       doc_ref = PROYECTOS.add({
           'titulo': datos.get('titulo'),
           'descripcion': datos.get('descripcion'),
           "fases": {
               "planificacion": {"completada": False, "entregas": []},
               "desarrollo": {"completada": False, "entregas": []},
               "evaluacion": {"completada": False, "entregas": []}
           },
           'estado': 'activo',
           'fecha_inicio': datos.get('fecha_inicio'),
           'fecha_fin': datos.get('fecha_fin'),
           'lider_id': datos.get('lider_id'),
           'docente_id': datos.get('docente_id'),
           'docente': docente_data,  # Guardar toda la información del docente
           'colaboradores': datos.get('colaboradores_id'),
           'tareas': [],
           'fecha_creacion': str(datetime.now())
       })
       
       return jsonify({
           'mensaje': 'Proyecto creado exitosamente',
           'id': doc_ref[1].id
       })
   except Exception as e:
       return jsonify({'error': str(e)}), 400
   

@proyecto_bp.route('/proyecto/<proyecto_id>/nueva-tarea', methods=['POST'])
def crear_tarea(proyecto_id):
    try:
        datos = request.get_json()
        tarea = {
            'id': str(datetime.now().timestamp()),  # Agregar ID único
            'titulo': datos.get('titulo'),
            'descripcion': datos.get('descripcion'),
            'asignado_a': datos.get('asignado_a'),
            'fecha_inicio': datos.get('fecha_inicio'),
            'fecha_fin': datos.get('fecha_fin'),
            'estado': 'pendiente',
            'fecha_creacion': str(datetime.now()),
            'comentarios_docente': []
        }
        
        PROYECTOS.document(proyecto_id).update({
            'tareas': firestore.ArrayUnion([tarea])
        })
        
        return jsonify({'mensaje': 'Tarea creada exitosamente', 'tarea': tarea})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/<proyecto_id>/docente', methods=['POST'])
def asignar_docente(proyecto_id):
   try:
       datos = request.get_json()
       docente_id = datos.get('docente_id')
       
       # Verificar que el docente existe y es docente
       docente = USUARIOS.document(docente_id).get()
       if not docente.exists or docente.get('rol') != 'docente_guia':
           return jsonify({'error': 'Docente no válido'}), 400
           
       PROYECTOS.document(proyecto_id).update({
           'docente_id': docente_id
       })
       
       return jsonify({'mensaje': 'Docente asignado exitosamente'})
   except Exception as e:
       return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/<proyecto_id>/colaborador', methods=['POST'])
def asignar_colaborador(proyecto_id):
   try:
       datos = request.get_json()
       colaborador_id = datos.get('colaborador_id')
       
       # Verificar que el colaborador existe
       colaborador = USUARIOS.document(colaborador_id).get()
       if not colaborador.exists or colaborador.get('rol') != 'colaborador':
           return jsonify({'error': 'Colaborador no válido'}), 400
           
       PROYECTOS.document(proyecto_id).update({
           'colaboradores': firestore.ArrayUnion([colaborador_id])
       })
       
       return jsonify({'mensaje': 'Colaborador asignado exitosamente'})
   except Exception as e:
       return jsonify({'error': str(e)}), 400
   
# Función para obtener el progreso de un proyecto
@proyecto_bp.route('/<proyecto_id>/avance', methods=['GET'])
def ver_avance(proyecto_id):
    try:
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
        
        proyecto_data = proyecto.to_dict()
        avance = {}

        # Calculamos el progreso de cada fase
        for fase, datos_fase in proyecto_data['fases'].items():
            total_entregas = len(datos_fase['entregas'])
            entregas_completadas = sum(1 for e in datos_fase['entregas'] if e.get('fecha_entrega') <= datetime.now().strftime('%Y-%m-%d'))
            porcentaje_completado = (entregas_completadas / total_entregas) * 100 if total_entregas > 0 else 0
            avance[fase] = {
                "porcentaje_completado": porcentaje_completado,
                "total_entregas": total_entregas,
                "entregas_completadas": entregas_completadas
            }

        return jsonify({'avance': avance}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/<proyecto_id>/fase/<fase>/entrega', methods=['POST'])
def agregar_entrega(proyecto_id, fase):
    try:
        # Verificar si la fase existe
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
        
        proyecto_data = proyecto.to_dict()
        
        if fase not in proyecto_data['fases']:
            return jsonify({'error': 'Fase no válida'}), 400
        
        # Obtener los datos de la entrega
        datos = request.get_json()
        entrega = {
            'id': str(datetime.now().timestamp()),  # ID único
            'titulo': datos.get('titulo'),
            'fecha_entrega': datos.get('fecha_entrega'),
            'archivo': datos.get('archivo')  # Si se sube un archivo, se maneja aquí
        }
        
        # Agregar la entrega a la fase correspondiente
        PROYECTOS.document(proyecto_id).update({
            f'fases.{fase}.entregas': firestore.ArrayUnion([entrega])
        })
        
        return jsonify({'mensaje': 'Entrega agregada exitosamente', 'entrega': entrega}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/<proyecto_id>/fase/<fase>/completar', methods=['POST'])
def completar_fase(proyecto_id, fase):
    try:
        # Verificar si el proyecto existe
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404

        proyecto_data = proyecto.to_dict()

        # Verificar que la fase sea válida
        if fase not in proyecto_data['fases']:
            return jsonify({'error': 'Fase no válida'}), 400

        # Verificar si todas las entregas de la fase están completadas
        entregas = proyecto_data['fases'][fase]['entregas']
        if all(e.get('fecha_entrega') <= datetime.now().strftime('%Y-%m-%d') for e in entregas):
            # Marcar la fase como completada
            PROYECTOS.document(proyecto_id).update({
                f'fases.{fase}.completada': True
            })
            return jsonify({'mensaje': f'Fase {fase} completada exitosamente'}), 200
        else:
            return jsonify({'error': f'No todas las entregas de la fase {fase} han sido completadas'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/<proyecto_id>', methods=['GET'])
def obtener_proyecto(proyecto_id):
    try:
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404

        proyecto_data = proyecto.to_dict()
        return jsonify({'proyecto': proyecto_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/proyectos', methods=['GET'])
def obtener_proyectos():
    try:
        proyectos = PROYECTOS.stream()  # Obtener todos los documentos de la colección
        lista_proyectos = [{**doc.to_dict(), 'id': doc.id} for doc in proyectos]
        
        return jsonify({'proyectos': lista_proyectos}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/lider/<lider_id>', methods=['GET'])
def obtener_proyectos_lider(lider_id):
    try:
        # Verificar que el líder existe
        lider = USUARIOS.document(lider_id).get()
        if not lider.exists:
            return jsonify({'error': 'Líder no encontrado'}), 404
            
        # Obtener todos los proyectos donde el usuario es líder
        proyectos = PROYECTOS.where('lider_id', '==', lider_id).stream()
        
        # Convertir los proyectos a una lista de diccionarios
        proyectos_data = []
        for proyecto in proyectos:
            data = proyecto.to_dict()
            data['id'] = proyecto.id  # Agregar el ID del documento
            proyectos_data.append(data)
            
        return jsonify({
            'proyectos': proyectos_data,
            'total': len(proyectos_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    