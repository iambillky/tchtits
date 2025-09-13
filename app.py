"""
File: app.py
Purpose: Main Flask application entry point for DCMS
Created: 2024-09-13
Author: DCMS Team

Revision History:
- 2024-09-13: Initial Flask app setup with dark theme
- 2024-09-13: Added SQLAlchemy database initialization
- 2024-09-13: Integrated data center blueprint
"""

from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# ========== APPLICATION INITIALIZATION ==========

# Initialize Flask application
app = Flask(__name__)

# ========== CONFIGURATION ==========

# Configuration
app.config['SECRET_KEY'] = 'dev-key-change-this-in-production'
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dcms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ========== DATABASE SETUP ==========

# Initialize database
from models.datacenter import db
db.init_app(app)

# ========== BLUEPRINT REGISTRATION ==========

# Register blueprints
from routes.datacenters import datacenters_bp
app.register_blueprint(datacenters_bp)

# Create tables
with app.app_context():
    db.create_all()

# ========== ROUTE HANDLERS ==========

@app.route('/')
def index():
    """Home page - Dashboard"""
    # Get summary data for dashboard
    from models.datacenter import DataCenter, Rack
    
    dc_count = DataCenter.query.count()
    rack_count = Rack.query.count()
    
    # Calculate total IPs (placeholder for now)
    ip_count = 0
    
    return render_template('index.html', 
                         title='Data Center Management System',
                         current_date=datetime.now().strftime('%B %d, %Y'),
                         current_year=datetime.now().year,
                         dc_count=dc_count,
                         rack_count=rack_count,
                         ip_count=ip_count)

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Data Center Management System'
    })

@app.route('/about')
def about():
    """About page with system information"""
    return render_template('about.html',
                         title='About DCMS',
                         version='1.0.0',
                         current_date=datetime.now().strftime('%B %d, %Y'),
                         current_year=datetime.now().year)

@app.route('/favicon.ico')
def favicon():
    """Return a 204 No Content for favicon requests"""
    return '', 204

# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

# ========== APPLICATION ENTRY POINT ==========

if __name__ == '__main__':
    # Run the development server
    # Note: On Windows, you might need to set host='127.0.0.1'
    app.run(host='127.0.0.1', port=5000, debug=True)