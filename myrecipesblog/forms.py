from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField,TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, InputRequired
from myrecipesblog.models import User, Recipe

#Sign Up Form
class SignupForm(FlaskForm):
    username = StringField('Username',
                            validators = [DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                            validators = [DataRequired(), Email()])
    password = PasswordField('Password',
                            validators = [DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                            validators = [DataRequired(), EqualTo('password')])
    """ account_type = StringField('Account Type: Please type "Explorer" or "Contributor"',
                            validators = [DataRequired()]) """
    account_type = SelectField('Account Type', choices=[('Contributor', 'Contributor'), ('Explorer', 'Explorer')])                        
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        #It will check if same username is already present in the database. The first match is sufficient to raise error.
        #If the username does not exist, None is returned.
        user = User.query.filter_by(username=username.data).first()
        #If user is anything other than None, error is raised.
        if user:
            raise ValidationError('This username is already taken. Please use another username.')

    def validate_email(self, email):        
        
        user = User.query.filter_by(email=email.data).first()
        
        if user:
            raise ValidationError('An account for this email already exists. Please use another email.')

#Login Form
class LoginForm(FlaskForm):
    
    email = StringField('Email',
                            validators = [DataRequired(), Email()])
    password = PasswordField('Password',
                            validators = [DataRequired()])
    """account_type = StringField('Account Type',
                            validators = [DataRequired()])"""
    account_type = SelectField('Account Type', choices=[('Contributor', 'Contributor'), ('Explorer', 'Explorer')])                        
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

#Update Account Credentials Form
class UpdateaccountForm(FlaskForm):
    username = StringField('Username',
                            validators = [DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                            validators = [DataRequired(), Email()])

    picture = FileField('Update Profile Picture',
                            validators = [FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            #It will check if same username is already present in the database. The first match is sufficient to raise error.
            #If the username does not exist, None is returned.
            user = User.query.filter_by(username=username.data).first()
            #If user is anything other than None, error is raised.
            if user:
                raise ValidationError('This username is already taken. Please use another username.')

    def validate_email(self, email):
        if email.data != current_user.email:        
            user = User.query.filter_by(email=email.data).first()            
            if user:
                raise ValidationError('An account for this email already exists. Please use another email.')

class CreateRecipeForm(FlaskForm):
    recipe_name = StringField('Name of your recipe', validators=[DataRequired()])
    recipe_ingredient = StringField('Ingredients', validators=[DataRequired()])
    recipe_cook_time = IntegerField('Cook time: Please enter in mintues', validators=[DataRequired()])
    recipe_method = StringField('Method: (Please mention the type of cooking such as stir fry, bake etc)', validators=[DataRequired()])
    recipe_meal_type = StringField('Meal type : (Please mention if type is breakfast, lunch, appetizer etc)', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    #rpicture = FileField('Upload recipe picture',
                            #validators = [FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Post')

    def validate_recipe_name(self, recipe_name):
        recipe = Recipe.query.filter_by(recipe_name=recipe_name.data).first()
        if recipe:
            raise ValidationError('Recipe names must be unique. Please make necessary changes')

class UpdateRecipeForm(FlaskForm):
    recipe_ingredient = StringField('Ingredients', validators=[DataRequired()])
    recipe_cook_time = IntegerField('Cook time: Please enter in mintues', validators=[DataRequired()])
    recipe_method = StringField('Method: (Please mention the type of cooking such as stir fry, bake etc)', validators=[DataRequired()])
    recipe_meal_type = StringField('Meal type : (Please mention if type is breakfast, lunch, appetizer etc)', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    rpicture = FileField('Upload recipe picture',
                            validators = [FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Post')
    
class AddCommentForm(FlaskForm):
    body = TextAreaField('Body', validators=[InputRequired()])
    submit = SubmitField("Post")
