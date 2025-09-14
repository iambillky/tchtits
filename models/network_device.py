"""
File: models/network_device.py
Purpose: Network equipment models for DCMS (simplified version)
Version: 1.1.0
Author: iambilky

Revision History:
- v1.0.0: Initial creation with simplified NetworkDevice model
- v1.1.0: Updated to reflect Core=Switch/Router terminology, added network_type field

Important Notes:
- TOR (Top of Rack) deployment - switches physically in the racks they serve
- INT[rack] = Private network TOR switch for that rack
- DISTRO[rack] = Public network TOR switch for that rack  
- Additional switches: INT10[rack][seq] (e.g., INT1051 = extra private switch in rack 5)
- CORE/PRIVCORE = Core switches/routers (not separate devices)
- Cross-connects exist: servers may connect to adjacent rack switches
- Private network: 10.10.x.x (INT switches)
- Public/Core network: 10.0.0.x and 208.76.x.x (DISTRO/CORE switches)
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from models.datacenter import db

# ========== MODEL DEFINITIONS ==========

class NetworkDevice(db.Model):
    """
    Network Device model
    Represents switches, routers, firewalls, etc.
    Keeps it simple - just track what matters
    """
    __tablename__ = 'network_devices'
    
    # ========== PRIMARY KEY ==========
    id = db.Column(db.Integer, primary_key=True)
    
    # ========== IDENTIFICATION ==========
    hostname = db.Column(db.String(100), unique=True, nullable=False)  # TCH-SFJ-INT5
    identifier = db.Column(db.String(50), nullable=False)  # INT5 (what you call it day-to-day)
    
    # ========== DEVICE TYPE ==========
    device_type = db.Column(db.String(50), nullable=False)  # Switch, Router, Firewall
    device_role = db.Column(db.String(50))  # Core, Distribution, Access
    network_type = db.Column(db.String(20), nullable=False)  # private or public - REQUIRED!
    
    # ========== HARDWARE INFO ==========
    manufacturer = db.Column(db.String(50))  # Cisco, Arista, etc.
    model = db.Column(db.String(100))  # Catalyst 2960, etc.
    serial_number = db.Column(db.String(100))
    
    # ========== SOFTWARE ==========
    software_version = db.Column(db.String(100))  # IOS version, etc.
    
    # ========== PHYSICAL LOCATION ==========
    rack_id = db.Column(db.Integer, db.ForeignKey('racks.id'), nullable=False)
    start_u = db.Column(db.Integer, nullable=False)  # Where in the rack
    size_u = db.Column(db.Integer, nullable=False, default=1)  # How many U it takes
    
    # ========== NETWORK INFO ==========
    management_ip = db.Column(db.String(45))  # 10.10.5.236
    port_count = db.Column(db.Integer)  # 24, 48, etc.
    
    # ========== POWER (SIMPLE DUAL PDU) ==========
    pdu_1_id = db.Column(db.Integer, db.ForeignKey('pdus.id'))
    pdu_1_outlet = db.Column(db.Integer)
    
    pdu_2_id = db.Column(db.Integer, db.ForeignKey('pdus.id'))  # Optional redundant
    pdu_2_outlet = db.Column(db.Integer)
    
    power_consumption = db.Column(db.Float)  # Watts
    
    # ========== STATUS ==========
    status = db.Column(db.String(20), default='active')  # active, spare, failed
    
    # ========== NOTES ==========
    notes = db.Column(db.Text)
    
    # ========== TIMESTAMPS ==========
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ========== RELATIONSHIPS ==========
    rack = db.relationship('Rack', backref='network_devices', foreign_keys=[rack_id])
    pdu_1 = db.relationship('PDU', foreign_keys=[pdu_1_id], backref='primary_power_devices')
    pdu_2 = db.relationship('PDU', foreign_keys=[pdu_2_id], backref='redundant_power_devices')
    
    # ========== PROPERTIES ==========
    @property
    def rack_position(self):
        """Return the rack position (e.g., U15 or U15-U16)"""
        if self.size_u == 1:
            return f"U{self.start_u}"
        else:
            return f"U{self.start_u}-U{self.start_u + self.size_u - 1}"
    
    @property
    def has_redundant_power(self):
        """Check if device has redundant power"""
        return self.pdu_1_id is not None and self.pdu_2_id is not None
    
    @property
    def is_primary_switch(self):
        """
        Check if this is a primary switch for a rack
        Primary switches have simple numbers (INT5, DISTRO5)
        Additional switches have 10xx numbers (INT1051)
        """
        # Extract number from identifier
        import re
        match = re.search(r'\d+', self.identifier)
        if match:
            number = int(match.group())
            return number < 1000  # Primary switches are < 1000
        return False
    
    def __repr__(self):
        return f'<NetworkDevice {self.identifier} ({self.hostname})>'


# ========== SIMPLE CHOICE LISTS ==========

DEVICE_TYPES = [
    ('Switch', 'Switch'),
    ('Core', 'Core Switch/Router'),  # Your "Core" devices
    ('Firewall', 'Firewall'),
    ('Load Balancer', 'Load Balancer'),
    ('Other', 'Other')
]

DEVICE_ROLES = [
    ('Core', 'Core Switch/Router'),      # CORE, PRIVCORE
    ('Distribution', 'Distribution'),     # DISTRO1, DISTRO2, etc.
    ('Access', 'Access/TOR'),            # INT5, INT1051 (top of rack)
    ('Management', 'Management'),
    ('Other', 'Other')
]

NETWORK_TYPES = [
    ('private', 'Private Network (INT)'),
    ('public', 'Public Network (DISTRO/CORE)')
]

DEVICE_STATUS = [
    ('active', 'Active'),
    ('spare', 'Spare'),
    ('failed', 'Failed'),
    ('maintenance', 'Maintenance')
]