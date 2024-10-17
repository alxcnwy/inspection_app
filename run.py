from app import create_app

app = create_app()

# Add `getattr` to Jinja2 globals
app.jinja_env.globals.update(getattr=getattr)

if __name__ == '__main__':
    app.run(debug=True)
