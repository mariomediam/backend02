from email.mime.text import MIMEText
import smtplib
from email.mime.multipart import MIMEMultipart
from os import environ
from dotenv import load_dotenv
load_dotenv()

mensaje = MIMEMultipart()

mensaje["From"] = environ.get("EMAIL")
mensaje["Subject"]="Solicitud de restauración de contraseña"
password = environ.get("EMAIL_PASSWORD")

def enviarCorreo(destinatario, cuerpo):
    '''Función que sirve para enviar un correo'''
    print("destinatario " +  destinatario)
    mensaje["To"]=destinatario
    texto=mensaje
    mensaje.attach(MIMEText(cuerpo, "html"))
    try:
        servidorSMTP = smtplib.SMTP("smtp.gmail.com", 587)
        servidorSMTP.starttls()
        servidorSMTP.login(user=mensaje.get("From"), password=password)
        servidorSMTP.sendmail(
            from_addr=mensaje.get("From"),
            to_addrs=mensaje.get("To"),
            msg=mensaje.as_string()
        )
        servidorSMTP.quit()
    except Exception as e:
        print(e)
