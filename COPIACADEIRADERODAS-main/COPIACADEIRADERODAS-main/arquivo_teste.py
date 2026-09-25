from App import app
from database import db, HistoricoDirecao

def teste_insert():
    with app.app_context():
        direcao =  "centro"
        novo_registro = HistoricoDirecao(direcao=direcao)
        db.session.add(novo_registro)
        db.session.commit()
        print(f"Salvo no banco: {direcao} (id={novo_registro.id})")


teste_insert()