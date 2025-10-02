from app import create_app

app = create_app()

if __name__ == "__main__":
    # debug True para desarrollo (no dejar en producción)
    app.run(debug=True, port=5000)
