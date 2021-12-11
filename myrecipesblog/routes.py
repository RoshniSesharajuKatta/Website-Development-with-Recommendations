import os
import re
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, Blueprint
from myrecipesblog import app, db, bcrypt
from myrecipesblog.forms import SignupForm, LoginForm, UpdateaccountForm ,CreateRecipeForm,  AddCommentForm,UpdateRecipeForm
from myrecipesblog.models import User, Recipe, RecipePostLike, RecipePostTried, RecipePostComment, Note, Subscription
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import or_, and_
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy import tuple_
import pandas as pd
from sqlalchemy import create_engine
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from itertools import permutations

posts=Blueprint('posts', __name__,template_folder='templates')

#Homepage Route
#All recipes are queried and appended to a list which is sent to the recipe.html page.
@app.route("/")
@app.route("/home")
def home():    
    recipes=[]
    
    allrecipes = Recipe.query.all()
    recipes.append(allrecipes)    

    return render_template("home.html",recipes=recipes)

#Newsfeed Route
#The newsfeed will have the recipes from authors that the current user has subscribed to.
#The authors subscribed are queried and the recipe deatils like date and time posted are collected. 
#The current user total likes for the contributor is counted.
#The recipes in news feed are sorted by date posted, number of likes for the contributor recipes and time posted. 
@app.route("/newsfeed")
@login_required
def newsfeed():
    subscribed_to = Subscription.query.filter_by(subscriber_id=current_user.id)
    allrecipes = []
    recipedetails = []
    for sub in subscribed_to:

        following = sub.subscribed_id
        following_string = str(following)
        recipes=Recipe.query.filter(Recipe.user_id.like(following_string))
        likes = 0
        for r in recipes:
            is_liked = RecipePostLike.query.filter_by(recipe_id=r.id, user_id=current_user.id)
            for i in is_liked:
                likes += 1

                allrecipes.append(r)

        for r in recipes:
            details = []    
            details.append(r)
            details.append(str(r.date_posted).split()[0])
            details.append(likes)
            details.append(str(r.date_posted).split()[1])
            
            recipedetails.append(details)

    recipedetailsframe = pd.DataFrame(recipedetails, columns = ["recipe", "date", "like", "time"])
    to_order = ["date", "like", "time"]
    recipedetailsframe = recipedetailsframe.sort_values(to_order, ascending = [False, False, False])
    allrecipes=list(recipedetailsframe["recipe"])

    return render_template("newsfeed.html",recipes=allrecipes)

#Subscrite Route
#The recipe author is queried to whom the current user can subscribe/unsubscribe to.
#The two action are 'Subscribe' and 'Unsubscribe'.
@app.route('/subscribe/<int:user_id>/<action>')
@login_required
def subscribe(user_id, action):
    rauthor = User.query.filter_by(id=user_id).first_or_404()
    profile = User.query.filter_by(username=rauthor.username).first_or_404()
    recipes = Recipe.query.all()
    if action == 'subscribe':
        current_user.subscribe(rauthor.id)
        db.session.commit()
    if action == 'unsubscribe':
        current_user.unsubscribe(rauthor.id)
        db.session.commit()
    return render_template('author_profile.html', rauthor=rauthor, profile=profile, recipes=recipes)


#Like Route
#The recipe is queried to what the current user can like/unlike to.
#The two action are 'Like' and 'Unlike'.
@app.route('/like/<int:recipe_id>/<action>')
@login_required
def like_function(recipe_id, action):
    recipe = Recipe.query.filter_by(id=recipe_id).first_or_404()
    if action == 'like':
        current_user.like_recipe(recipe)
        db.session.commit()
    if action == 'unlike':
        current_user.unlike_recipe(recipe)
        db.session.commit()
    image_file = url_for('static', filename='account_pics/' + recipe.image_file)
    return render_template('recipe.html', recipe=recipe, image_file=image_file)

@app.route('/tried/<int:recipe_id>/<action>')
@login_required
def tried_action(recipe_id, action):
    recipe = Recipe.query.filter_by(id=recipe_id).first_or_404()
    if action == 'tried':
        current_user.tried_recipe(recipe)
        db.session.commit()
    image_file = url_for('static', filename='account_pics/' + recipe.image_file)
    return render_template('recipe.html', recipe=recipe, image_file=image_file)


