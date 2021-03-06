from config.conexion_bd import base_de_datos
from models.Tarea import TareaModel
from flask_restful import Resource, reqparse
from flask_jwt import current_identity, jwt_required
from cloudinary import CloudinaryImage


class TareasController(Resource):
    serializador = reqparse.RequestParser(bundle_errors=True)
    serializador.add_argument(
        'titulo',
        location='json',
        required=True,
        help='Falta el titulo',
        type=str
    )
    serializador.add_argument(
        'descripcion',
        location='json',
        required=True,
        help='Falta la descripcion',
        type=str
    )
    serializador.add_argument(
        'tags',
        type=list,
        required=True,
        help='Falta los tags',
        location='json'
    )
    serializador.add_argument(
        'estado',
        choices=['POR_HACER', 'HACIENDO', 'FINALIZADO'],
        type=str,
        help='Falta el estado',
        required=True,
        location='json'
    )
    serializador.add_argument(
            'imagen',
            location='json',
            required=False,
            help='Falta imagen',
            type=str
        )

    @jwt_required()
    def post(self):
        data = self.serializador.parse_args()
        try:
            nuevaTarea = TareaModel()
            nuevaTarea.tareaDescripcion = data.get('descripcion')
            nuevaTarea.tareaEstado = data.get('estado')
            nuevaTarea.tareaTags = data.get('tags')
            nuevaTarea.tareaTitulo = data.get('titulo')
            nuevaTarea.usuario = current_identity.get('usuarioId')
            if data.get('imagen'):
                nuevaTarea.tareaImagen = data.get('imagen')
            else:
                nuevaTarea.tareaImagen = None

            base_de_datos.session.add(nuevaTarea)
            base_de_datos.session.commit()
            print(current_identity)
            return {
                "message": "Tarea creada exitosamente",
                "content": {
                    "tareaId": nuevaTarea.tareaId,
                    "tareaDescripcion": nuevaTarea.tareaDescripcion,
                    "tareaEstado": nuevaTarea.tareaEstado.value,
                    "tareaTags": nuevaTarea.tareaTags,
                    "tareaTitulo": nuevaTarea.tareaTitulo,
                    "tareaFechaCreacion": str(nuevaTarea.tareaFechaCreacion),
                    "usuario": nuevaTarea.usuario,
                    "tareaImagen": nuevaTarea.tareaImagen,
                }
            }, 201
        except Exception as e:
            base_de_datos.session.rollback()
            return{
                "message": "Error al crear la tarea",
                "content": e.args
            }, 400

    @jwt_required()
    def get(self):
        tareasEncontradas = base_de_datos.session.query(TareaModel).filter(
            TareaModel.usuario == current_identity.get('usuarioId')).all()
        resultado = []
        for tarea in tareasEncontradas:
            tareaDict = tarea.__dict__.copy()
            del tareaDict['_sa_instance_state']
            tareaDict['tareaFechaCreacion'] = str(
                tareaDict['tareaFechaCreacion'])

            respuestaCD = CloudinaryImage(tarea.tareaImagen)

            #.image(transformation=[
            #{'background': "#ce6767", 'border': "17px_solid_rgb:000", 'height': 310, 'quality': 46, 'radius': 14, 'width': 634, 'zoom': "1.8", 'crop': "scale"},
            #{'angle': 185}
            #])
            print(respuestaCD.url)
            tareaDict['tareaEstado'] = tareaDict['tareaEstado'].value
            tareaDict["tareaImagen"] = respuestaCD.url

            resultado.append(tareaDict)
        # devolver todas las tareas correspondiente al usuario del current_identity
        return{
            "message": None,
            "content": resultado
        }
