from flask import Flask, redirect, url_for, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    """
    Home page.

    Returns
    -------
    template
        Renders the template.
    """

    return render_template("index.html")

@app.route("/about")
def about():
    """
    About page.

    Returns
    -------
    template
        Renders the template.
    """

    return render_template("about.html")

@app.route("/github")
def github():
    """
    Redirects to GitLab repository.

    Returns
    -------
    url
        Redirect to specified URL.
    """

    return redirect("https://github.com/liviuvj/sentiment-analysis-platform")

@app.route("/colab")
def colab():
    """
    Redirects to Google Colab notebook.

    Returns
    -------
    url
        Redirect to specified URL.
    """

    return redirect("https://colab.research.google.com/drive/1d_obU9idFqjsDi7ezeFs1CORxTUAgh7V#offline=true&sandboxMode=true")

@app.route("/dockerhub")
def dockerhub():
    """
    Redirects to DockerHub repository.

    Returns
    -------
    url
        Redirect to specified URL.
    """

    return redirect("https://hub.docker.com/r/liviuvj/airbyte-source-twitter/tags")

@app.errorhandler(400)
def bad_request_error(e):
    """
    Error 400: Bad Rquest page.

    Parameters
    ----------
    e : str
        Error trace.

    Returns
    -------
    template
        Renders the error 400 page.
    """

    return render_template("error400.html", error=e), 404

@app.errorhandler(404)
def not_found_error(e):
    """
    Error 404: Not Foud page.

    Parameters
    ----------
    e : str
        Error trace.

    Returns
    -------
    template
        Renders the error 404 page.
    """

    return render_template("error404.html"), 404

@app.errorhandler(405)
def method_not_allowed(e):
    """
    Error 405: Method Not Allowed page.

    Parameters
    ----------
    e : str
        Error trace.

    Returns
    -------
    template
        Renders the error 405 page.
    """

    return render_template("error405.html"), 404

@app.errorhandler(500)
def server_error(e):
    """
    Error 500: Internal Server Error page.

    Parameters
    ----------
    e : str
        Error trace.

    Returns
    -------
    template
        Renders the error 500 page.
    """

    return render_template("error500.html", error=e), 500

def get_app():
    """
    Function that returns the app, necessary for the Google Colab Notebook.

    Returns
    -------
    flask.app.Flask
        The app.
    """

    return app

if __name__ == "__main__":

    # Run app
    app.run(host="0.0.0.0", debug=False)