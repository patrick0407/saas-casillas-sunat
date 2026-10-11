import os
from django.core.mail import EmailMessage, get_connection
from django.conf import settings

def enviar_alerta_correo(notificacion):
    estudio = notificacion.cliente_ruc.estudio
    destinatario = estudio.usuario.email

    if not destinatario:
        print(f"⚠️ El usuario {estudio.usuario.username} no tiene email configurado.")
        return

    # Selección de credenciales SMTP
    if hasattr(estudio, 'use_custom_email') and estudio.use_custom_email and estudio.email_smtp and estudio.password_smtp:
        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host='smtp.gmail.com',
            port=465,
            username=estudio.email_smtp,
            password=estudio.password_smtp,
            use_ssl=True,
            timeout=10
        )
        from_email = f"{estudio.nombre_estudio} <{estudio.email_smtp}>"
    else:
        connection = get_connection()
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)

    asunto_mail = f"🚨 Nueva Notificación {notificacion.origen} - RUC {notificacion.cliente_ruc.ruc}"
    
    cuerpo = f"""
    Hola,

    Se ha detectado una nueva notificación en la Casilla Electrónica.

    Detalles del documento:
    --------------------------------------------------
    • Contribuyente: {notificacion.cliente_ruc.razon_social} (RUC: {notificacion.cliente_ruc.ruc})
    • Origen: {notificacion.origen}
    • Código Doc: {notificacion.codigo_documento}
    • Asunto: {notificacion.asunto}
    • Fecha Emisión: {notificacion.fecha_emision.strftime('%d/%m/%Y %H:%M')}
    --------------------------------------------------

    Atentamente,
    {estudio.nombre_estudio}
    """

    email = EmailMessage(
        subject=asunto_mail,
        body=cuerpo,
        from_email=from_email,
        to=[destinatario],
        connection=connection
    )

    if notificacion.archivo_pdf and os.path.exists(notificacion.archivo_pdf.path):
        email.attach_file(notificacion.archivo_pdf.path)

    try:
        email.send(fail_silently=False)
        print(f"✅ Alerta enviada con éxito a {destinatario}")
    except Exception as e:
        print(f"❌ Error al enviar correo de alerta: {str(e)}")