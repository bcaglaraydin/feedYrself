from flask import Flask, render_template, request, redirect, flash, session, url_for,g
from datetime import timedelta
import view
from flask_mysqldb import MySQL
import requests

app = Flask(__name__)
app.secret_key = "asdfghjk"
app.permanent_session_lifetime = timedelta(minutes=5)
app.add_url_rule("/", view_func=view.home_page)
app.add_url_rule("/login", view_func=view.login_page)
app.add_url_rule("/sign_up", view_func=view.sign_up_page)


app.config['MYSQL_HOST'] = "eu-cdbr-west-03.cleardb.net"
app.config['MYSQL_USER'] = "b7bc219a8e3513"
app.config['MYSQL_PASSWORD'] = "3729114a"
app.config['MYSQL_DB'] = "heroku_bae7948a328621b"
app.config['MYSQL_CURSORCLASS'] = "DictCursor"
db = MySQL(app)
api_key = 'H8yr4KlLftBQAa1NhtUY14pgLsydbMCFq3VCXN1R'

if __name__ == "__main__":
    app.run()


@app.route("/sign_up_suc", methods=['POST'])
def sign_up_suc_page():
    if request.method == 'POST':
        user = request.form.get('usrname')
        name = request.form.get('nm')
        pas = request.form.get('pass')
        gender = request.form.get('g')
        age = request.form.get('a')
        cursor = db.connection.cursor()
        query = "INSERT INTO user VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (None, name, age, gender, user, pas, 0, None))
        db.connection.commit()
        cursor.close()
        return render_template('sign_up.html', sign=1)


@app.route("/login_suc", methods=['GET', 'POST'])
def logic_suc_page():
    if request.method == 'POST':
        user = request.form.get('usrname')
        pas = request.form.get('pass')
        r = request.form.get('remember')
        cursor = db.connection.cursor()
        query = "SELECT * FROM user WHERE username = %s AND password = %s"
        cursor.execute(query, (user, pas))
        ex = cursor.fetchone()
        db.connection.commit()
        cursor.close()
        if not ex:
            return render_template('login.html', success=0)
        else:
            session["user"] = user
            if r:
                session.permanent = True
                return redirect(url_for("home_page"))
            else:
                session.permanent = False
                return redirect(url_for("home_page"))


@app.route("/log_out", methods=['GET', 'POST'])
def log_out_page():
    session.pop("user", None)
    return redirect(url_for("home_page"))


@app.route("/user", methods=['GET', 'POST'])
def user_page():
    user = session["user"]
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM user WHERE username = %s", [user])
    result = cursor.fetchone()
    u_id = result['user_id']

    if result["gender"] == "m":
        gender = "Male"
    elif result["gender"] == "f":
        gender = "Female"
    else:
        gender = "Other"
    cursor.execute("SELECT protein, fat, carbs, calorie  FROM nutrient WHERE id IN (SELECT diet_id FROM user WHERE user_id = %s)", [u_id])
    nutrients = cursor.fetchone()
    return render_template("user.html", result=result, gender=gender, nutrients=nutrients, prof=1)


@app.route("/add", methods=['GET', 'POST'])
def add_page():
    return render_template("add_recipe.html")


@app.route("/add_inst", methods=['GET', 'POST'])
def add_inst_page():
    if request.method == 'POST':
        user = session['user']
        cursor = db.connection.cursor()
        cursor.execute("SELECT user_id FROM user WHERE username = %s", [user])
        user_id = cursor.fetchone()
        id = user_id['user_id']
        name = request.form.get('rec_name')
        cat = request.form.get('cat')
        inst = request.form.get('inst')
        check = request.form.get('check')
        if check:
            c = True
        else:
            c = False
        query = "INSERT INTO recipe VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (None, None, id, name, cat, inst, 0, c))
        db.connection.commit()
        rec_id = cursor.lastrowid
        session['rec'] = rec_id
        query = "INSERT INTO user_recipe VALUES(%s, %s)"
        cursor.execute(query, (id, rec_id))
        db.connection.commit()
        cursor.close()
        return render_template("add_ingre.html")


