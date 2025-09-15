"""
File: models/ipam.py
Purpose: IP Address Management (IPAM) database models
Created: 2025-01-14
Author: DCMS Team

Revision History:
- v1.0.0: Initial creation with core IPAM models
          Network, VLAN, IPRange, IPPool, IPAddress, IPHistory
          Complete tracking for all IP assignments with history
- v1.0.1: Fixed foreign key to reference 'datacenters.id' (the actual table name)
- v1.0.2: Added netmask field to IPRange model for complete network configuration
- v1.0.3: Simplified VLAN model, replaced complex fields with boolean flags
          Added colo_client_id and colo_client_name for client tracking

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
    
    # === Location ===
    datacenter_id = db.Column(db.Integer, db.ForeignKey('datacenters.id'))  # References datacenters table
    
    # === Network Properties ===
    description = db.Column(db.String(200))
    bgp_advertised = db.Column(db.Boolean, default=False)  # Is this advertised via BGP?
    is_public = db.Column(db.Boolean, default=True)  # Public or private network?
    
    # === Timestamps ===
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === Relationships ===
    datacenter = db.relationship('DataCenter', backref='networks')
    ip_ranges = db.relationship('IPRange', backref='network', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def total_ips(self):
        """Calculate total IPs across all ranges"""
        total = 0
        for ip_range in self.ip_ranges:
            total += ip_range.total_ips
        return total
    
    @property
    def available_count(self):
        """Count available IPs across all ranges"""
        count = 0
        for ip_range in self.ip_ranges:
            count += IPAddress.query.filter_by(
                ip_range_id=ip_range.id,
                status='available'
            ).count()
        return count
    
    @property
    def assigned_count(self):
        """Count assigned IPs across all ranges"""
        count = 0
        for ip_range in self.ip_ranges:
            count += IPAddress.query.filter_by(
                ip_range_id=ip_range.id,
                status='assigned'
            ).count()
        return count
    
    @property
    def utilization(self):
        """Calculate utilization percentage"""
        if self.total_ips == 0:
            return 0
        return round((self.assigned_count / self.total_ips) * 100, 1)

# ========== VLAN MODEL ==========

class VLAN(db.Model):
    """
    VLAN definitions as configured on switches.
    Maps to specific IP ranges and switch ports.
    
    Updated in v1.0.3 to simplify and add client tracking.
    """
    __tablename__ = 'vlans'
    
    # === Primary Key ===
    id = db.Column(db.Integer, primary_key=True)
    
    # === VLAN Definition ===
    vlan_number = db.Column(db.Integer, unique=True, nullable=False)  # 10, 201, etc.
    name = db.Column(db.String(100))  # "Vlan111", "Colo-Customer-A"
    description = db.Column(db.String(200))
    
    # === VRF Assignment (for private networks) ===
    vrf = db.Column(db.String(50))  # "private" for 10.x.x.x networks
    
    # === VLAN Type Flags (simplified in v1.0.3) ===
    is_private = db.Column(db.Boolean, default=False)  # 10.x.x.x network
    is_colo = db.Column(db.Boolean, default=False)  # Customer colocation VLAN
    is_vps = db.Column(db.Boolean, default=False)  # VPS pool VLAN
    
    # === Colocation Client Tracking (added in v1.0.3) ===
    colo_client_id = db.Column(db.Integer)  # Optional: Track which client owns this VLAN
    colo_client_name = db.Column(db.String(100))  # Optional: Client name for quick reference
    
    # === Timestamps ===
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === Relationships ===
    ip_ranges = db.relationship('IPRange', backref='vlan', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<VLAN {self.vlan_number}: {self.name}>'
    
    @property
    def total_ips(self):
        """Calculate total IPs in all ranges in this VLAN"""
        total = 0
        for ip_range in self.ip_ranges:
            start = ipaddress.ip_address(ip_range.start_ip)
            end = ipaddress.ip_address(ip_range.end_ip)
            total += int(end) - int(start) + 1
        return total

# ========== IP RANGE MODEL ==========

class IPRange(db.Model):
    """
    Specific IP ranges within a network.
    Example: 208.76.80.1 - 208.76.80.254 within 208.76.80.0/24
    
    This allows tracking usable ranges vs network/broadcast addresses.
    """
    __tablename__ = 'ip_ranges'
    
    # === Primary Key ===
    id = db.Column(db.Integer, primary_key=True)
    
    # === Range Definition ===
    start_ip = db.Column(db.String(15), nullable=False)  # "208.76.80.1"
    end_ip = db.Column(db.String(15), nullable=False)    # "208.76.80.254"
    
    # === Parent References ===
    network_id = db.Column(db.Integer, db.ForeignKey('networks.id'), nullable=False)
    vlan_id = db.Column(db.Integer, db.ForeignKey('vlans.id'))
    
    # === Range Properties ===
    range_type = db.Column(db.String(20))  # 'primary', 'secondary', 'addon'
    status = db.Column(db.String(20), default='active')  # See IP_RANGE_STATUS
    description = db.Column(db.String(200))
    
    # === Gateway Configuration ===
    gateway_ip = db.Column(db.String(15))  # "208.76.80.1" - never assignable
    netmask = db.Column(db.String(15))  # "255.255.255.0" - Added in v1.0.2
    
    # === Timestamps ===
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === Relationships ===
    ip_addresses = db.relationship('IPAddress', backref='ip_range', lazy='dynamic', cascade='all, delete-orphan')
    
    # === Constraints ===
    __table_args__ = (
        UniqueConstraint('start_ip', 'end_ip', name='_range_uc'),
        Index('ix_ip_range_network', 'network_id'),
        Index('ix_ip_range_vlan', 'vlan_id'),
    )
    
    @property
    def total_ips(self):
        """Calculate total IPs in range"""
        start = ipaddress.ip_address(self.start_ip)
        end = ipaddress.ip_address(self.end_ip)
        return int(end) - int(start) + 1
    
    @validates('start_ip', 'end_ip')
    def validate_ip(self, key, value):
        """Validate IP address format"""
        try:
            ipaddress.ip_address(value)
        except ValueError:
            raise ValueError(f"Invalid IP address: {value}")
        return value
    
    def populate_ips(self):
        """
        Generate all IP addresses in this range.
        Called when range is created to pre-populate IP table.
        """
        start = ipaddress.ip_address(self.start_ip)
        end = ipaddress.ip_address(self.end_ip)
        
        ips_to_create = []
        current = start
        
        while current <= end:
            ip_str = str(current)
            
            # Check if IP already exists
            existing = IPAddress.query.filter_by(address=ip_str).first()
            if not existing:
                # Determine initial status
                if ip_str == self.gateway_ip:
                    status = 'gateway'
                elif current == start and start.packed[-1] == 0:
                    status = 'network'
                elif current == end and end.packed[-1] == 255:
                    status = 'broadcast'
                else:
                    status = 'available'
                
                ip = IPAddress(
                    address=ip_str,
                    ip_range_id=self.id,
                    status=status
                )
                ips_to_create.append(ip)
            
            current = ipaddress.ip_address(int(current) + 1)
        
        # Bulk insert
        if ips_to_create:
            db.session.bulk_save_objects(ips_to_create)
            db.session.commit()

# ========== IP POOL MODEL ==========

class IPPool(db.Model):
    """
    Pools of IPs for specific purposes (e.g., VPS allocations).
    Allows grouping IPs for automatic assignment.
    """
    __tablename__ = 'ip_pools'
    
    # === Primary Key ===
    id = db.Column(db.Integer, primary_key=True)
    
    # === Pool Definition ===
    name = db.Column(db.String(100), unique=True, nullable=False)  # "VPS Public Pool"
    pool_type = db.Column(db.String(20))  # 'vps', 'addon', 'management'
    
    # === Pool Properties ===
    auto_assign = db.Column(db.Boolean, default=False)  # Allow automatic assignment?
    max_per_device = db.Column(db.Integer)  # Max IPs per device from this pool
    
    # === Hypervisor Association (for VPS pools) ===
    hypervisor_id = db.Column(db.Integer)  # Server ID of hypervisor
    
    # === Timestamps ===
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === Relationships ===
    ip_addresses = db.relationship('IPAddress', backref='ip_pool', lazy='dynamic')

# ========== IP ADDRESS MODEL ==========

class IPAddress(db.Model):
    """
    Individual IP address tracking.
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
    history = db.relationship('IPHistory', backref='ip_address', lazy='dynamic', cascade='all, delete-orphan')
    
    # === Indexes ===
    __table_args__ = (
        Index('ix_ip_assignment', 'assigned_to_type', 'assigned_to_id'),
        Index('ix_ip_status', 'status'),
        Index('ix_ip_quarantine', 'quarantine_until'),
    )
    
    def assign(self, device_type, device_id, user=None, is_primary=False, connection_type='public'):
        """
        Assign this IP to a device.
        Creates history record automatically.
        """
        if self.status == 'assigned':
            raise ValueError(f"IP {self.address} is already assigned!")
        
        if self.status in ['gateway', 'network', 'broadcast']:
            raise ValueError(f"IP {self.address} cannot be assigned (status: {self.status})")
        
        # Set assignment
        self.status = 'assigned'
        self.assigned_to_type = device_type
        self.assigned_to_id = device_id
        self.assignment_date = datetime.utcnow()
        self.assigned_by = user or 'system'
        self.is_primary = is_primary
        self.connection_type = connection_type
        
        # Clear quarantine if applicable
        self.quarantine_until = None
        
        # Create history record
        history = IPHistory(
            ip_address_id=self.id,
            action='assign',
            performed_by=user or 'system',
            assigned_to_type=device_type,
            assigned_to_id=device_id,
            details=f"Assigned as {connection_type} {'primary' if is_primary else 'addon'} IP"
        )
        db.session.add(history)
    
    def release(self, user=None):
        """
        Release this IP from assignment.
        Puts it in 90-day quarantine.
        """
        if self.status != 'assigned':
            raise ValueError(f"IP {self.address} is not assigned!")
        
        # Store previous assignment for history
        prev_type = self.assigned_to_type
        prev_id = self.assigned_to_id
        
        # Release IP
        self.status = 'quarantine'
        self.assigned_to_type = None
        self.assigned_to_id = None
        self.assignment_date = None
        self.assigned_by = None
        self.is_primary = False
        
        # Set quarantine
        self.release_date = datetime.utcnow()
        self.released_by = user or 'system'
        self.quarantine_until = datetime.utcnow() + timedelta(days=90)
        
        # Clear interface info
        self.mac_address = None
        self.interface_name = None
        
        # Create history record
        history = IPHistory(
            ip_address_id=self.id,
            action='release',
            performed_by=user or 'system',
            assigned_to_type=prev_type,
            assigned_to_id=prev_id,
            details=f"Released from {prev_type} #{prev_id}, quarantine until {self.quarantine_until.strftime('%Y-%m-%d')}"
        )
        db.session.add(history)
    
    def reserve(self, reason, user=None):
        """Reserve this IP for specific purpose"""
        if self.status == 'assigned':
            raise ValueError(f"IP {self.address} is already assigned!")
        
        self.status = 'reserved'
        self.notes = reason
        
        # Create history record
        history = IPHistory(
            ip_address_id=self.id,
            action='reserve',
            performed_by=user or 'system',
            details=f"Reserved: {reason}"
        )
        db.session.add(history)

