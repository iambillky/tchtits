"""
File: routes/network_devices.py
Purpose: Route handlers for network device management
Version: 1.0.0
Author: iambilky

Revision History:
- v1.0.0: Initial creation with CRUD operations for network devices
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.network_device import db, NetworkDevice, DEVICE_TYPES, DEVICE_ROLES, NETWORK_TYPES, DEVICE_STATUS
from models.datacenter import Rack, PDU
from forms.network_device_forms import NetworkDeviceForm
from sqlalchemy import and_

# ========== BLUEPRINT INITIALIZATION ==========

network_devices_bp = Blueprint('network_devices', __name__, url_prefix='/network-devices')

# ========== MAIN VIEWS ==========

@network_devices_bp.route('/')
def index():
    """
    Main network device view
    Shows all network devices organized by type and location
    """
    # Get filter parameters
    network_type = request.args.get('network_type', 'all')
    device_type = request.args.get('device_type', 'all')
    rack_id = request.args.get('rack', 'all')
    
    # Build query
    query = NetworkDevice.query
    
    if network_type != 'all':
        query = query.filter_by(network_type=network_type)
    if device_type != 'all':
        query = query.filter_by(device_type=device_type)
    if rack_id != 'all':
        query = query.filter_by(rack_id=int(rack_id))
    
    # Get devices
    devices = query.order_by(NetworkDevice.identifier).all()
    
    # Get all racks for filter dropdown
    racks = Rack.query.order_by(Rack.rack_id).all()
    
    # Calculate summary statistics
    total_devices = NetworkDevice.query.count()
    private_count = NetworkDevice.query.filter_by(network_type='private').count()
    public_count = NetworkDevice.query.filter_by(network_type='public').count()
    active_count = NetworkDevice.query.filter_by(status='active').count()
    
    # Group devices by rack for visualization
    devices_by_rack = {}
    for device in devices:
        if device.rack.rack_id not in devices_by_rack:
            devices_by_rack[device.rack.rack_id] = []
        devices_by_rack[device.rack.rack_id].append(device)
    
    return render_template('network_devices/index.html',
                         devices=devices,
                         devices_by_rack=devices_by_rack,
                         racks=racks,
                         total_devices=total_devices,
                         private_count=private_count,
                         public_count=public_count,
                         active_count=active_count,
                         current_filters={
                             'network_type': network_type,
                             'device_type': device_type,
                             'rack': rack_id
                         })

# ========== CREATE OPERATIONS ==========

@network_devices_bp.route('/add', methods=['GET', 'POST'])
def add_device():
    """Add new network device"""
    form = NetworkDeviceForm()
    
    # Populate rack choices
    racks = Rack.query.order_by(Rack.rack_id).all()
    form.rack_id.choices = [(0, '-- Select Rack --')] + [
        (rack.id, f"{rack.rack_id} ({rack.u_available}U available)") 
        for rack in racks
    ]
    
    # Populate PDU choices (if PDUs exist)
    pdus = PDU.query.join(Rack).order_by(Rack.rack_id, PDU.identifier).all()
    pdu_choices = [(0, '-- No PDU --')] + [
        (pdu.id, f"{pdu.rack.rack_id} - {pdu.identifier} ({pdu.available_outlets} outlets free)")
        for pdu in pdus
    ]
    form.pdu_1_id.choices = pdu_choices
    form.pdu_2_id.choices = pdu_choices
    
    if form.validate_on_submit():
        # Check if hostname already exists
        existing = NetworkDevice.query.filter_by(hostname=form.hostname.data.upper()).first()
        if existing:
            flash(f'Device with hostname {form.hostname.data.upper()} already exists!', 'error')
            return render_template('network_devices/add_device.html', form=form)
        
        # Check if rack space is available
        rack = Rack.query.get(form.rack_id.data)
        if not validate_rack_space(rack, form.start_u.data, form.size_u.data):
            flash(f'Rack space U{form.start_u.data}-U{form.start_u.data + form.size_u.data - 1} is not available!', 'error')
            return render_template('network_devices/add_device.html', form=form)
        
        # Create new device
        device = NetworkDevice(
            hostname=form.hostname.data.upper(),
            identifier=form.identifier.data.upper(),
            device_type=form.device_type.data,
            device_role=form.device_role.data,
            network_type=form.network_type.data,
            manufacturer=form.manufacturer.data,
            model=form.model.data,
            serial_number=form.serial_number.data,
            software_version=form.software_version.data,
            rack_id=form.rack_id.data,
            start_u=form.start_u.data,
            size_u=form.size_u.data,
            management_ip=form.management_ip.data,
            port_count=form.port_count.data,
            pdu_1_id=form.pdu_1_id.data if form.pdu_1_id.data != 0 else None,
            pdu_1_outlet=form.pdu_1_outlet.data,
            pdu_2_id=form.pdu_2_id.data if form.pdu_2_id.data != 0 else None,
            pdu_2_outlet=form.pdu_2_outlet.data,
            power_consumption=form.power_consumption.data,
            status=form.status.data,
            notes=form.notes.data
        )
        
        # Update rack usage
        rack.u_used += device.size_u
        
        # Update PDU outlet usage if configured
        if device.pdu_1_id:
            pdu1 = PDU.query.get(device.pdu_1_id)
            pdu1.used_outlets += 1
        if device.pdu_2_id:
            pdu2 = PDU.query.get(device.pdu_2_id)
            pdu2.used_outlets += 1
        
        db.session.add(device)
        db.session.commit()
        
        flash(f'Network device {device.identifier} added successfully!', 'success')
        return redirect(url_for('network_devices.index'))
    
    return render_template('network_devices/add_device.html', form=form)

# ========== UPDATE OPERATIONS ==========

@network_devices_bp.route('/edit/<int:device_id>', methods=['GET', 'POST'])
def edit_device(device_id):
    """Edit network device"""
    device = NetworkDevice.query.get_or_404(device_id)
    form = NetworkDeviceForm(obj=device)
    
    # Store original values for comparison
    original_rack_id = device.rack_id
    original_start_u = device.start_u
    original_size_u = device.size_u
    original_pdu_1_id = device.pdu_1_id
    original_pdu_2_id = device.pdu_2_id
    
    # Populate rack choices
    racks = Rack.query.order_by(Rack.rack_id).all()
    form.rack_id.choices = [(rack.id, f"{rack.rack_id} ({rack.u_available}U available)") 
                            for rack in racks]
    
    # Populate PDU choices
    pdus = PDU.query.join(Rack).order_by(Rack.rack_id, PDU.identifier).all()
    pdu_choices = [(0, '-- No PDU --')] + [
        (pdu.id, f"{pdu.rack.rack_id} - {pdu.identifier} ({pdu.available_outlets} outlets free)")
        for pdu in pdus
    ]
    form.pdu_1_id.choices = pdu_choices
    form.pdu_2_id.choices = pdu_choices
    
    if form.validate_on_submit():
        # Check if hostname changed and already exists
        if form.hostname.data.upper() != device.hostname:
            existing = NetworkDevice.query.filter_by(hostname=form.hostname.data.upper()).first()
            if existing:
                flash(f'Device with hostname {form.hostname.data.upper()} already exists!', 'error')
                return render_template('network_devices/edit_device.html', form=form, device=device)
        
        # Check rack space if position changed
        if (form.rack_id.data != original_rack_id or 
            form.start_u.data != original_start_u or 
            form.size_u.data != original_size_u):
            
            rack = Rack.query.get(form.rack_id.data)
            if not validate_rack_space(rack, form.start_u.data, form.size_u.data, exclude_device_id=device_id):
                flash(f'Rack space U{form.start_u.data}-U{form.start_u.data + form.size_u.data - 1} is not available!', 'error')
                return render_template('network_devices/edit_device.html', form=form, device=device)
            
            # Update rack usage
            old_rack = Rack.query.get(original_rack_id)
            old_rack.u_used -= original_size_u
            rack.u_used += form.size_u.data
        
        # Update PDU outlet usage if changed
        if form.pdu_1_id.data != original_pdu_1_id:
            if original_pdu_1_id:
                old_pdu = PDU.query.get(original_pdu_1_id)
                old_pdu.used_outlets -= 1
            if form.pdu_1_id.data and form.pdu_1_id.data != 0:
                new_pdu = PDU.query.get(form.pdu_1_id.data)
                new_pdu.used_outlets += 1
        
        if form.pdu_2_id.data != original_pdu_2_id:
            if original_pdu_2_id:
                old_pdu = PDU.query.get(original_pdu_2_id)
                old_pdu.used_outlets -= 1
            if form.pdu_2_id.data and form.pdu_2_id.data != 0:
                new_pdu = PDU.query.get(form.pdu_2_id.data)
                new_pdu.used_outlets += 1
        
        # Update device
        device.hostname = form.hostname.data.upper()
        device.identifier = form.identifier.data.upper()
        device.device_type = form.device_type.data
        device.device_role = form.device_role.data
        device.network_type = form.network_type.data
        device.manufacturer = form.manufacturer.data
        device.model = form.model.data
        device.serial_number = form.serial_number.data
        device.software_version = form.software_version.data
        device.rack_id = form.rack_id.data
        device.start_u = form.start_u.data
        device.size_u = form.size_u.data
        device.management_ip = form.management_ip.data
        device.port_count = form.port_count.data
        device.pdu_1_id = form.pdu_1_id.data if form.pdu_1_id.data != 0 else None
        device.pdu_1_outlet = form.pdu_1_outlet.data
        device.pdu_2_id = form.pdu_2_id.data if form.pdu_2_id.data != 0 else None
        device.pdu_2_outlet = form.pdu_2_outlet.data
        device.power_consumption = form.power_consumption.data
        device.status = form.status.data
        device.notes = form.notes.data
        
        db.session.commit()
        flash(f'Network device {device.identifier} updated!', 'success')
        return redirect(url_for('network_devices.index'))
    
    return render_template('network_devices/edit_device.html', form=form, device=device)

# ========== DELETE OPERATIONS ==========

@network_devices_bp.route('/delete/<int:device_id>', methods=['POST'])
def delete_device(device_id):
    """Delete network device"""
    device = NetworkDevice.query.get_or_404(device_id)
    
    # Update rack usage
    rack = Rack.query.get(device.rack_id)
    rack.u_used -= device.size_u
    
    # Update PDU outlet usage
    if device.pdu_1_id:
        pdu1 = PDU.query.get(device.pdu_1_id)
        pdu1.used_outlets -= 1
    if device.pdu_2_id:
        pdu2 = PDU.query.get(device.pdu_2_id)
        pdu2.used_outlets -= 1
    
    db.session.delete(device)
    db.session.commit()
    
    flash(f'Network device {device.identifier} deleted!', 'success')
    return redirect(url_for('network_devices.index'))

# ========== API ENDPOINTS ==========

@network_devices_bp.route('/api/check-hostname/<hostname>')
def check_hostname_exists(hostname):
    """Check if hostname already exists"""
    existing = NetworkDevice.query.filter_by(hostname=hostname.upper()).first()
    return jsonify({'exists': existing is not None})

@network_devices_bp.route('/api/rack-usage/<int:rack_id>')
def get_rack_usage(rack_id):
    """Get current rack usage for visualization"""
    rack = Rack.query.get_or_404(rack_id)
    devices = NetworkDevice.query.filter_by(rack_id=rack_id).order_by(NetworkDevice.start_u.desc()).all()
    
    # Build usage map
    usage_map = []
    for device in devices:
        usage_map.append({
            'device': device.identifier,
            'start_u': device.start_u,
            'end_u': device.start_u + device.size_u - 1,
            'size': device.size_u,
            'type': device.device_type,
            'network': device.network_type
        })
    
    return jsonify({
        'rack_id': rack.rack_id,
        'total_u': rack.u_height,
        'used_u': rack.u_used,
        'available_u': rack.u_available,
        'devices': usage_map
    })

# ========== UTILITY FUNCTIONS ==========

def validate_rack_space(rack, start_u, size_u, exclude_device_id=None):
    """
    Validate if rack space is available
    Returns True if space is available, False otherwise
    """
    end_u = start_u + size_u - 1
    
    # Check if within rack bounds
    if start_u < 1 or end_u > rack.u_height:
        return False
    
    # Check for overlapping devices
    query = NetworkDevice.query.filter(
        and_(
            NetworkDevice.rack_id == rack.id,
            NetworkDevice.start_u < start_u + size_u,
            NetworkDevice.start_u + NetworkDevice.size_u > start_u
        )
    )
    
    # Exclude current device when editing
    if exclude_device_id:
        query = query.filter(NetworkDevice.id != exclude_device_id)
    
    overlapping = query.first()
    return overlapping is None