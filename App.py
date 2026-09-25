import json
import os
from queue import Empty, Full, Queue
from threading import Lock

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, stream_with_context

from database import db, HistoricoDirecao
from mqtt_service import init_mqtt

load_dotenv()


def create_app(config_teste=None, iniciar_mqtt=True):
    """Cria a aplicação. Testes passam uma configuração SQLite em memória."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if config_teste:
        app.config.update(config_teste)
    else:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL não encontrada no .env. Configure a connection string do Neon.")
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url

    db.init_app(app)
    with app.app_context():
        db.create_all()

    clientes_eventos = set()
    clientes_lock = Lock()

    def publicar_direcao(registro):
        evento = json.dumps(registro)
        with clientes_lock:
            for fila in tuple(clientes_eventos):
                try:
                    fila.put_nowait(evento)
                except Full:
                    pass

    app.config["PUBLICAR_DIRECAO"] = publicar_direcao

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/api/status", methods=["GET"])
    def status():
        return jsonify({"status": "API da Cadeira de Rodas ativa"}), 200

    @app.route("/api/historico", methods=["GET"])
    def obter_historico():
        registros = HistoricoDirecao.query.order_by(HistoricoDirecao.criado_em.desc()).limit(50).all()
        return jsonify([registro.to_dict() for registro in registros]), 200

    @app.route("/api/eventos", methods=["GET"])
    def eventos():
        fila = Queue(maxsize=10)
        with clientes_lock:
            clientes_eventos.add(fila)

        @stream_with_context
        def fluxo():
            yield "retry: 1000\n\n"
            try:
                while True:
                    try:
                        evento = fila.get(timeout=20)
                        yield f"event: direcao\ndata: {evento}\n\n"
                    except Empty:
                        yield ": conexão mantida ativa\n\n"
            finally:
                with clientes_lock:
                    clientes_eventos.discard(fila)

        return Response(
            fluxo(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    if iniciar_mqtt and not app.config.get("TESTING"):
        app.mqtt_client = init_mqtt(app)

    return app

app = create_app(iniciar_mqtt=False)

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True, use_reloader=False)
