# Alias entry point for TaskFlow
from tut1 import app, db

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
