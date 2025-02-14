import os
import csv
from flask import Flask, Blueprint, request, jsonify, flash, redirect, url_for, render_template
from flask_caching import Cache
from werkzeug.serving import WSGIRequestHandler
from werkzeug.utils import secure_filename
from models import Produto
from database import get_db

# Configuração do Flask
app = Flask(__name__)

# Aumenta o timeout global para 60 segundos
WSGIRequestHandler.timeout = 60

# Configuração do cache
cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)

# Configuração de uploads
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'txt'}

# Criação do Blueprint
routes = Blueprint("routes", __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Função para formatar os números corretamente
def formatar_numero(valor):
    return f"{float(valor):.2f}".replace('.', ',')  # Converte corretamente para 2 casas decimais

# Rota principal para upload de arquivos
@routes.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nenhum arquivo enviado', 'error')
            return redirect(url_for('routes.index'))

        arquivo = request.files['file']
        if arquivo.filename == '':
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(url_for('routes.index'))

        if arquivo and allowed_file(arquivo.filename):
            filename = secure_filename(arquivo.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            arquivo.save(os.path.join(UPLOAD_FOLDER, filename))

            with open(os.path.join(UPLOAD_FOLDER, filename), 'r') as file:
                reader = csv.reader(file, delimiter=';')
                produtos = []

                with next(get_db()) as db:
                    db.execute("SET statement_timeout TO 30000;")  # Timeout do banco para 30s
                    db.query(Produto).delete()
                    db.commit()

                    for row in reader:
                        try:
                            id_produto = row[0].zfill(10)  # Mantém zeros à esquerda
                            descricao = row[1]
                            valor = formatar_numero(row[2])  # Formata o valor corretamente
                            unidade = row[3]

                            produto = Produto(id=int(id_produto), codigo=id_produto, descricao=descricao, valor=valor, unidade=unidade)
                            db.add(produto)
                            produtos.append(produto)
                        except ValueError:
                            flash('Erro ao processar linha do arquivo. Verifique o formato.', 'error')
                            db.rollback()
                            break  

                    if produtos:
                        db.commit()
                        cache.delete('produtos_cache')  # Limpa o cache ao atualizar os produtos
                        flash('Arquivo enviado e atualizado com sucesso!', 'success')
                    else:
                        flash('Nenhum produto processado. Verifique o arquivo.', 'warning')

            return redirect(url_for('routes.index'))

    return render_template('index.html')

# Rota para obter produtos com paginação e cache
@routes.route('/produtos', methods=['GET'])
@cache.cached(timeout=60, key_prefix='produtos_cache')  # Cache de 60 segundos
def get_produtos():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    with next(get_db()) as db:
        db.execute("SET statement_timeout TO 30000;")  # Timeout do banco para 30s
        produtos = db.query(Produto).limit(per_page).offset((page - 1) * per_page).all()

        return jsonify([
            {
                'id': produto.id,
                'codigo': produto.codigo,
                'descricao': produto.descricao,
                'valor': produto.valor,
                'unidade': produto.unidade
            } for produto in produtos
        ])

# Registra o Blueprint no Flask
app.register_blueprint(routes)

# Executa a aplicação
if __name__ == '__main__':
    app.run(debug=True, threaded=True)  # Ativa threads para melhor desempenho