@app.route("/add_", methods=['GET', 'POST'])
def add_ingre_page():
    if request.method == 'POST':
        cursor = db.connection.cursor()
        rec_id = session['rec']
        p_tot = 0
        f_tot = 0
        carb_tot = 0
        cal_tot = 0
        for val in range(1, 6):
            i = "i" + str(val)
            a = "a" + str(val)
            sel = "sel" + str(val)
            food = request.form.get(i)

            if food:
                unit = request.form.get(sel)
                amount = float(request.form.get(a))
                query = "INSERT INTO ingredient VALUES(%s, %s, %s, %s)"
                cursor.execute(query, (None, food, unit, float(amount)))
                db.connection.commit()

                ingr_id = cursor.lastrowid
                query = "INSERT INTO recipe_ingredient VALUES(%s, %s)"
                cursor.execute(query, (ingr_id, rec_id))
                db.connection.commit()

                response = requests.get('https://api.nal.usda.gov/fdc/v1/foods/search?api_key=' + api_key + '&query=' + food + '&pageSize=1')
                json = response.json()
                nut = json['foods']
                nuts = nut[0]['foodNutrients']

                for item in nuts:
                    if item['nutrientId'] == 1003:
                        if item['unitName'] == "G":
                            p = (item['value'] * amount) / 100
                        elif item.unitName == "MG":
                            p = (item['value'] * amount) * 10

                    elif item['nutrientId'] == 1004:
                        if item['unitName'] == "G":
                            f = (item['value'] * amount) / 100
                        elif item.unitName == "MG":
                            f = (item['value'] * amount) * 10

                    elif item['nutrientId'] == 1005:
                        if item['unitName'] == "G":
                            carb = (item['value'] * amount) / 100
                        elif item.unitName == "MG":
                            carb = (item['value'] * amount) * 10

                    elif item['nutrientId'] == 1008:
                        if item['unitName'] == "KCAL":
                            cal = (item['value'] * amount) / 100
                        elif item.unitName == "CAL":
                            cal = (item['value'] * amount) * 10

                p_tot += p
                f_tot += f
                carb_tot += carb
                cal_tot += cal

        query = "INSERT INTO nutrient VALUES(%s, %s, %s, %s, %s)"
        cursor.execute(query, (None, p_tot, f_tot, carb_tot, cal_tot))
        db.connection.commit()
        nut_id = cursor.lastrowid
        query = "UPDATE recipe SET nutrient_id = %s WHERE recipe_id = %s"
        cursor.execute(query, (nut_id, rec_id))
        db.connection.commit()
        cursor.close()
        session.pop("rec", None)
        return redirect(url_for("home_page"))