# ========== IP HISTORY MODEL ==========

class IPHistory(db.Model):
    """
    Complete audit trail of all IP operations.
    Never delete records from this table!
    """
    __tablename__ = 'ip_history'
    
    # === Primary Key ===
    id = db.Column(db.Integer, primary_key=True)
    
    # === IP Reference ===
    ip_address_id = db.Column(db.Integer, db.ForeignKey('ip_addresses.id'), nullable=False)
    
    # === Action Details ===
    action = db.Column(db.String(20), nullable=False)  # 'assign', 'release', 'reserve', 'quarantine_end'
    performed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    performed_by = db.Column(db.String(100))  # Username
    
    # === Assignment Details (if applicable) ===
    assigned_to_type = db.Column(db.String(20))
    assigned_to_id = db.Column(db.Integer)
    
    # === Additional Info ===
    details = db.Column(db.Text)  # JSON or text description
    
    # === Indexes ===
    __table_args__ = (
        Index('ix_history_ip', 'ip_address_id'),
        Index('ix_history_date', 'performed_at'),
        Index('ix_history_assignment', 'assigned_to_type', 'assigned_to_id'),
    )

# ========== UTILITY FUNCTIONS ==========

def check_duplicate_ip(ip_address):
    """
    Check if an IP is already assigned.
    This is THE critical function for preventing duplicates!
    
    Returns the IPAddress object if found, None if available.
    """
    return IPAddress.query.filter_by(
        address=ip_address,
        status='assigned'
    ).first()

