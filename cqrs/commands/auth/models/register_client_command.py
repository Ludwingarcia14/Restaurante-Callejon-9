# controllers/api/cqrs/commands/auth/models/register_client_command.py

class RegisterClientCommand:
    """DTO para encapsular los datos necesarios para registrar un nuevo cliente."""
    
    def __init__(self, nombre, apellidos, email, telefono, fecha_nac, 
                 password, password_confirm, recaptcha_response, remote_addr,
                 cliente_idFinanciera=None, asesor_id=None): # <-- ¡CAMPOS AÑADIDOS!
        
        self.nombre = nombre
        self.apellidos = apellidos
        self.email = email
        self.telefono = telefono
        self.fecha_nac = fecha_nac
        self.password = password
        self.password_confirm = password_confirm
        self.recaptcha_response = recaptcha_response
        self.remote_addr = remote_addr
        
        # Nuevos campos opcionales
        self.cliente_idFinanciera = cliente_idFinanciera
        self.asesor_id = asesor_id