@app.route("/search",methods=['GET','POST'])
def search():
    if request.method=='POST':
        form=request.form
        
        search_string=form['search_string']
        search_string=search_string.replace(',','%')
        search_string2=form['search_string2']
        s_lst=search_string2.split(',')
        s=search_string2.replace(',','%')
        search_ingredient=[]
        perm = permutations(s_lst)
        for i in list(perm):
            t=[]
            for j in i:
                concat='%'+j
                t.append(concat)
            string=" "
            string =string.join(t)
            string=string.replace(' ','')
            string=string+'%'
            search_ingredient.append(string)
        search_string4=form['search_string4']
        search_string5=form['search_string5']
        search_string_ck=form['search_string3']
        results=[]
        if search_string_ck=='':
            for s in search_ingredient:
                result=Recipe.query.filter(and_(Recipe.recipe_name.like('%'+search_string+'%'),
                                            Recipe.recipe_ingredient.like(s),
                                            Recipe.recipe_cook_time.like('%'),
                                            Recipe.recipe_method.like('%'+search_string4+'%'),
                                            Recipe.recipe_meal_type.like('%'+search_string5+'%')))
                
                results.append(result)
        
        else:
            search_string3=int(''.join(i for i in search_string_ck if i.isdigit()))
            for s in search_ingredient:
                result=Recipe.query.filter(and_(Recipe.recipe_name.like('%'+search_string+'%'),
                                            Recipe.recipe_ingredient.like('%'+s+'%'),
                                            Recipe.recipe_cook_time.like(search_string3),
                                            Recipe.recipe_method.like('%'+search_string4+'%'),
                                            Recipe.recipe_meal_type.like('%'+search_string5+'%')))
                results.append(result)
        return render_template("home.html",recipes=results)
    else:
        print('Sorry no recipes found')
        return redirect('/')


@app.route("/contact")
def contact():
    return render_template("contact.html", title="Contact")

#Sign Up Route
#This route collects the data entered and commits to the database.
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user1 = User(username=form.username.data, email=form.email.data, password=hashed_password, account_type=form.account_type.data)
        db.session.add(user1)
        db.session.commit()
        flash(f'Hi {form.username.data}! Your account is created! You can now login.', 'success')
        return redirect(url_for('login'))
    return render_template("signup.html", form=form)

#Login Route
#This route collects the data entered and checks it against the stored data.
#If it matches, the user is logged in and home page is rendered.
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, account_type=form.account_type.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash(f'Login Unsuccessful. Please check the Email, Password and account type entered.', 'danger')
    return render_template("login.html", form=form)

#Logout Route
#This route logs out the user from the session. 
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

