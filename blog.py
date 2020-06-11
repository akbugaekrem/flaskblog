from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,BooleanField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#Kullanici Giris Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bitte melden Sie sich an, um diese Seite anzuzeigen ...","danger")
            return redirect(url_for("login"))

    return decorated_function
#Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name=StringField("Vorname Nachname",validators=[validators.DataRequired()])
    username=StringField("BenutzerName",validators=[validators.Length(min=4,max=30,message="Lütfen kullanıcı adınızı giriniz...")])
    email=StringField("Email",validators=[validators.Email(message="Lütfen geçerli bir mail adresi giriniz...")])
    password=PasswordField("Kennwort:",validators=[
        validators.DataRequired(message="Setzen Sie bitte ein Kennwort"),
        validators.EqualTo(fieldname="confirm",message="Ihr Kennwort stimmt leider nicht überein...\nGeben Sie bitte ein richtiges Kennwort ein...")
    ])
    confirm=PasswordField("Bestätigen Sie Ihr Kennwort")

#Login Formu Olusturma
class LoginForm(Form):
    username=StringField("BenutzerName",validators=[validators.Length(min=4,max=20,message="Lütfen kullanıcı adınızı giriniz...")])
    password=PasswordField("Kennwort:",validators=[validators.DataRequired(message="Lütfen Bir Tane Parola Giriniz....")])






app=Flask(__name__)
app.secret_key="ekremblog"
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="ekremblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql=MySQL(app)

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/about")
def about():
    return render_template("about.html")
#Makale Sayfasi Görüntüleme
@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()
    sorgu="Select * From articles"
    result=cursor.execute(sorgu)
    if result>0:    #veritabanimizda makale var demek
        articles=cursor.fetchall()
        return render_template("articles.html",articles=articles)

    else:   #else kismi da veritabanimizda makale yoksa result 0 ise demek
        return render_template("articles.html")
    
        

#Kayit Olma
@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)

    if request.method=="POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)

        cursor=mysql.connection.cursor()

        sorgu="Insert into users(name,email,username,password) VALUES (%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()

        cursor.close()
        flash("Sie haben sich erfolgreich registriert ...","success")

        return redirect(url_for("login"))


    else:

        return render_template("register.html",form=form)
#Kontrol Paneli Olusturma
@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles where author=%s"
    result=cursor.execute(sorgu,(session["username"],))
    if result>0:
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")
#Login  islemi
@app.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm(request.form)
    if request.method=="POST":
        username=form.username.data
        password_entered=form.password.data
        cursor=mysql.connection.cursor()

        sorgu="Select * From users where username=%s"
        result=cursor.execute(sorgu,(username,))
        if result>0:
            data=cursor.fetchone()
            real_password=data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Sie haben sich erfolgreich angemeldet...","success")
                session["logged_in"]=True
                session["username"]=username
                return redirect(url_for("index"))
            else:
                flash("Sie haben Ihr Kennwort falsch eingegeben ...","danger")
                return redirect(url_for("login"))





        else:
            flash("Es gibt keinen solchen Benutzer ...","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form=form)
#Detay Sayfasi Olusturma
@app.route("/article/<string:id>")
def article(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * From articles where id=%s"
    result=cursor.execute(sorgu,(id,))
    if result>0:
        article=cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")
#Logout islemi
@app.route("/logout")
def logout():
    session.clear()
    flash("Sie haben sich erfolgreich abgemeldet...","success")
    return redirect(url_for("index"))

    


#makale ekleme
@app.route("/addarticle", methods=["GET","POST"])
def addarticle():
    form=ArticleForm(request.form)
    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data


        cursor=mysql.connection.cursor()
        sorgu="Insert into articles(title,author,content) VALUES (%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Artikel wurde erfolgreich hinzugefügt...","success")
        return redirect(url_for("dashboard"))
    else:
        return render_template("addarticle.html",form=form)
#makale silme islemi
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles where author=%s and id=%s"
    result=cursor.execute(sorgu,(session["username"],id))
    if result>0:
        sorgu2="Delete from articles where id=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Es gibt entweder einen solchen Artikel oder solche Autorität","danger")
        return redirect(url_for("index"))

#makale güncelleme islemi
@app.route("/edit/<string:id>", methods=["GET","POST"])
@login_required
def update(id):
    if request.method=="GET":
        cursor=mysql.connection.cursor()
        sorgu="Select * from articles where id=%s and author=%s"
        result=cursor.execute(sorgu,(id,session["username"]))
        if result==0:
            flash("Es gibt entweder einen solchen Artikel oder solche Autorität...","danger")
            return redirect(url_for("index"))
        else:
            article=cursor.fetchone()
            form=ArticleForm()
            form.title.data=article["title"]
            form.content.data=article["content"]
            return render_template("update.html",form=form)

    else:
        form=ArticleForm(request.form)
        newTitle=form.title.data
        newContent=form.content.data
        sorgu2="Update articles Set title=%s,content=%s  where id=%s "
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Artikel wurde erfolgreich aktualisiert ...","success")
        return redirect(url_for("dashboard"))











#Arama Url islemi
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")
        cursor=mysql.connection.cursor()
        sorgu="Select * from articles where title like '%"+ keyword +"%'"
        result=cursor.execute(sorgu)
        if result==0:
            flash("Es wurden keine Artikel gefunden, die dem gesuchten Wort entsprechen ...","warning")
            return redirect(url_for("articles"))
        else:
            articles=cursor.fetchall()
            return render_template("articles.html",articles=articles)
            




#makale form
class ArticleForm(Form):
    title=StringField("Die Überschrift des Artikels",validators=[validators.length(min=5,max=100,message="Lütfen Makale Başlığı Giriniz...")])
    content=TextAreaField("Der Inhalt des Artikels",validators=[validators.length(min=10)])


if __name__=="__main__":
    app.run(debug=True)
