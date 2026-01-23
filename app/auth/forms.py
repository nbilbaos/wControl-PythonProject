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