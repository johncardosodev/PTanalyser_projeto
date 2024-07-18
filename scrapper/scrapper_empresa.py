import os
import requests
from bs4 import BeautifulSoup
from mysql.connector import connect , Error


PROXY = os.getenv('PROXY') #Este é o proxy que vamos usar para fazer os pedidos
proxies = {
    "http": PROXY,
    "https": PROXY,
}

def scrape_empresa(website_index):
    response = requests.get("https://pt.teamlyzer.com"+website_index, proxies=proxies) #Aqui estamos a fazer o pedido à página
    soup= BeautifulSoup(response.text, "html.parser") #Aqui estamos a criar um objeto BeautifulSoup

    info_total = soup.select('div.col-lg-8:not(.ethical_ad)') #Seleccao de todas as divs com a classe col-lg-8 e que não tenham a classe ethical_ad

    #encontrar dentro do soup <h1>ERRO 404!</h1>
    if soup.find("h1").text == "ERRO 404!":
        print("Encontrou um erro 404!")
        return #terminar funcao
        
    #SQL para inserir os dados na tabela empresa
    sql = f"""
    INSERT INTO `bdptanalyser`.`empresa` (
        `nome`, `website`, `descricao`, `rating`, `taxa_recomendacao`, 
        `salario_medio`, `horas_trabalho`, `dificuldade`, `tx_feedback`, 
        `investimento_tempo`, `website_index`, `trabalhador_id`, `industria_id`
    )
    VALUES (
        '{nome_empresa(info_total)}', '{website(info_total)}', '{descricao(info_total)}', '{rating(info_total)}', 
        '{tx_recomendacao(info_total)}', '{salario_medio(info_total)}', '{horas_trabalho(info_total)}', 
        '{dificuldade_entrevista(info_total)}', '{tx_feedback(info_total)}', '{investimento_tempo(info_total)}', '{website_index}',
        (SELECT id FROM bdptanalyser.trabalhador WHERE numero='{trabalhadores(info_total)}'), 
        (SELECT id FROM bdptanalyser.industria WHERE designacao='{industria(info_total)}')
    )
    ON DUPLICATE KEY UPDATE 
        nome = VALUES(nome),
        website = VALUES(website),
        descricao = VALUES(descricao),
        rating = VALUES(rating),
        taxa_recomendacao = VALUES(taxa_recomendacao),
        salario_medio = VALUES(salario_medio),
        horas_trabalho = VALUES(horas_trabalho),
        dificuldade = VALUES(dificuldade),
        tx_feedback = VALUES(tx_feedback),
        investimento_tempo = VALUES(investimento_tempo),
        website_index = VALUES(website_index),
        trabalhador_id = VALUES(trabalhador_id),
        industria_id = VALUES(industria_id)  
    ;
    """
    numero_linhas=inserir_base_dados(sql)
    
    #SQL para inserir os dados na tabela tecnologias porque esta tabela é uma tabela de muitos para muitos
    stacks = tecnologias(soup)
    for tecnologia in stacks:
        sqlTech = f"""
        INSERT INTO `bdptanalyser`.`tecnologias_has_empresa` (`tecnologias_id`, `empresa_id`)
        SELECT t.id, e.id
        FROM bdptanalyser.tecnologias t
        JOIN empresa e ON e.website_index = '{website_index}'
        WHERE t.nome = '{tecnologia}'
        AND NOT EXISTS (
            SELECT 1
            FROM bdptanalyser.tecnologias_has_empresa te
            WHERE te.tecnologias_id = t.id
            AND te.empresa_id = e.id
        );
        """        
        inserir_base_dados(sqlTech)
    # Execute the SQL statement
    return numero_linhas>0 #Se o numero de linhas afetadas for maior que 0 true, senao false

def atualizar_website_index(min_page, max_page):
    lista_empresas_verificar = get_companies(min_page, max_page) #Obter a lista de empresas no site
    lista_empresas_base_dados = buscar_base_dados("SELECT website_index FROM bdptanalyser.empresa") #Obter a lista de empresas na base de dados
    lista_empresas_novas=[]
    
    for website_index in lista_empresas_verificar: #Iterar sobre todas as empresas no site   
        if website_index not in lista_empresas_base_dados: #Se a empresa não estiver na base de dados
            lista_empresas_novas.append(website_index) #Adicionar a empresa à lista de empresas novas
            scrape_empresa(website_index) #Scrape a empresa
    return lista_empresas_novas #Devolver a lista de empresas novas


def eliminar_empresa(website_index):     
    eliminar_tecnologias(website_index) #Eliminar as tecnologias da empresa antes de eliminar a empresa por causa da foreign key
    sql = f"DELETE FROM bdptanalyser.empresa WHERE website_index='{website_index}'"
    numero_linhas = inserir_base_dados(sql)
    return numero_linhas>0 #Se o numero de linhas afetadas for maior que 0 true, senao false


