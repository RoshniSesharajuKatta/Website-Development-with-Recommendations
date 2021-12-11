from datetime import datetime
from myrecipesblog import db, login_manager
from flask_login import UserMixin
from sqlalchemy.sql import func

#This is an extension and decorator function used to get user with user id.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#This is the User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    #length is 60 here as every password will be converted to 60 characters using hashing algorithm.
    password = db.Column(db.String(60), nullable=False)
    account_type = db.Column(db.String(30), nullable=False)
    
    recipes = db.relationship('Recipe', backref='author', lazy=True)
    user_notes = db.relationship('Note', backref='author', lazy=True)
    comments = db.relationship('RecipePostComment', backref='author', lazy=True)

    #Subscriber definitions
    subscribers = db.relationship(
        'Subscription',
        foreign_keys='Subscription.subscriber_id',
        backref='user', lazy='dynamic')

    # subscribed_to = db.relationship(
    #     'Subscription',
    #     foreign_keys='Subscription.subscribed_id',
    #     backref='user', lazy='dynamic')

    def subscribe(self, rauthor):
        if not self.already_subscribed(rauthor):
            subscribee = Subscription(subscriber_id=self.id, subscribed_id=rauthor)
            db.session.add(subscribee)

    def unsubscribe(self, rauthor):
        if self.already_subscribed(rauthor):
            Subscription.query.filter_by(
                subscriber_id=self.id,
                subscribed_id=rauthor).delete()

    def already_subscribed(self, rauthor):
        return Subscription.query.filter(
            Subscription.subscriber_id == self.id,
            Subscription.subscribed_id == rauthor).count() > 0

    #Like definitions
    liked = db.relationship(
        'RecipePostLike',
        foreign_keys='RecipePostLike.user_id',
        backref='user', lazy='dynamic')

    def like_recipe(self, recipe):
        if not self.already_liked_recipe(recipe):
            like = RecipePostLike(user_id=self.id, recipe_id=recipe.id)
            db.session.add(like)

    def unlike_recipe(self, recipe):
        if self.already_liked_recipe(recipe):
            RecipePostLike.query.filter_by(
                user_id=self.id,
                recipe_id=recipe.id).delete()

    def already_liked_recipe(self, recipe):
        return RecipePostLike.query.filter(
            RecipePostLike.user_id == self.id,
            RecipePostLike.recipe_id == recipe.id).count() > 0

    #Tried definitions
    tried = db.relationship(
        'RecipePostTried',
        foreign_keys='RecipePostTried.user_id',
        backref='user', lazy='dynamic')

    def tried_recipe(self, recipe):
        if not self.already_tried_recipe(recipe):
            tried = RecipePostTried(user_id=self.id, recipe_id=recipe.id)
            db.session.add(tried)

    def already_tried_recipe(self, recipe):
        return RecipePostTried.query.filter(
            RecipePostTried.user_id == self.id,
            RecipePostTried.recipe_id == recipe.id).count() > 0
    
    def get_notes(self, recipe):
        return Note.query.filter(
            Note.user_id == self.id,
            Note.recipe_name == recipe.recipe_name)

def __repr__(self):
        #return '<User %r>' % self.username, self.email, self.image_file
        return f"User('{self.username}', '{self.email}', '{self.image_file}', '{self.account_type}'"

#This is the Recipe Model
class Recipe(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  recipe_name = db.Column(db.String(100), unique=True, nullable=False)
  recipe_ingredient = db.Column(db.String(100), nullable=False)
  recipe_cook_time = db.Column(db.Integer, nullable=False)
  recipe_method= db.Column(db.String(100), nullable=False)
  recipe_meal_type = db.Column(db.String(100), nullable=False)
  date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
  content = db.Column(db.Text, nullable=False)
  
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

  notes = db.relationship('Note', backref='recipe', lazy='dynamic')
  #notes_id = db.relationship('Note', backref='recipe', lazy='dynamic')
  likes = db.relationship('RecipePostLike', backref='recipe', lazy='dynamic')
  tries = db.relationship('RecipePostTried', backref='recipe', lazy='dynamic')
  comments = db.relationship('RecipePostComment', backref='article', lazy='dynamic') ## lazy = True  backref

#   def get_notes(self):
#       return Note.query.filter_by(recipe_id = recipe.id)

  def __repr__(self):
      return f"Recipe('{self.recipe_name}',{self.recipe_ingredient}',{self.recipe_cook_time}',{self.recipe_method}',{self.recipe_meal_type}', '{self.date_posted}'"

#This is the model for Like functionality for a recipe. User can like or unlike the post
class RecipePostLike(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))

#This is the model for Tried Functionality for a recipe. User can only digitally mark the recipe and not undo.
#novelty-2
class RecipePostTried(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))    


class RecipePostComment(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))
    body = db.Column(db.String(140))
    # timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # body_html = db.Column(db.Text)
    
    def __repr__(self):
        return f"RecipePostComment('{self.body}', '{self.recipe_id}', '{self.user_id}')"

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    #note_recipeid = db.relationship("id", foreign_keys='Note.recipe_id')
    recipe_name= db.Column(db.Integer, db.ForeignKey('recipe.recipe_name'), nullable=False)
    #note_recipename = db.relationship("recipe_name", foreign_keys='Note.recipe_name')
    body = db.Column(db.String(140))

    def __repr__(self):
        return f"Note('{self.body}', '{self.user_id}','{self.recipe_name}')"

#This is the model for Subscription
class Subscription(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    subscriber_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subscribed_id = db.Column(db.Integer)