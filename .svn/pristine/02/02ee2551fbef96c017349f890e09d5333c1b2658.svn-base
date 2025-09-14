"""
File: app.py
Purpose: Main Flask application entry point for DCMS
Created: 2024-09-13
Author: DCMS Team

Revision History:
- v1.0.0: Initial Flask app setup with dark theme
- v1.0.1: Added SQLAlchemy database initialization
- v1.0.2: Integrated data center blueprint
- v1.1.0: Added network devices blueprint
- v1.2.0: Added PDU management and power profiles
- v1.3.0: Added IPAM module with complete IP tracking
         Imported IPAM models and registered blueprint
         Added IP statistics to dashboard
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
from routes.network_devices import network_devices_bp
from routes.pdus import pdus_bp
from routes.ipam import ipam_bp

app.register_blueprint(datacenters_bp)
app.register_blueprint(network_devices_bp)
app.register_blueprint(pdus_bp)
app.register_blueprint(ipam_bp)

# ========== DATABASE TABLE CREATION ==========

# Create tables
with app.app_context():
    # Import all models to ensure they're registered with SQLAlchemy
    from models.datacenter import DataCenter, Floor, Rack, PDU
    from models.network_device import NetworkDevice
    from models.power_profiles import PowerProfile, init_default_profiles
    from models.ipam import (
        Network, VLAN, IPRange, IPPool, IPAddress, IPHistory,
        process_quarantine_expirations
    )
    
    # Create all tables
    db.create_all()
    
    # Initialize default power profiles for TCH equipment
    existing_profiles = PowerProfile.query.count()
    if existing_profiles == 0:
        init_default_profiles(db.session)
        print("Initialized TCH power profiles")
    
    # Process any expired IP quarantines on startup
    expired_count = process_quarantine_expirations()
    if expired_count > 0:
        print(f"Released {expired_count} IPs from expired quarantine")

# ========== ROUTE HANDLERS ==========

@app.route('/')
def index():
    """
    Home page - Dashboard
    Shows overview of entire infrastructure
    """
    # Get summary data for dashboard
    from models.datacenter import DataCenter, Rack, PDU
    from models.network_device import NetworkDevice
    from models.ipam import Network, IPAddress, VLAN
    
    # Infrastructure counts
    dc_count = DataCenter.query.count()
    rack_count = Rack.query.count()
    network_device_count = NetworkDevice.query.count()
    pdu_count = PDU.query.count()
    
    # IPAM statistics
    network_count = Network.query.count()
    vlan_count = VLAN.query.count()
    total_ips = IPAddress.query.count()
    assigned_ips = IPAddress.query.filter_by(status='assigned').count()
    available_ips = IPAddress.query.filter_by(status='available').count()
    quarantine_ips = IPAddress.query.filter_by(status='quarantine').count()
    
    # Calculate IP utilization
    ip_utilization = 0
    if total_ips > 0:
        ip_utilization = round((assigned_ips / total_ips) * 100, 1)
    
    return render_template('index.html', 
                         title='Data Center Management System',
                         current_date=datetime.now().strftime('%B %d, %Y'),
                         current_year=datetime.now().year,
                         dc_count=dc_count,
                         rack_count=rack_count,
                         network_device_count=network_device_count,
                         pdu_count=pdu_count,
                         network_count=network_count,
                         vlan_count=vlan_count,
                         total_ips=total_ips,
                         assigned_ips=assigned_ips,
                         available_ips=available_ips,
                         quarantine_ips=quarantine_ips,
                         ip_utilization=ip_utilization)

@app.route('/about')
def about():
    """
    About page - System information
    Shows version info and system requirements
    """
    version = "1.3.0"
    return render_template('about.html', version=version)

# ========== API ENDPOINTS ==========

@app.route('/api/stats')
def api_stats():
    """
    API endpoint for dashboard statistics
    Returns JSON with current system metrics
    """
    from models.datacenter import DataCenter, Rack, PDU
    from models.network_device import NetworkDevice
    from models.ipam import Network, IPAddress, VLAN
    
    # Gather all statistics
    stats = {
        'infrastructure': {
            'datacenters': DataCenter.query.count(),
            'racks': Rack.query.count(),
            'network_devices': NetworkDevice.query.count(),
            'pdus': PDU.query.count()
        },
        'ipam': {
            'networks': Network.query.count(),
            'vlans': VLAN.query.count(),
            'total_ips': IPAddress.query.count(),
            'assigned_ips': IPAddress.query.filter_by(status='assigned').count(),
            'available_ips': IPAddress.query.filter_by(status='available').count(),
            'quarantine_ips': IPAddress.query.filter_by(status='quarantine').count(),
            'reserved_ips': IPAddress.query.filter_by(status='reserved').count()
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Calculate utilization
    if stats['ipam']['total_ips'] > 0:
        stats['ipam']['utilization_percent'] = round(
            (stats['ipam']['assigned_ips'] / stats['ipam']['total_ips']) * 100, 1
        )
    else:
        stats['ipam']['utilization_percent'] = 0
    
    return jsonify(stats)

@app.route('/api/health')
def health_check():
    """
    Health check endpoint
    Used for monitoring application status
    """
    try:
        # Test database connection
        from models.datacenter import DataCenter
        DataCenter.query.first()
        db_status = 'healthy'
    except:
        db_status = 'unhealthy'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'database': db_status,
        'version': '1.3.0',
        'timestamp': datetime.utcnow().isoformat()
    })

# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ========== MAIN ENTRY POINT ==========

if __name__ == '__main__':
    # Development server configuration
    app.run(
        host='0.0.0.0',  # Allow external connections
        port=5000,
        debug=True
    )