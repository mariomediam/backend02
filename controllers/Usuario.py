from flask_restful import Resource, reqparse, request
from re import search
from bcrypt import hashpw, gensalt, checkpw
from models.Usuario import UsuarioModel
from config.conexion_bd import base_de_datos
from flask_jwt import jwt_required, current_identity
from sqlalchemy.exc import IntegrityError
from cryptography.fernet import Fernet
from os import environ
from datetime import datetime, timedelta
from json import dumps
from config.enviar_correo import enviarCorreo
from utils.patrones import PATRON_CORREO, PATRON_PASSWORD


class RegistroController(Resource):
    serializador = reqparse.RequestParser(bundle_errors=True)
    serializador.add_argument(
        'nombre',
        type=str,
        location='json',
        required=True,
        help='Falta el nombre'
    )

    serializador.add_argument(
        'apellido',
        type=str,
        location='json',
        required=True,
        help='Falta el apellido'
    )

    serializador.add_argument(
        'correo',
        type=str,
        location='json',
        required=True,
        help='Falta el correo'
    )

    serializador.add_argument(
        'password',
        type=str,
        location='json',
        required=True,
        help='Falta el password'
    )

    serializador.add_argument(
        'telefono',
        type=str,
        location='json',
        required=True,
        help='Falta el telefono'
    )

    def post(self):
        data = self.serializador.parse_args()
        print(data)
        correo = data['correo']
        password = data['password']
        if search(PATRON_CORREO, correo) is None:
            return {
                "message": "Correo incorrecto"
            }, 400

        if search(PATRON_PASSWORD, password) is None:
            return {
                "message": "Password incorrecto, minimo 6 caracteres una mayuscula, una minuscula y un simbolo especial"
            }, 400
        try:
            nuevoUsuario = UsuarioModel()
            nuevoUsuario.usuarioCorreo = correo
            nuevoUsuario.usuarioNombre = data.get('nombre')
            nuevoUsuario.usuarioTelefono = data.get('telefono')
            nuevoUsuario.usuarioApellido = data.get('apellido')
            # Encriptacion de la contrase??a
            # Primero convertimos la pwd a formato bytes
            passwordBytes = bytes(password, "utf-8")
            # llamamos al metodo gensalt que nos dara un salt aleatorio en base al numero de rounds
            salt = gensalt(rounds=10)
            # hashpw que lo que hara sera combinar nuestras pwd con el salt generado previamente
            hashPwd = hashpw(passwordBytes, salt)
            # convertimos el hash a formato string para poder almacenarlo en la bd
            hashPwd = hashPwd.decode('utf-8')
            # almacenamos el hashpwd
            nuevoUsuario.usuarioPassword = hashPwd
            base_de_datos.session.add(nuevoUsuario)
            base_de_datos.session.commit()
            return {
                "message": "Usuario creado exitosamente"
            }, 201
        except Exception as e:
            base_de_datos.session.rollback()
            return {
                "message": "Error al ingresar el usuario",
                "content": e.args
            }, 500


class LoginController(Resource):
    serializador = reqparse.RequestParser(bundle_errors=True)
    serializador.add_argument(
        'correo',
        type=str,
        required=True,
        location='json',
        help='Falta el correo'
    )
    serializador.add_argument(
        'password',
        type=str,
        required=True,
        location='json',
        help='Falta la password'
    )

    def post(self):
        # si el usuario existe en la bd indicarlo sino en un mensaje indicar que no existe y un estado 404
        data = self.serializador.parse_args()
        usuario = base_de_datos.session.query(UsuarioModel).filter(
            UsuarioModel.usuarioCorreo == data.get('correo')).first()
        if usuario is None:
            return {
                "message": "Usuario no encontrado"
            }, 404
        password = bytes(data.get('password'), 'utf-8')
        usuarioPwd = bytes(usuario.usuarioPassword, 'utf-8')
        resultado = checkpw(password, usuarioPwd)
        if resultado:
            return{
                "message": "Usuario encontrado"
            }
        else:
            return {
                "message": "Usuario no encontrado"
            }, 400