def eliminar_tecnologias(website_index):
    # SQL statement to delete a specific row from the table
    sql = f"DELETE FROM bdptanalyser.tecnologias_has_empresa WHERE empresa_id IN (Select id FROM empresa WHERE website_index='{website_index}')"
    inserir_base_dados(sql)
    numero_linhas = inserir_base_dados(sql)
    return numero_linhas>0 #Se o numero de linhas afetadas for maior que 0 true, senao false
    

######################################## info inicial da empresa #########################################################################
def nome_empresa(info_total):
    nome_empresa=info_total[0].find("h1", class_="reduce-h1 text-default-xs").text.strip() #Encontramos aqui o nome da empresa
    return nome_empresa.replace("'", "-") #Aqui estamos a substituir todas as aspas simples por um hifen para evitar problemas com a query

def industria(info_total):
    industria=info_total[0].find_all("div", class_="center_mobile hidden-xs company_add_details")[0].text.strip().splitlines()
    #Encontramos aqui a industria da empresa e dividimos usando "line" como separador     
    return industria[0]

def trabalhadores(info_total):
    industria=info_total[0].find_all("div", class_="center_mobile hidden-xs company_add_details")[0].text.strip().splitlines()
    #Encontramos aqui a industria da empresa e dividimos usando "line" como separador     
    return industria[2]

def website(info_total):
    allUrls=info_total[0].find_all("div", class_="center_mobile hidden-xs company_add_details") #Aqui estamos a encontrar todas as divs com a classe center_mobile
    urls=allUrls[0].find_all('a', href=lambda href: href and href.startswith('http://') or href.startswith('https://') or href.startswith('www.')) #Aqui estamos a encontrar todas as tags a que tenham .com no href 
    for url_tag in urls: #Aqui estamos a iterar sobre todas as tags a que encontramos 
        url = url_tag['href'] #Aqui estamos a obter o valor do atributo href
    if len(urls) == 0:
        url = ""
    
    return url

def descricao(info_total):
    descricao=info_total[0].find("div", class_="ellipsis center_mobile").text.strip() #Encontramos aqui a descricao da empresa
    descricao=descricao.replace("'", "-") #Aqui estamos a substituir todas as aspas simples por um hifen para evitar problemas com a query
    descricao=descricao.replace('"', "-") #Aqui estamos a substituir todas as aspas simples por um hifen para evitar problemas com a query
    return descricao

def rating(info_total):
    rating=info_total[0].select("div.text-center") #Aqui estamos a encontrar todas as divs com a classe text-center
    
    #Aqui estamos a dividir a string em duas partes, usando " / " como separador e a 
    #ficar com a primeira parte     
    rating=rating[0].text.strip().split("/", 1)[0] 
    return rating

#################################### Tecnologia ##################################################################################################
def tecnologias(soup):
    
    try:
        #find in info_total the dive in tags voffset2 tags_popover
        tag_container=soup.find("div", class_="wrapper-tags-reviews-answered-rate") #Aqui estamos a encontrar todas as divs com a classe voffset2 e tags_popover
        # Find all <a> tags within the <div> with class "tags voffset2 tags_popover"
        tag_div = tag_container.find('div', class_='tags voffset2 tags_popover')
        tag_links = tag_div.find_all('a')

        # Extract tag names and URLs
        tag_info = [(link.text, link['href']) for link in tag_links]

        # Extract tags from the button's data-content attribute
        button_content = soup.find('button', class_='btn btn-link button_plus')['data-content']
        button_soup = BeautifulSoup(button_content, 'html.parser')
        additional_tags = button_soup.find_all('a')

        # Add additional tags to tag_info list
        tag_info += [(tag.text, tag['href']) for tag in additional_tags]

        # Print tag names and URLs
        tag=[]
        for name in tag_info:
            tag.append(name[0])
    except:
        tag = ""    
    return tag
################################### Reviews de funcionários e candidatos #########################################################################
def tx_recomendacao(info_total):
    try:
        tx_recomendacao = info_total[0].find_all("p", class_="size-h2")[0].text.strip()
    except IndexError:
        tx_recomendacao = "" #vazio se nao tiver recomendacao

    return tx_recomendacao


def salario_medio(info_total):

    try:
        salario_medio=info_total[0].find_all("p", class_="size-h2")[1].text.strip() #Encontramos aqui o salario medio da empresa
    except IndexError:
        salario_medio = "" #vazio se nao tiver recomendacao

    return salario_medio

def horas_trabalho(info_total):    
    try:
        horas_trabalho=info_total[0].find_all("p", class_="size-h2")[2].text.strip() #Encontramos aqui o horas medio da empresa
    except IndexError:
        horas_trabalho = "" #vazio se nao tiver recomendacao

    return horas_trabalho

def dificuldade_entrevista(info_total):
    try:
        dificuldade_entrevista=info_total[0].find_all("p", class_="size-h2")[3].text.strip().split("/", 1)[0]  #Encontramos aqui a dificuldade da entrevista da empresa
    except IndexError:
        dificuldade_entrevista = "" #vazio se nao tiver recomendacao    

    return dificuldade_entrevista

