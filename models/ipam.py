"""
File: models/ipam.py
Purpose: IP Address Management (IPAM) database models
Created: 2025-01-14
Author: DCMS Team

Revision History:
- 2025-01-14: Initial creation with core IPAM models
             Network, VLAN, IPRange, IPPool, IPAddress, IPHistory
             Complete tracking for all IP assignments with history

This module implements the PRIMARY REQUIREMENT from README.md:
"Complete IP Address Management (IPAM) with zero exceptions"
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, Index, event
from sqlalchemy.orm import validates
import ipaddress
import json

# Use the existing db instance from datacenter module
from models.datacenter import db

# ========== ENUM DEFINITIONS ==========

IP_STATUS = {
    'available': 'Available for assignment',
    'assigned': 'Currently assigned to a device',
    'reserved': 'Reserved for specific purpose',
    'quarantine': 'In 90-day quarantine after release',
    'gateway': 'Gateway IP - never assign',
    'network': 'Network address - never assign',
    'broadcast': 'Broadcast address - never assign'
}

ASSIGNMENT_TYPES = {
    'server': 'Physical server',
    'vps': 'Virtual Private Server',
    'hypervisor': 'VPS Hypervisor',
    'switch': 'Network switch',
    'router': 'Router',
    'firewall': 'Firewall',
    'pdu': 'Power Distribution Unit',
    'ipmi': 'IPMI/Management interface',
    'other': 'Other device'
}

IP_RANGE_STATUS = {
    'active': 'Active and available for use',
    'reserved': 'Reserved for future use',
    'deprecated': 'Being phased out',
    'not_in_use': 'Not currently in use'
}

# ========== NETWORK MODEL ==========

class Network(db.Model):
    """
    Parent network blocks as advertised via BGP or defined in core switch.
    Examples: 208.76.80.0/24, 198.38.76.0/22
    
    These are the top-level network definitions that contain IP ranges.
    """
    __tablename__ = 'networks'
    
    # === Primary Key ===
    id = db.Column(db.Integer, primary_key=True)
    
    # === Network Definition ===
    network = db.Column(db.String(18), unique=True, nullable=False)  # "208.76.80.0/24"
    cidr = db.Column(db.Integer, nullable=False)  # 24, 22, etc.
    ip_version = db.Column(db.Integer, default=4)  # 4 for IPv4, 6 for IPv6
    
    # === Network Info ===
    description = db.Column(db.Text)
    datacenter_id = db.Column(db.Integer, db.ForeignKey('data_center.id'))
    bgp_advertised = db.Column(db.Boolean, default=False)
    
    # === Timestamps ===
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === Relationships ===
    ip_ranges = db.relationship('IPRange', backref='network', lazy='dynamic', cascade='all, delete-orphan')
    datacenter = db.relationship('DataCenter', backref='networks')
    
    def __repr__(self):
        return f'<Network {self.network}>'
    
    @property
    def total_ips(self):
        """Calculate total IPs in this network"""
        try:
            net = ipaddress.ip_network(self.network)
            return net.num_addresses
        except:
            return 0
    
    @property
    def utilization(self):
        """Calculate network utilization percentage"""
        # Will be implemented to check all IP addresses
        pass

# ========== VLAN MODEL ==========

class VLAN(db.Model):
    """
    VLANs from core switch configuration.
    Tracks VLAN to IP range mappings.
    
    Note: Some VLANs have multiple IP ranges (primary and secondary IPs)
    Example: VLAN 111 has three different IP ranges
    """
    __tablename__ = 'vlans'
    
    # === Primary Key ===
    id = db.Column(db.Integer, primary_key=True)
    
    # === VLAN Definition ===
    vlan_number = db.Column(db.Integer, unique=True, nullable=False)  # 111, 2, 3, etc.
    name = db.Column(db.String(50))  # "Vlan111", "Vlan2"
    description = db.Column(db.Text)
    
    # === VRF Support ===
    vrf = db.Column(db.String(50))  # "private" for private network VLANs
    
    # === Special Flags ===
    is_private = db.Column(db.Boolean, default=False)  # For 10.x.x.x networks
    is_colo = db.Column(db.Boolean, default=False)  # For customer colo VLANs
    is_vps = db.Column(db.Boolean, default=False)  # For VPS pool VLANs
    
    # === Timestamps ===
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === Relationships ===
    ip_ranges = db.relationship('IPRange', backref='vlan', lazy='dynamic')
    ip_pools = db.relationship('IPPool', backref='vlan', lazy='dynamic')
    
    def __repr__(self):
        return f'<VLAN {self.vlan_number}: {self.name}>'

# ========== IP RANGE MODEL ==========

class IPRange(db.Model):
    """
    Actual usable IP ranges within networks.
    Maps to VLAN interfaces on core switch.
    
    Example: 208.76.80.4-126 on VLAN 111 with gateway 208.76.80.3
    """
    __tablename__ = 'ip_ranges'
    
    # === Primary Key ===
    id = db.Column(db.Integer, primary_key=True)
    
    # === Parent References ===
    network_id = db.Column(db.Integer, db.ForeignKey('networks.id'), nullable=False)
    vlan_id = db.Column(db.Integer, db.ForeignKey('vlans.id'))
    
    # === Range Definition ===
    start_ip = db.Column(db.String(15), nullable=False)  # "208.76.80.4"
    end_ip = db.Column(db.String(15), nullable=False)  # "208.76.80.126"
    gateway = db.Column(db.String(15))  # "208.76.80.3"
    netmask = db.Column(db.String(15))  # "255.255.255.128"
    
    # === Range Type ===
    range_type = db.Column(db.String(20), default='primary')  # 'primary', 'secondary'
    status = db.Column(db.String(20), default='active')  # See IP_RANGE_STATUS
    
    # === Metadata ===
    description = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # === Timestamps ===
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === Relationships ===
    ip_addresses = db.relationship('IPAddress', backref='ip_range', lazy='dynamic')
    
    # === Constraints ===
    __table_args__ = (
        UniqueConstraint('start_ip', 'end_ip', name='_range_uc'),
        Index('idx_range_ips', 'start_ip', 'end_ip'),
    )
    
    def __repr__(self):
        return f'<IPRange {self.start_ip}-{self.end_ip}>'
    
    @property
    def size(self):
        """Calculate number of IPs in range"""
        try:
            start = ipaddress.ip_address(self.start_ip)
            end = ipaddress.ip_address(self.end_ip)
            return int(end) - int(start) + 1
        except:
            return 0

# ========== IP POOL MODEL (VPS) ==========

class IPPool(db.Model):
    """
    IP pools for VPS hypervisors and other grouped allocations.
    Maps hypervisors to their assigned IP ranges.
    
    Example: 'vps14' pool uses IPs from VLAN 17
    """
    __tablename__ = 'ip_pools'
    
    # === Primary Key ===
    id = db.Column(db.Integer, primary_key=True)
    
    # === Pool Definition ===
    name = db.Column(db.String(50), unique=True, nullable=False)  # 'vps14', 'vps8/9/10/11'
    pool_type = db.Column(db.String(20), default='vps')  # 'vps', 'dedicated', 'infrastructure'
    
    # === VLAN Association ===
    vlan_id = db.Column(db.Integer, db.ForeignKey('vlans.id'))
    
    # === Hypervisor Tracking ===
    # JSON array of server IDs that are hypervisors using this pool
    hypervisor_ids = db.Column(db.Text)  # JSON: [14] or [8,9,10,11]
    
    # === Pool Settings ===
    is_active = db.Column(db.Boolean, default=True)
    auto_assign = db.Column(db.Boolean, default=False)  # Allow automatic assignment
    
    # === Metadata ===
    description = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # === Timestamps ===
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === Relationships ===
    ip_addresses = db.relationship('IPAddress', backref='ip_pool', lazy='dynamic')
    
    def __repr__(self):
        return f'<IPPool {self.name}>'
    
    @property
    def hypervisor_list(self):
        """Get list of hypervisor IDs"""
        if self.hypervisor_ids:
            try:
                return json.loads(self.hypervisor_ids)
            except:
                return []
        return []
    
    @property
    def utilization(self):
        """Calculate pool utilization percentage"""
        total = self.ip_addresses.count()
        if total == 0:
            return 0
        assigned = self.ip_addresses.filter_by(status='assigned').count()
        return (assigned / total) * 100

# ========== IP ADDRESS MODEL ==========

class IPAddress(db.Model):
    """
    Every single IP address in the system.
    This is the core table that prevents duplicates and tracks all assignments.
    
    CRITICAL: No IP can ever be assigned twice!
    """
    __tablename__ = 'ip_addresses'
    
    # === Primary Key ===
    id = db.Column(db.Integer, primary_key=True)
    
    # === IP Address ===
    address = db.Column(db.String(15), unique=True, nullable=False, index=True)  # "208.76.80.5"
    ip_version = db.Column(db.Integer, default=4)  # 4 or 6
    
    # === Parent References ===
    ip_range_id = db.Column(db.Integer, db.ForeignKey('ip_ranges.id'))
    ip_pool_id = db.Column(db.Integer, db.ForeignKey('ip_pools.id'))
    
    # === Status Tracking ===
    status = db.Column(db.String(20), default='available', nullable=False)  # See IP_STATUS
    
    # === Assignment Information ===
    assigned_to_type = db.Column(db.String(20))  # See ASSIGNMENT_TYPES
    assigned_to_id = db.Column(db.Integer)  # ID of the device
    assignment_date = db.Column(db.DateTime)
    assigned_by = db.Column(db.String(100))  # Username who assigned
    
    # === Release & Quarantine ===
    release_date = db.Column(db.DateTime)
    released_by = db.Column(db.String(100))  # Username who released
    quarantine_until = db.Column(db.DateTime)  # 90 days after release
    
    # === VPS Specific Fields ===
    vps_hostname = db.Column(db.String(255))  # 'wasatch.aaronoz.com'
    hypervisor_id = db.Column(db.Integer)  # Server ID of hypervisor
    
    # === Network Interface Info ===
    mac_address = db.Column(db.String(17))  # "00:11:22:33:44:55"
    interface_name = db.Column(db.String(50))  # 'eth0', 'bond0', 'eno1'
    interface_speed = db.Column(db.String(20))  # '1Gbps', '10Gbps'
    
    # === DNS Records ===
    ptr_record = db.Column(db.String(255))  # Reverse DNS
    a_records = db.Column(db.Text)  # JSON array of A records
    
    # === Connection Type ===
    is_primary = db.Column(db.Boolean, default=False)  # Primary IP for device
    connection_type = db.Column(db.String(20))  # 'public', 'private', 'ipmi'
    
    # === Monitoring ===
    last_ping = db.Column(db.DateTime)
    last_ping_status = db.Column(db.Boolean)
    
    # === Metadata ===
    notes = db.Column(db.Text)
    
    # === Timestamps ===
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === Relationships ===
    history = db.relationship('IPHistory', backref='ip_address', lazy='dynamic', 
                             cascade='all, delete-orphan', order_by='IPHistory.performed_at.desc()')
    
    # === Indexes for Performance ===
    __table_args__ = (
        Index('idx_ip_status', 'status'),
        Index('idx_ip_assignment', 'assigned_to_type', 'assigned_to_id'),
        Index('idx_ip_pool', 'ip_pool_id', 'status'),
        Index('idx_ip_quarantine', 'quarantine_until'),
    )
    
    def __repr__(self):
        return f'<IPAddress {self.address}: {self.status}>'
    
    @validates('address')
    def validate_address(self, key, address):
        """Validate IP address format"""
        try:
            ipaddress.ip_address(address)
        except ValueError:
            raise ValueError(f"Invalid IP address: {address}")
        return address
    
    def assign(self, device_type, device_id, user=None, **kwargs):
        """
        Assign this IP to a device.
        Prevents duplicate assignments.
        """
        if self.status == 'assigned':
            raise ValueError(f"IP {self.address} is already assigned!")
        
        if self.status == 'quarantine' and datetime.utcnow() < self.quarantine_until:
            remaining = (self.quarantine_until - datetime.utcnow()).days
            raise ValueError(f"IP {self.address} is in quarantine for {remaining} more days!")
        
        self.status = 'assigned'
        self.assigned_to_type = device_type
        self.assigned_to_id = device_id
        self.assignment_date = datetime.utcnow()
        self.assigned_by = user
        
        # Set additional fields from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Record in history
        history = IPHistory(
            ip_address_id=self.id,
            action='assigned',
            assigned_to_type=device_type,
            assigned_to_id=device_id,
            performed_by=user,
            performed_at=datetime.utcnow()
        )
        db.session.add(history)
        
        return True
    
    def release(self, user=None, skip_quarantine=False):
        """
        Release this IP and start 90-day quarantine.
        """
        if self.status != 'assigned':
            raise ValueError(f"IP {self.address} is not currently assigned!")
        
        # Store previous assignment for history
        prev_type = self.assigned_to_type
        prev_id = self.assigned_to_id
        
        # Clear assignment
        self.assigned_to_type = None
        self.assigned_to_id = None
        self.assignment_date = None
        self.release_date = datetime.utcnow()
        self.released_by = user
        
        # Clear additional fields
        self.vps_hostname = None
        self.hypervisor_id = None
        self.mac_address = None
        self.interface_name = None
        self.is_primary = False
        
        # Set quarantine (90 days)
        if not skip_quarantine:
            self.status = 'quarantine'
            self.quarantine_until = datetime.utcnow() + timedelta(days=90)
        else:
            self.status = 'available'
            self.quarantine_until = None
        
        # Record in history
        history = IPHistory(
            ip_address_id=self.id,
            action='released',
            assigned_to_type=prev_type,
            assigned_to_id=prev_id,
            performed_by=user,
            performed_at=datetime.utcnow(),
            notes=f"Quarantine until {self.quarantine_until}" if not skip_quarantine else "No quarantine"
        )
        db.session.add(history)
        
        return True

# ========== IP HISTORY MODEL ==========

class IPHistory(db.Model):
    """
    Complete audit trail of all IP assignments and releases.
    Never delete history records!
    """
    __tablename__ = 'ip_history'
    
    # === Primary Key ===
    id = db.Column(db.Integer, primary_key=True)
    
    # === IP Reference ===
    ip_address_id = db.Column(db.Integer, db.ForeignKey('ip_addresses.id'), nullable=False)
    
    # === Action Tracking ===
    action = db.Column(db.String(20), nullable=False)  # 'assigned', 'released', 'quarantined', 'reserved'
    
    # === Assignment Info ===
    assigned_to_type = db.Column(db.String(20))  # What type of device
    assigned_to_id = db.Column(db.Integer)  # Device ID
    
    # === Who and When ===
    performed_by = db.Column(db.String(100))  # User who performed action
    performed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # === Additional Info ===
    notes = db.Column(db.Text)
    extra_data = db.Column(db.Text)  # JSON for any additional data
    
    # === Indexes ===
    __table_args__ = (
        Index('idx_history_ip', 'ip_address_id'),
        Index('idx_history_date', 'performed_at'),
        Index('idx_history_device', 'assigned_to_type', 'assigned_to_id'),
    )
    
    def __repr__(self):
        return f'<IPHistory {self.action} at {self.performed_at}>'

# ========== DATABASE EVENTS ==========

@event.listens_for(IPAddress, 'before_update')
def ip_check_quarantine(mapper, connection, target):
    """
    Automatically clear quarantine status when time expires.
    """
    if target.status == 'quarantine' and target.quarantine_until:
        if datetime.utcnow() >= target.quarantine_until:
            target.status = 'available'
            target.quarantine_until = None
            
            # Add history record
            history = IPHistory(
                ip_address_id=target.id,
                action='quarantine_expired',
                performed_at=datetime.utcnow(),
                notes='Quarantine period completed'
            )
            db.session.add(history)

# ========== UTILITY FUNCTIONS ==========

def process_quarantine_expirations():
    """
    Batch process to clear expired quarantines.
    Should be run daily via cron/scheduler.
    """
    expired = IPAddress.query.filter(
        IPAddress.status == 'quarantine',
        IPAddress.quarantine_until <= datetime.utcnow()
    ).all()
    
    for ip in expired:
        ip.status = 'available'
        ip.quarantine_until = None
        
        history = IPHistory(
            ip_address_id=ip.id,
            action='quarantine_expired',
            performed_at=datetime.utcnow(),
            notes='Quarantine period completed (batch process)'
        )
        db.session.add(history)
    
    db.session.commit()
    return len(expired)

def check_duplicate_ip(address, exclude_id=None):
    """
    Check if an IP address already exists in the system.
    This is the CRITICAL function that prevents duplicates!
    
    Args:
        address: IP address to check
        exclude_id: IP record ID to exclude (for updates)
    
    Returns:
        IPAddress object if duplicate found, None otherwise
    """
    query = IPAddress.query.filter_by(address=address)
    if exclude_id:
        query = query.filter(IPAddress.id != exclude_id)
    
    return query.first()

def suggest_next_available_ip(vlan_id=None, pool_id=None, connection_type='public'):
    """
    Find the next available IP address.
    This replaces the "ping and pray" method!
    
    Args:
        vlan_id: Specific VLAN to search in
        pool_id: Specific pool for VPS assignments
        connection_type: 'public' or 'private'
    
    Returns:
        IPAddress object or None
    """
    query = IPAddress.query.filter_by(status='available')
    
    if pool_id:
        query = query.filter_by(ip_pool_id=pool_id)
    elif vlan_id:
        # Get IP ranges for this VLAN
        ranges = IPRange.query.filter_by(vlan_id=vlan_id).all()
        range_ids = [r.id for r in ranges]
        query = query.filter(IPAddress.ip_range_id.in_(range_ids))
    elif connection_type == 'private':
        # Private network (10.10.4.0/22) - wild west!
        query = query.filter(IPAddress.address.like('10.10.%'))
    
    # Get first available
    return query.first()

# ========== END OF IPAM MODELS ==========