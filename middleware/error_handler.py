from flask import jsonify
from werkzeug.exceptions import HTTPException
import traceback

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description)
        }), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication is required to access this resource'
        }), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({
            'error': error.name,
            'message': error.description
        }), error.code

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        # Log the full error for debugging
        app.logger.error(f'Unhandled error: {str(error)}')
        app.logger.error(traceback.format_exc())
        
        # In production, don't return the actual error
        if app.config['DEBUG']:
            message = str(error)
            stack_trace = traceback.format_exc()
        else:
            message = 'An unexpected error occurred'
            stack_trace = None
            
        response = {
            'error': 'Internal Server Error',
            'message': message
        }
        
        if stack_trace and app.config['DEBUG']:
            response['stack_trace'] = stack_trace
            
        return jsonify(response), 500