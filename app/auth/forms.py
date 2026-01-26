from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange


class RegistrationForm(FlaskForm):
    name = StringField('Nombre Completo',
                       validators=[DataRequired(message="El nombre es obligatorio")])

    email = StringField('Correo Electrónico',
                        validators=[DataRequired(), Email(message="Ingresa un email válido")])

    # Seguridad: Mínimo 8 caracteres
    password = PasswordField('Contraseña', validators=[
        DataRequired(),
        Length(min=8, message="La contraseña debe tener al menos 8 caracteres")
    ])

    # Seguridad: Confirmar contraseña para evitar errores de dedo
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(),
        EqualTo('password', message='Las contraseñas no coinciden')
    ])

    gender = SelectField('Género', choices=[
        ('', 'Prefiero no decir / Completar después'),
        ('male', 'Hombre'),
        ('female', 'Mujer')
    ], validators=[Optional()])

    height = FloatField('Altura (cm)', validators=[Optional(), NumberRange(min=50, max=250)])
    weight = FloatField('Peso Inicial (kg)', validators=[Optional(), NumberRange(min=20, max=300)])

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