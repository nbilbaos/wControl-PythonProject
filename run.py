from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True permite que el servidor se reinicie si cambias código
    #app.run(debug=True)
    app.run()