class UsuarioController(Resource):

    # con el decorador indicamos que este metodo de esta clase va a ser protegido
    @jwt_required()
    def get(self):
        print(current_identity)
        del current_identity['_sa_instance_state']
        del current_identity['usuarioPassword']
        return {
            "content": current_identity
        }

    @jwt_required()
    def patch(self):
        serializador = reqparse.RequestParser()
        serializador.add_argument(
            'nombre',
            type=str,
            location='json',
            required=False,
        )

        serializador.add_argument(
            'apellido',
            type=str,
            location='json',
            required=False,
        )

        serializador.add_argument(
            'correo',
            type=str,
            location='json',
            required=False,
        )

        serializador.add_argument(
            'password',
            type=str,
            location='json',
            required=False,
        )

        serializador.add_argument(
            'telefono',
            type=str,
            location='json',
            required=False,
        )

        data = serializador.parse_args()
        
        print(data.get('nombre') if data.get(
            'nombre') is not None else 'shrek')
        usuarioId = current_identity.get('usuarioId')
        usuarioEncontrado = base_de_datos.session.query(
            UsuarioModel).filter(UsuarioModel.usuarioId == usuarioId).first()
        # operador ternario
        # TODO hacer que si el usuario envia la password entonces modificarla pero previamente usar bcrypt para encriptar la contrase??a
        nuevaPwd = None
        if data.get("password") is not None:
            if search(PATRON_PASSWORD, data.get("password")) is None:
                return{
                    "message":"La contrase??a debe tener 1 mayuscula 1 minuscula 1 numero 1 caracter"
                }, 400
            pwdb = bytes(data.get("password"), "utf-8")
            salt = gensalt(rounds=10)
            nuevaPwd = hashpw(pwdb, salt).decode("utf-8")
        try:
            usuarioActualizado = base_de_datos.session.query(
                UsuarioModel).filter(UsuarioModel.usuarioId==usuarioEncontrado.usuarioId).update({
                    "usuarioNombre": data.get('nombre') if data.get(
                        'nombre') is not None else usuarioEncontrado.usuarioNombre,

                    "usuarioApellido": data.get('apellido') if data.get(
                        'apellido') is not None else usuarioEncontrado.usuarioApellido,

                    UsuarioModel.usuarioCorreo: data.get('correo') if data.get(
                        'correo') is not None else usuarioEncontrado.usuarioCorreo,

                    UsuarioModel.usuarioTelefono: data.get('telefono') if data.get(
                        'telefono') is not None else usuarioEncontrado.usuarioTelefono,

                    UsuarioModel.usuarioPassword: nuevaPwd if data.get(
                        'password') is not None else usuarioEncontrado.usuarioPassword,
                })
            print(usuarioActualizado)
            base_de_datos.session.commit()

            return {
                "message": "Usuario actualizado exitosamente"
            }
        except IntegrityError as error:
            return{
                "message":"Y aexiste un usuario con ese correo, no se puede duplicar el correo"
            }, 400

class ResetearPasswordController(Resource):
    serializador = reqparse.RequestParser()
    serializador.add_argument(
        "correo",
        type=str,
        required=True,
        location="json",
        help="falta el correo"
    )

    def post(self):
        data = self.serializador.parse_args()
        correo = data.get("correo")
        if search(PATRON_CORREO, correo) is None:
            return {
                "message":"Formato de correo incorrecto"
            }, 400
        usuario = base_de_datos.session.query(UsuarioModel).filter(
            UsuarioModel.usuarioCorreo==correo
        ).first()
        if not usuario:
            return{
                "message":"Usuario no encontrado" #Se debe poner mensaje como si hubise sido exitoso para evitar ataque DOS
            }, 404
        print(environ.get("FERNET_SECRET"))
        fernet = Fernet(environ.get("FERNET_SECRET"))
        mensaje= {
            "fecha_caducidad": str(datetime.utcnow() + timedelta(minutes=30)),
            "correo":correo
        }
        mensaje_json = dumps(mensaje)

        
        mensaje_enctriptado = fernet.encrypt(bytes(mensaje_json, "utf-8")).decode("utf-8")
        print(mensaje_enctriptado)
        #mensaje_desencriptado = fernet.decrypt(bytes(mensaje_enctriptado, "utf-8"))
        #print(mensaje_desencriptado)
        #link="http://localhost:5000/change-password?token={}".format(mensaje_enctriptado)
        link=request.host_url+ "change-password?token={}".format(mensaje_enctriptado)
        enviarCorreo(correo, '''Hola {} has solicitado el reinicio de tu contrase??a,
        has clic en el siguiente enlace para efectuarla:
        <br>
        <button><a href="{}">Cambiar</a></button>'''.format(usuario.usuarioNombre, link))
        return{
            "message":"Se envio un correo con el cambio de password"
        }
