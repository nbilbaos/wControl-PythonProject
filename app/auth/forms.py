from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange

class RegistrationForm(FlaskForm):
    name = StringField('Nombre', validators=[
        DataRequired(message="El nombre es obligatorio"),
        Length(min=2, max=50)
    ])

    email = StringField('Correo Electrónico', validators=[
        DataRequired(message="El correo es obligatorio"),
        Email(message="Ingresa un correo válido")
    ])

    password = PasswordField('Contraseña', validators=[
        DataRequired(message="La contraseña es obligatoria"),
        Length(min=6, message="Mínimo 6 caracteres")
    ])

    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(),
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])

    # NUEVO: Campos obligatorios para perfil inicial
    gender = SelectField('Género', choices=[
        ('', 'Selecciona...'),
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro')
    ], validators=[DataRequired(message="Selecciona un género")])

    height = IntegerField('Altura (cm)', validators=[
        DataRequired(message="La altura es obligatoria"),
        NumberRange(min=50, max=300, message="Altura inválida (50-300 cm)")
    ])

    weight = FloatField('Peso Inicial (kg)', validators=[
        DataRequired(message="El peso inicial es obligatorio"),
        NumberRange(min=20, max=500, message="Peso inválido")
    ])

    submit = SubmitField('Registrarse')


class ProfileForm(FlaskForm):
    # Datos Generales
    name = StringField('Nombre Completo', validators=[DataRequired()])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])

    # Datos Físicos
    gender = SelectField('Género', choices=[('', 'Seleccionar...'), ('male', 'Hombre'), ('female', 'Mujer')])
    height = FloatField('Altura (cm)', validators=[DataRequired()])
    weight_goal = FloatField('Meta de Peso (kg)', validators=[DataRequired()])

    # Seguridad (Opcionales)
    new_password = PasswordField('Nueva Contraseña (dejar en blanco para no cambiar)',
                                 validators=[Optional(), Length(min=8)])
    confirm_password = PasswordField('Confirmar Nueva Contraseña',
                                     validators=[EqualTo('new_password', message='Las contraseñas no coinciden')])

    # Validación Requerida para cambios sensibles
    current_password = PasswordField('Contraseña Actual (requerida para guardar cambios)',
                                     validators=[
                                         DataRequired(message="Debes ingresar tu contraseña actual para confirmar")])

    submit = SubmitField('Guardar Cambios')


class LoginForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar')