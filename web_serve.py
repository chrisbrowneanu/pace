from waitress import serve
import web_app

serve(web_app.app, host='0.0.0.0', port=8080)