def tx_feedback(info_total):

    try:
        tx_feedback=info_total[0].find_all("p", class_="size-h2")[4].text.strip() #Encontramos aqui a taxa de feedback da empresa
    except IndexError:
        tx_feedback = "" #vazio se nao tiver recomendacao      

    return tx_feedback

def investimento_tempo(info_total):
    try:
        investimento_tempo=info_total[0].find_all("p", class_="size-h2")[5].text.strip() #Encontramos aqui o investimento de tempo da empresa
    except IndexError:
        investimento_tempo = "" #vazio se nao tiver recomendacao    

    return investimento_tempo

################################### Função base de dados #########################################################################
def connect_to_database(): # Definir a função connect_to_database
    mysql_database_user = "Raquel"
    mysql_database_user_password = "Silva1234"
    mysql_database_name = "bdptanalyser"
    mysql_database_host = "62.28.39.135"

    return connect( # Retornar uma conexão à base de dados
        host=mysql_database_host, # Utilizar a variável mysql_database_host do ficheiro config.py
        user=mysql_database_user, # Utilizar a variável mysql_database_user do ficheiro config.py
        password=mysql_database_user_password, # Utilizar a variável mysql_database_user_password do ficheiro config.py
        database=mysql_database_name, # Utilizar a variável mysql_database_name do ficheiro config.py
        charset='utf8mb4', # Utilizar o conjunto de caracteres utf8mb4 (suporta emojis) e charset português
        collation='utf8mb4_unicode_ci' # Utilizar a colação utf8mb4_unicode_ci (suporta emojis)    
    )

def inserir_base_dados(sql):
    import mysql.connector # Importar o módulo mysql.connector. Dá yellow porque não está a ser usado, mas está a ser usado
    numero_linhas = 0    
    try:
        # Connectar à base de dados
        db = connect_to_database()
        cursor = db.cursor()       

        # Execute the SQL statement
        cursor.execute(sql)

        # Fazer commit da transação
        db.commit()  

        numero_linhas = cursor.rowcount #Obter o número de linhas afetadas pela query

        
    except mysql.connector.Error as err:
        print("Error:", err)

    finally:
        # Close MySQL connection
        if db.is_connected():
            cursor.close()
            db.close()
    return numero_linhas #Devolve o número de linhas afetadas pela query

def buscar_base_dados(sql):
    import mysql.connector
    try:
        # Connectar à base de dados
        db = connect_to_database()
        cursor = db.cursor()       

        # Execute the SQL statement
        cursor.execute(sql)

        # Fetch the result
        results = cursor.fetchall()
        return results
        
    except mysql.connector.Error as err:
        print("Error:", err)

    finally:
        # Close MySQL connection
        if db.is_connected():
            cursor.close()
            db.close()
    
def get_website_(column_name):
    try:
        # Connect to MySQL
        db = connect_to_database()
        cursor = db.cursor()       

        # SQL statement to select specific text from the table
        sql = "SELECT {column1} FROM `empresa`".format(column1=column_name)

        # Execute the SQL statement
        cursor.execute(sql)

        # Fetch the result
        results = cursor.fetchall()

        # Extract the specific text for every row
        specific_texts = [row[0] for row in results] #devolve a lista com os valores da coluna website_index

        return specific_texts #devolve a lista com os valores da coluna website_index

    except mysql.connector.Error as err:
        print("Error:", err)

    finally:
        # Close MySQL connection
        if db.is_connected():
            cursor.close()
            db.close()

def get_companies(min_page, max_page):
    #Este loop irá correr todas as empresas existentes da pagina min e max.
    #Assim descobrimos o index de cada empresa no site ptAnalyser para percorrar depois toda a informaçao 
    companies = [] #Dicionario com as empresas e os links 
    for i in range(min_page, max_page):
        URL = "https://pt.teamlyzer.com/companies/?page=" + str(i)
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")
        result= soup.find_all("h3", class_="voffset0") #
        #companies para lista     
        
        for r in result:
            companies.append(f"{r.a['href']}") #nome da empresa e link a um dicionario
            

    return companies

def scrape_tech(url="https://pt.teamlyzer.com/companies/"):

    response = requests.get(url, proxies=proxies)
    soup = BeautifulSoup(response.text, features="html.parser")
    
    tech=[]
    stack_container = soup.find_all("div", class_="form_field")[3]
    options = stack_container.find_all("option")
    for option in options:
        tech.append(option.text)
    #stack= stack_container.find_all("option")
    #print(stack)
    return tech #devolve a lista com as tecnologias

################################### Função principal #########################################################################
#if __name__ == '__main__':
    
    #for i in range(0, len(website_index)):
     #  scrape_empresa(website_index[i])
      # print(website_index[i])
#    scrape_empresa('/companies/slim-business-solutions')
            
#novasEMpresas=atualizar_website_index(774, 779) # Atualizar o website_index das empresas entre 1 e 2
#print(novasEMpresas)