#Pictures are resized and saved in a similar format.
def save_pictures(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/account_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    i.save(picture_path)

    return picture_fn



@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateaccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_pictures(form.picture.data)
            current_user.image_file = picture_file

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        # flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='account_pics/' + current_user.image_file)
    return render_template("account.html", image_file=image_file, form=form)


@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    image_file = url_for('static', filename='account_pics/' + current_user.image_file)
    recipes = Recipe.query.all()
    return render_template("profile.html", image_file=image_file,recipes=recipes)

#Author Profile Route
#The current user can view the particular recipe's author.
#The particular recipe's author is queried
@app.route("/author_profile/<string:username>", methods=['GET', 'POST'])
@login_required
def author_profile(username):
    recipes = Recipe.query.all()
    profile = User.query.filter_by(username=username).first_or_404()
    image_file = url_for('static', filename='account_pics/' + profile.image_file)
    return render_template("author_profile.html", recipes=recipes, profile=profile, image_file=image_file)


#Create Recipe Route
#The contributor can create the recipe.
#The particular recipe is queried and displayed in the background.
@app.route("/recipe/create", methods=['GET', 'POST'])
@login_required
def create_recipe():
    form = CreateRecipeForm()
    if form.validate_on_submit():
        recipe = Recipe(recipe_name=form.recipe_name.data, recipe_ingredient= form.recipe_ingredient.data,recipe_cook_time=form.recipe_cook_time.data,recipe_method=form.recipe_method.data,recipe_meal_type=form.recipe_meal_type.data,content=form.content.data, author=current_user)
        db.session.add(recipe)
        db.session.commit()
        #flash('Your recipe has been created!', 'success')
        return redirect(url_for('profile'))
    return render_template('create_recipe.html', recipe_name='New Recipe',
                           form=form, legend='New Recipe')

@app.route("/recipe/<int:recipe_id>", methods=['GET', 'POST'])
def recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    notes = Note.query.all()
    image_file = url_for('static', filename='account_pics/' + recipe.image_file)
    
    df=pd.read_sql(db.session.query(Recipe).statement,db.session.bind)
    features = ['recipe_ingredient']
    for feature in features:
        df[feature] = df[feature].fillna('')
    
    def get_title_from_index(index):
	    return df[df.index == index]["recipe_name"].values[0]

    def get_id_from_index(index):
	    return df[df.index == index]["id"].values[0]

    def get_index_id(id):
	    return df[df.id == id].index.values[0]

    cv = CountVectorizer()
    count_matrix = cv.fit_transform(df["recipe_ingredient"])
    cosine_sim = cosine_similarity(count_matrix) 
    recipe_index = get_index_id(recipe_id)
    similar_recipes =  list(enumerate(cosine_sim[recipe_index]))
    sorted_similar_recipes = sorted(similar_recipes,key=lambda x:x[1],reverse=True)
    id_list=[]
    order=[]
    recipe_not_included=[]
    for element in sorted_similar_recipes:
        id_list.append(element[0])
        order.append(get_id_from_index(element[0]))
        if element[1]==0:
            recipe_not_included.append(get_title_from_index(element[0]))

    id_list.append(len(id_list))
    recipe_recommendations=db.session.query(Recipe).filter(Recipe.id.in_(id_list)).all()
    recipe_recommendation = sorted(recipe_recommendations, key=lambda o: order.index(o.id))
    return render_template('recipe.html', recipe_name=recipe.recipe_name, recipe=recipe ,notes=notes,recipe_recommendation=recipe_recommendation,recipe_not_included=recipe_not_included, image_file=image_file)



#Update Recipe Route
#The contributor can update the recipe and add the picture during updation.
#The particular updated recipe is queried and displayed in the background.
@app.route("/recipe/<int:recipe_id>/update", methods=['GET', 'POST'])
@login_required
def update_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        abort(403)
    form = UpdateRecipeForm()
    if form.validate_on_submit():
        if form.rpicture.data:
            rpicture_file = save_pictures(form.rpicture.data)
            recipe.image_file = rpicture_file
        
        recipe.recipe_ingredient = form.recipe_ingredient.data
        recipe.recipe_cook_time = form.recipe_cook_time.data
        recipe.recipe_method = form.recipe_method.data
        recipe.recipe_meal_type = form.recipe_meal_type.data
        recipe.content = form.content.data
        db.session.commit()
        #flash('Your recipe has been updated!', 'success')
        return redirect(url_for('profile'))

    elif request.method == 'GET':
        form.recipe_ingredient.data = recipe.recipe_ingredient
        form.recipe_cook_time.data = recipe.recipe_cook_time  
        form.recipe_method.data =  recipe.recipe_method
        form.recipe_meal_type.data = recipe.recipe_meal_type
        form.content.data = recipe.content
    return render_template('update_recipe.html', name='Update recipe',
                           form=form, legend='Update recipe')


@app.route("/recipe/<int:recipe_id>/delete", methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    r_name= recipe.recipe_name

    note_filter=Note.query.filter(Recipe.recipe_name.like(r_name))
    for i in note_filter:
        if i.recipe_name == r_name:
            db.session.delete(i)
            db.session.commit()

    if recipe.author != current_user:
        abort(403)

    db.session.delete(recipe)
    db.session.commit()
    #flash('Your recipe has been deleted!','success')
    return redirect(url_for('profile'))

@app.route("/recipe/<int:recipe_id>/comment", methods=["GET", "POST"])
@login_required
def comment_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    form = AddCommentForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            comment = RecipePostComment(body=form.body.data, recipe_id=recipe.id, user_id=current_user.id)
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for("recipe", recipe_id=recipe.id, user_id=current_user.id))
    return render_template("comment_recipe.html", title="Comment recipe",form=form, recipe_id=recipe_id, user_id=current_user.id)


@app.route("/recipe/<string:recipe_name>/note", methods=["GET", "POST"])
@login_required
def note(recipe_name):
    recipe = Recipe.query.all()
    notes=Note.query.filter(Recipe.recipe_name.like(recipe_name))
    recipe_this=Recipe.query.filter(Recipe.recipe_name.like(recipe_name))
    print(recipe_this)

    note = request.form.get('note')
    if request.method == 'POST':
            new_note = Note(body=note, user_id=current_user.id,recipe_name = recipe_name)
            db.session.add(new_note)
            db.session.commit()
            print('Done')
            #flash("Your notes has been added", "success")
            return render_template("note.html", title="Your Notes", notes=notes, recipe=recipe,recipe_name = recipe_name, recipe_this=recipe_this)
    return render_template("note.html", title="Your Notes", notes=notes, recipe=recipe,recipe_name = recipe_name,recipe_this=recipe_this)