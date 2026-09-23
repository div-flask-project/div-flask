from flask import Flask, render_template


def create_app():
    app  = Flask(__name__)

    @app.route('/')
    def index():
        return "flask team project!!"

    @app.route('/main_product')
    def main_product():
        return render_template('product/main_product.html')

    @app.route('/sub_product')
    def sub_product():
        return render_template('product/sub_product.html')

    return app