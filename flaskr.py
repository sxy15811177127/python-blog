import os
import sys

import sqlite3
from flask import Flask,request,session,g,redirect,url_for,abort,\
     render_template,flash
from contextlib import closing

app = Flask(__name__)             #创建Flask类的一个实例app
sys.path.append(app.root_path)
'''configuration'''
class Config(object):
    DATABASE=os.path.join(app.root_path, 'flaskr.db') #os.path.join是连接目录和文件名的方法 
    #print(DATABASE)
    DEBUG = False                                     #os.path.join("D:\","test.txt")结果是D:\test.txt（只连接，不写入数据的话不生成这个文件）
    SECRET_KEY = 'development key'                    #生成用os.mkdir(os.path.join("D:\","test.txt"))
    USERNAME = 'admin'                                #.root_path属性可以获取该应用的路径
    PASSWORD = 'default'
#print(Config.DATABASE)

app.config.from_object(Config)    #.from_object()会从给定的对象中寻找所有 。大写。的变量
#print(app.config)#并导入（注意下面configuration部分，变量为大写）
                                  #如果把config写在一个单独的文件中
                                  #使用app.config.from_envvar('FLASKR_SETTINGS', silent=True)///FLASKR_SETTINGS不是一个文件
                                  #只需设置一个名为 FLASKR_SETTINGS 的环境变量，指向要加载的配置文件      



                                               
'''创建一个到数据库的连接，只是个简单的例子'''
def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    #rv = sqlite3.connect('DATABASE')            #DATABASE变量在这里用到了，sqlite3.connect（路径/内存），连接或创建数据库
    rv.row_factory = sqlite3.Row                 #rv是数据库链接对象，有以下的操作：commit(),rollback(),close(),cursor()
    return rv                                    #在sqlite3中，所有sql语句的执行都要在游标对象的参与下完成，cu = rv.cursor()创建游标
                                                 #如果config写在了这个模块里的话，connect括号里直接写DATABASE应该也可以吧？
                                                 #为了简化查询，利用行工厂函数，该函数会转换每次从数据库返回的结果。
                                                 #使用.row_factory属性来更改返回值的表现方式，暂时理解为改变了rv中数据的‘格式’
                                                 #例如，为了得到字典类型而不是元组类型的返回结果，可以写成左面的形式
    

'''数据库连接部分:Flask 提供了两种环境（Context）：应用环境（Application Context）和请求环境（Request Context）'''
def get_db():  #这个函数首次调用的时候会为当前环境创建一个数据库连接，调用成功后返回已经建立好的连接
    if not hasattr(g, 'sqlite_db'):  #如果g对象中没有属性sqlite_db，hasattr用于确定一个对象是否具有某个属性 hasattr(object, name) -> bool
        g.sqlite_db = connect_db()   #则创建该属性，（暂时理解为sqlite_db属性是我们自己命名的，换成x也一样，只是创造的一个条件）
    return g.sqlite_db               #并返回该属性,即首次调用get_db()函数时，通过connect_db()建立一个数据库连接并返回
                                     #为什么要把connect_db()给g呢？

'''断开数据库连接部分'''       #疑问：这个装饰器让close_db函数实现了自动调用吗？为什么是在应用环境销毁时调用
@app.teardown_appcontext   #teardown_appcontext装饰器标记的函数，会在每次应用环境销毁时调用，应用环境在请求传入前创建，请求结束时销毁，
def close_db(error):       #销毁有两种原因：正常（错误参数会是None），发生异常
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):  
        g.sqlite_db.close() #暂时理解为g的sqlite_db属性靠close（）方法来删除，没有这个方法 就意味着关闭了与数据库的连接


'''创建数据库'''
def init_db():  #定义一个初始化数据库的函数（文档提到要把这个函数放在connect_db函数的后面，一定吗?）
    with app.app_context(): #由于是定义一个函数，所以我们并没有请求，也就没有建立应用环境，无法使用g。这一语句就是创建应用环境
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f: #接触了新的方法.open_resource 和新的语法 with as
            a=f.read()                                       #read()方法只能读一次 一定要用变量保存
            db.cursor().executescript(a)              #open_resource方法从app所在的位置打开文件schema.sql 
        with app.open_resource('dbuser.sql', mode='r') as g: #创建了一个叫user的table 存放注册用户信息
            b=g.read()
            db.cursor().executescript(b)
        db.commit()                                          #但是这句和db.cursor().executescript(\path\schema.sql)有什么区别呢？？




'''-------------------------------------------
------数据库连接部分已经写完，下面开始写视图函数------
-------------------------------------------'''

'''show entries'''
@app.route('/')   #它绑定在应用的根地址
def show_intro():
  
    return render_template('Intro.html')



'''添加条目'''
@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_intro'))




'''登录'''
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:                            #暂时理解为session是个字典
            session['logged_in'] = True  #session不是在一个函数中的变量吗，怎么保证这个变量是全局的，还是说在flask框架中
            flash('You were logged in')  #session这个名字的变量，直接可以看做是全局的
            return redirect(url_for('show_intro'))
    return render_template('login.html', error=error)





'''登出'''
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_intro'))

'''注册功能'''
#@app.route('/register')
#def reg_user():
#    











if __name__ == '__main__':                       #把这个文件当做独立应用来运行
    app.run()