@app.route("/recipes/<int:public>/<string:cat>/<int:user_id>", methods=['GET', 'POST'])
def recipes_page(public=None, cat=None, user_id=None):
    cursor = db.connection.cursor()
    user = session['user']
    cursor = db.connection.cursor()
    cursor.execute("SELECT user_id FROM user WHERE username = %s", [user])
    uid = cursor.fetchone()
    id = uid['user_id']
    if user_id:
        if not public:
            if cat == "all":
                cursor.execute("SELECT u.user_id, r.recipe_id, r.name, u.username, r.score FROM recipe r INNER JOIN user u WHERE  r.user_id = %s and r.user_id = u.user_id", [user_id])
            elif cat == "diet":
                cursor.execute("SELECT * FROM nutrient WHERE id IN (SELECT diet_id FROM user WHERE user_id = %s)", [id])
                nuts = cursor.fetchone()

                if nuts['protein']:
                    p = nuts['protein']
                else:
                    p = 0

                if nuts['fat']:
                    f = nuts['fat']
                else:
                    f = 100000

                if nuts['carbs']:
                    c = nuts['carbs']
                else:
                    c = 100000

                if nuts['calorie']:
                    cal = nuts['calorie']
                else:
                    cal = 100000

                query = "SELECT u.user_id, r.recipe_id, r.name, u.username, r.score " \
                        "FROM recipe r INNER JOIN nutrient n ON r.nutrient_id = n.id AND r.user_id = %s AND n.protein > %s AND n.fat < %s AND n.carbs < %s AND n.calorie < %s " \
                        "INNER JOIN user u ON u.user_id = r.user_id"
                values = (user_id, p, f, c, cal)
                cursor.execute(query, values)
            else:
                query = "SELECT u.user_id, r.recipe_id, r.name, u.username, r.score FROM recipe r INNER JOIN user u WHERE r.user_id = %s and r.category = %s and r.user_id = u.user_id"
                values = (user_id, cat)
                cursor.execute(query, values)
        else:
            if cat == "all":
                query = "SELECT u.user_id, r.recipe_id, r.name, u.username, r.score FROM recipe r INNER JOIN user u WHERE r.is_public = %s and r.user_id = %s and r.user_id = u.user_id "
                values = (public, user_id)
                cursor.execute(query, values)
            elif cat == "diet":
                cursor.execute("SELECT * FROM nutrient WHERE id IN (SELECT diet_id FROM user WHERE user_id = %s)", [id])
                nuts = cursor.fetchone()

                if nuts['protein']:
                    p = nuts['protein']
                else:
                    p = 0

                if nuts['fat']:
                    f = nuts['fat']
                else:
                    f = 100000

                if nuts['carbs']:
                    c = nuts['carbs']
                else:
                    c = 100000

                if nuts['calorie']:
                    cal = nuts['calorie']
                else:
                    cal = 100000

                query = "SELECT u.user_id, r.recipe_id, r.name, u.username, r.score " \
                        "FROM recipe r INNER JOIN nutrient n ON r.nutrient_id = n.id AND r.user_id = %s AND r.is_public = %s AND n.protein > %s AND n.fat < %s AND n.carbs < %s AND n.calorie < %s " \
                        "INNER JOIN user u ON u.user_id = r.user_id"
                values = (user_id, public, p, f, c, cal)
                cursor.execute(query, values)

            else:
                query = "SELECT u.user_id, r.recipe_id, r.name, u.username, r.score FROM recipe r INNER JOIN user u WHERE r.is_public = %s and r.user_id = %s and r.category = %s and r.user_id = u.user_id"
                values = (public, user_id, cat)
                cursor.execute(query, values)
    else:
        if cat == "all":
            cursor.execute("SELECT u.user_id, r.recipe_id, r.name, u.username, r.score FROM recipe r INNER JOIN user u WHERE r.is_public = %s and r.user_id = u.user_id", [public])
        elif cat == "diet":
            cursor.execute("SELECT * FROM nutrient WHERE id IN (SELECT diet_id FROM user WHERE user_id = %s)", [id])
            nuts = cursor.fetchone()

            if nuts['protein']:
                p = nuts['protein']
            else:
                p = 0

            if nuts['fat']:
                f = nuts['fat']
            else:
                f = 100000

            if nuts['carbs']:
                c = nuts['carbs']
            else:
                c = 100000

            if nuts['calorie']:
                cal = nuts['calorie']
            else:
                cal = 100000

            query = "SELECT u.user_id, r.recipe_id, r.name, u.username, r.score " \
                    "FROM recipe r INNER JOIN nutrient n ON r.nutrient_id = n.id AND r.is_public = %s AND n.protein > %s AND n.fat < %s AND n.carbs < %s AND n.calorie < %s " \
                    "INNER JOIN user u ON u.user_id = r.user_id"
            values = (public, p, f, c, cal)
            cursor.execute(query, values)
        else:
            query = "SELECT u.user_id, r.recipe_id, r.name, u.username, r.score FROM recipe r INNER JOIN user u WHERE r.is_public = %s and r.user_id = u.user_id and r.category = %s"
            values = (public, cat)
            cursor.execute(query, values)
    result = cursor.fetchall()
    return render_template("recipes.html", result=result, cat=cat, public=public, fav=0, user_id=user_id)


