import os
# import env
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo, DESCENDING
from bson.objectid import ObjectId
import bcrypt

app = Flask(__name__)

app.config['MONGO_DBNAME'] = os.getenv('MONGO_DBNAME')
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.secret_key = os.getenv('SECRET_KEY')

mongo = PyMongo(app)



@app.route('/')
def index():
    # if the cookie for the user already exist the login page is skipped
    if "username" in session:
        return redirect(url_for('get_tasks'))
    
    return render_template('login.html')

@app.route('/login', methods=["GET", "POST"])
def login():
   if request.method == 'POST':
      users = mongo.db.users
      user_login = users.find_one({'username':request.form['username']})

      if user_login:
         if bcrypt.hashpw(request.form['password'].encode('utf-8'), user_login['password']) == user_login['password']:
                session["username"] = request.form["username"].capitalize()
                return redirect(url_for('get_tasks'))
      
      flash('The login details are not correct')
      return render_template('login.html', logged_in = 0)
   
   return render_template('login.html', logged_in = 0)
   

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        user_exists = users.find_one({'username':request.form['username']})

        if user_exists is None:
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'username':request.form['username'], 'password':hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('get_tasks'))

        flash('That username already exists, please choose a different one.')
        return render_template('register.html', logged_in = 0)

    return render_template('register.html', logged_in = 0)

@app.route('/log_out')
def log_out():
   session.pop('username')
   return render_template('login.html')


@app.route('/get_tasks')
def get_tasks():
   return render_template('tasks.html', tasks = mongo.db.tasks.find({"username":session['username']}).sort([('is_urgent',DESCENDING)]), user=session['username'])


@app.route('/add_task')
def add_task():
   return render_template("add_task.html", categories=mongo.db.categories.find({  "$or":[ {'username':session['username']},{'username':""}]   }), username=session['username'])


@app.route('/insert_task', methods = ["POST"])
def insert_task(): 
   mongo.db.tasks.insert_one(request.form.to_dict())   
   return redirect(url_for("get_tasks"))


@app.route('/edit_task/<task_id>')
def edit_task(task_id):
   task = mongo.db.tasks.find_one({"_id":ObjectId(task_id)})
   return render_template('edit_task.html', task = task, categories=mongo.db.categories.find() )


@app.route('/update_task/<task_id>', methods=["POST"])
def update_task(task_id):
    tasks = mongo.db.tasks
    tasks.update( {'_id': ObjectId(task_id)},
    {
        'task_name':request.form.get('task_name'),
        'category_name':request.form.get('category_name'),
        'task_description': request.form.get('task_description'),
        'due_date': request.form.get('due_date'),
        'is_urgent':request.form.get('is_urgent')
    })
    return redirect(url_for('get_tasks'))


@app.route('/delete_task/<task_id>')
def delete_task(task_id): 
   mongo.db.tasks.remove({"_id":ObjectId(task_id)})   
   return redirect(url_for("get_tasks"))


@app.route('/get_categories')
def categories():
   return render_template('categories.html', categories = mongo.db.categories.find({'username':session['username']}))


@app.route('/add_category')
def add_category():
   return render_template("add_category.html",username=session['username'])


@app.route('/insert_category', methods = ["POST"])
def insert_category(): 
   mongo.db.categories.insert_one(request.form.to_dict())   
   return redirect(url_for("categories"))


@app.route('/edit_category/<category_id>')
def edit_category(category_id):
   category = mongo.db.categories.find_one({"_id":ObjectId(category_id)})
   return render_template('edit_category.html', category = category)


@app.route('/update_category/<category_id>', methods=["POST"])
def update_category(category_id):
    category = mongo.db.categories.update( {'_id': ObjectId(category_id)},
    {
        'category_name':request.form.get('category_name'),
    })
    return redirect(url_for('categories'))


@app.route('/delete_category/<category_id>')
def delete_category(category_id): 
   mongo.db.categories.remove({"_id":ObjectId(category_id)})   
   return redirect(url_for("categories"))


if __name__ == "__main__":
    app.run(host=os.getenv('IP'), port=os.getenv('PORT'), debug=False)