def suggest_next_available_ip(network_id=None, vlan_id=None, pool_id=None):
    """
    Suggest the next available IP for assignment.
    Replaces the old "ping and pray" method!
    
    Priority:
    1. From specific pool if specified
    2. From VLAN ranges if specified
    3. From network ranges if specified
    4. Any available IP (danger!)
    """
    query = IPAddress.query.filter_by(status='available')
    
    if pool_id:
        query = query.filter_by(ip_pool_id=pool_id)
    elif vlan_id:
        ranges = IPRange.query.filter_by(vlan_id=vlan_id).all()
        range_ids = [r.id for r in ranges]
        query = query.filter(IPAddress.ip_range_id.in_(range_ids))
    elif network_id:
        ranges = IPRange.query.filter_by(network_id=network_id).all()
        range_ids = [r.id for r in ranges]
        query = query.filter(IPAddress.ip_range_id.in_(range_ids))
    
    # Get first available
    return query.order_by(IPAddress.address).first()

def process_quarantine_expirations():
    """
    Process expired quarantines.
    Run this daily via cron/scheduler.
    """
    expired = IPAddress.query.filter(
        IPAddress.status == 'quarantine',
        IPAddress.quarantine_until <= datetime.utcnow()
    ).all()
    
    for ip in expired:
        ip.status = 'available'
        ip.quarantine_until = None
        ip.release_date = None
        ip.released_by = None
        
        # Create history record
        history = IPHistory(
            ip_address_id=ip.id,
            action='quarantine_end',
            performed_by='system',
            details='Quarantine period expired, IP now available'
        )
        db.session.add(history)
    
    if expired:
        db.session.commit()
    
    return len(expired)

# ========== EVENT LISTENERS ==========

@event.listens_for(IPRange, 'after_insert')
def create_ip_addresses(mapper, connection, target):
    """
    Automatically populate IP addresses when a range is created.
    This happens in the background after commit.
    """
    # Note: This is called within the transaction, so we can't
    # call populate_ips() directly. Instead, flag it for later.
    target._needs_population = True

@event.listens_for(db.session, 'after_commit')
def populate_ranges(session):
    """
    After commit, populate any IP ranges that need it.
    """
    for obj in session.identity_map.values():
        if isinstance(obj, IPRange) and hasattr(obj, '_needs_population'):
            obj.populate_ips()
            delattr(obj, '_needs_population')