@app.route("/user/<int:user_id>")
def profile_page(user_id):
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM user WHERE user_id = %s", [user_id])
    result = cursor.fetchone()
    cursor.close()

    if result["gender"] == "m":
        gender = "Male"
    elif result["gender"] == "f":
        gender = "Female"
    else:
        gender = "Other"

    return render_template("user.html", result=result, gender=gender, prof=0)


@app.route("/recipe/<int:recipe_id>/<int:fav>")
def recipe_page(recipe_id, fav):
    cursor = db.connection.cursor()
    if fav:
        cursor.execute("UPDATE recipe SET score=score+1 where recipe_id = %s", [recipe_id])
        db.connection.commit()
        cursor.execute("SELECT user_id FROM recipe WHERE recipe_id = %s", [recipe_id])
        u = cursor.fetchone()
        query = "UPDATE user SET score = (SELECT avg(score) FROM recipe WHERE recipe_id IN (SELECT recipe_id FROM user_recipe WHERE user_id = %s)) WHERE user_id = %s"
        values = (u['user_id'], u['user_id'])
        cursor.execute(query, values)
        db.connection.commit()
    cursor.execute("SELECT r.name, r.instructions, r.score, u.username, r.user_id FROM recipe r INNER JOIN user u WHERE r.recipe_id = %s and r.user_id = u.user_id", [recipe_id])
    recipe = cursor.fetchone()
    cursor.execute("SELECT food, unit, amount FROM ingredient WHERE ingredient_id IN (SELECT ingredient_id FROM recipe_ingredient where recipe_id = %s)", [recipe_id])
    ingredients = cursor.fetchall()
    cursor.execute("SELECT protein, fat, carbs, calorie FROM nutrient WHERE id IN (SELECT nutrient_id FROM recipe where recipe_id = %s)",[recipe_id])
    nutrients = cursor.fetchone()
    cursor.close()
    return render_template("recipe.html", recipe_id=recipe_id, recipe=recipe, ingredients=ingredients, nutrients=nutrients)


@app.route("/myrecipes", methods=['GET', 'POST'])
def myrecipes_page():
    user = session["user"]
    cursor = db.connection.cursor()
    cursor.execute("SELECT user_id FROM user WHERE username = %s", [user])
    user_id = cursor.fetchone()
    id = user_id['user_id']
    return redirect(url_for("recipes_page", user_id=id, public=0, cat="all"))


@app.route("/add_diet", methods=['GET', 'POST'])
def add_diet_page():
    return render_template("add_diet.html")


@app.route("/add_diet_", methods=['GET', 'POST'])
def add_diet_page_():
    if request.method == 'POST':
        p = request.form.get('p')
        if not p:
            p = None
        f = request.form.get('f')
        if not f:
            f = None
        carb = request.form.get('carb')
        if not carb:
            carb = None
        cal = request.form.get('cal')
        if not cal:
            cal = None

        user = session["user"]
        cursor = db.connection.cursor()
        cursor.execute("SELECT user_id FROM user WHERE username = %s", [user])
        user_id = cursor.fetchone()
        u_id = user_id['user_id']

        cursor.execute("SELECT id FROM nutrient WHERE id IN (SELECT diet_id FROM user WHERE user_id = %s)", [u_id])
        if cursor.rowcount == 0:
            query = "INSERT INTO nutrient VALUES(%s, %s, %s, %s, %s)"
            cursor.execute(query, (None, p, f, carb, cal))
            db.connection.commit()
            nut_id = cursor.lastrowid
            query = "UPDATE user SET diet_id = %s WHERE user_id = %s"
            values = (nut_id, u_id)
            cursor.execute(query, values)
            db.connection.commit()
        else:
            nut = cursor.fetchone()
            query = "UPDATE nutrient SET protein = %s, fat = %s, carbs = %s, calorie = %s WHERE id = %s"
            values = (p, f, carb, cal, nut['id'])
            cursor.execute(query, values)
            db.connection.commit()
        cursor.close()
    return redirect(url_for("user_page"))















