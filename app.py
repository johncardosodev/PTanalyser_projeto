from flask import Flask, redirect, request, session, url_for, \
    render_template  # Importar as classes Flask, redirect, request, session, url_for e render_template do módulo flask
from mysql.connector import connect  # Importar a função connect do módulo mysql.connector
from config import *  # Importar as variáveis de configuração
from scrapper.scrapper_empresa import scrape_empresa, eliminar_empresa, atualizar_website_index

app = Flask(__name__)  # Criar um objeto da classe Flask
app.config.from_pyfile('config.py')  # Carregar as configurações do ficheiro config.py para o objeto app
# (configurações do Flask)

app.secret_key = 'secret'  # Chave secreta para a sessão


def connect_to_database():  # Definir a função connect_to_database
    return connect(  # Retornar uma conexão à base de dados
        host=mysql_database_host,  # Utilizar a variável mysql_database_host do ficheiro config.py
        user=mysql_database_user,  # Utilizar a variável mysql_database_user do ficheiro config.py
        password=mysql_database_user_password,  # Utilizar a variável mysql_database_user_password do ficheiro config.py
        database=mysql_database_name,  # Utilizar a variável mysql_database_name do ficheiro config.py

        charset='utf8mb4',  # Utilizar o conjunto de caracteres utf8mb4 (suporta emojis) e charset português
        collation='utf8mb4_unicode_ci'  # Utilizar a colação utf8mb4_unicode_ci (suporta emojis)
    )


@app.route('/')  # Decorador que associa a função index à rota /
def index():  # Definir a função index (página inicial de origem)

    return render_template('base.html')  # Renderizar o modelo base.html


@app.route('/login', methods=['GET', 'POST'])  # Decorador que associa a função login à rota /login
def login():
    if request.method == 'POST':
        # Get username and password from the form
        username = request.form['username']
        password = request.form['password']

        db = connect_to_database()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
        user = cursor.fetchone()  # Obter o primeiro registo da tabela users com o username e password fornecidos
        cursor.close()  # Fechar o cursor

        if user:
            session['username'] = user[1]  # Store the username in the session
            if user[3] == 'user':
                return redirect(url_for('queryUser'))  # Redirect to the admin dashboard
            else:
                return redirect(url_for('adminPage'))  # Redirect to the user dashboard

    return render_template('login.html')  # Render the login page with an error message


@app.route('/logout')  # Decorador que associa a função logout à rota /logout
def logout():
    session.pop('username', None)  # Remove the username from the session and none is the default value
    return redirect(url_for('login'))


@app.route('/queryUser', methods=['GET', 'POST'])  # Decorador que associa a função success à rota /success
def queryUser():  #

    if request.method == 'POST':
        query = request.form['query']
        table, column_names = executeQuery(query) # Executar a query e obter a tabela e os nomes das colunas da tabela
        return render_template('queryUser.html', table=table, column_names=column_names) #renderiza a página com a tabela (se houver query
    else:
        return render_template('queryUser.html') #renderiza a página com a tabela vazia para o caso de não haver query


def executeQuery(query):
    db = connect_to_database()
    cursor = db.cursor()
    cursor.execute(query)
    table = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]  # Receber os nomes das colunas da tabela resultante da query
    cursor.close()
    db.close()
    return table, column_names # Retornar a tabela e os nomes das colunas

@app.route('/adminPage', methods=['GET', 'POST'])  # Decorador que associa a função success à rota /success
def adminPage():
    message = ""
    message2 = ""
    if request.method == 'POST':        
        empresa_eliminar = request.form.get('deleteInputField') # Obter o valor do campo de texto com o nome da empresa a eliminar       
        if empresa_eliminar: #Em python empty strings é falso e strings com conteudo é verdadeiro
            if eliminar_empresa(empresa_eliminar): # Se a empresa for eliminada com sucesso
                message += "Empresa eliminada com sucesso! "
            else: # Se a empresa não existir
                message += "Empresa para eliminar não existe!"
        

        empresa_adicionar = request.form.get('addInputField') # Obter o valor do campo de texto com o nome da empresa a adicionar
        if empresa_adicionar:
            if scrape_empresa(empresa_adicionar):
                message += "Empresa adicionada com sucesso!"
            else:
                message += "Empresa para adicionar não existe!"       

        link_min=request.form.get('inputField1')
        link_max=request.form.get('inputField2')
        if link_min and link_max: # Se link_min e link_max não forem vazios
            lista_empresas_novas=[]
            lista_empresas_novas=atualizar_website_index(int(link_min), int(link_max)) # Atualizar o website_index das empresas entre link_min e link_max com cast para int            
            lista_empresas_novas_str = ', '.join(map(str, lista_empresas_novas)) # Converter a lista para uma string separada por vírgulas e adicionar à mensagem
            message2 += f"Empresas atualizadas com sucesso: {lista_empresas_novas_str}"
        else:
            message2 += "Não foi possível atualizar as empresas!"


    return render_template('adminPage.html', message=message, message2=message2) # Renderizar a página adminPage.html com a mensagem



if __name__ == '__main__':  # Se o módulo for executado como script (não foi importado)
    app.run(debug=True)  # Executar o servidor web embutido do Flask em modo de depuração
# Para executar o servidor web embutido do Flask, executar o comando python app.py no terminal
