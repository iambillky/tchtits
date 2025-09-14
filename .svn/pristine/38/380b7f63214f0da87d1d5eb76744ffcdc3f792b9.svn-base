"""
File: routes/pdus.py
Purpose: Route handlers for PDU (Power Distribution Unit) management
Version: 1.0.0
Author: DCMS Team

Revision History:
- v1.0.0: Initial creation with full CRUD operations for PDUs
         Includes listing, adding, editing, deleting PDUs
         Outlet management and bank tracking (Bank 1: 1-12, Bank 2: 13-24)
         Power usage statistics and circuit capacity monitoring
         Integration with network devices and future server modules
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.datacenter import db, PDU, Rack, DataCenter, Floor
from models.network_device import NetworkDevice
from forms.datacenter_forms import PDUForm
from sqlalchemy import and_, or_, func

# ========== BLUEPRINT INITIALIZATION ==========

pdus_bp = Blueprint('pdus', __name__, url_prefix='/pdus')

# ========== UTILITY FUNCTIONS ==========

def calculate_bank_usage(pdu_id):
    """
    Calculate outlet usage per bank for a PDU
    Bank 1: Outlets 1-12
    Bank 2: Outlets 13-24 (or 13+ for larger PDUs)
    
    Returns: (bank1_used, bank2_used)
    """
    # Get all devices connected to this PDU
    devices_on_pdu_1 = NetworkDevice.query.filter_by(pdu_1_id=pdu_id).all()
    devices_on_pdu_2 = NetworkDevice.query.filter_by(pdu_2_id=pdu_id).all()
    
    bank1_used = 0
    bank2_used = 0
    
    # Count outlets in Bank 1 (1-12)
    for device in devices_on_pdu_1:
        if device.pdu_1_outlet and device.pdu_1_outlet <= 12:
            bank1_used += 1
        elif device.pdu_1_outlet and device.pdu_1_outlet > 12:
            bank2_used += 1
    
    # Count outlets in Bank 2 for redundant connections
    for device in devices_on_pdu_2:
        if device.pdu_2_outlet and device.pdu_2_outlet <= 12:
            bank1_used += 1
        elif device.pdu_2_outlet and device.pdu_2_outlet > 12:
            bank2_used += 1
    
    return bank1_used, bank2_used

def get_outlet_map(pdu_id):
    """
    Build a map of which device is on which outlet
    Returns: dict {outlet_number: device_info}
    """
    outlet_map = {}
    
    # Get devices on primary PDU connection
    devices_primary = NetworkDevice.query.filter_by(pdu_1_id=pdu_id).all()
    for device in devices_primary:
        if device.pdu_1_outlet:
            outlet_map[device.pdu_1_outlet] = {
                'device': device.identifier,
                'type': 'network',
                'connection': 'primary'
            }
    
    # Get devices on redundant PDU connection
    devices_redundant = NetworkDevice.query.filter_by(pdu_2_id=pdu_id).all()
    for device in devices_redundant:
        if device.pdu_2_outlet:
            outlet_map[device.pdu_2_outlet] = {
                'device': device.identifier,
                'type': 'network',
                'connection': 'redundant'
            }
    
    # TODO: Add server connections when server module is built
    
    return outlet_map

# ========== MAIN VIEWS ==========

@pdus_bp.route('/')
def index():
    """
    Main PDU management view
    Shows all PDUs with filtering by DC, rack, voltage, capacity
    Includes bank usage visualization
    """
    # Get filter parameters
    dc_filter = request.args.get('datacenter', 'all')
    rack_filter = request.args.get('rack', 'all')
    voltage_filter = request.args.get('voltage', 'all')
    capacity_filter = request.args.get('capacity', 'all')
    
    # Build query
    query = PDU.query.join(Rack)
    
    # Apply filters
    if dc_filter != 'all':
        query = query.join(Floor).filter(Floor.datacenter_id == int(dc_filter))
    if rack_filter != 'all':
        query = query.filter(PDU.rack_id == int(rack_filter))
    if voltage_filter != 'all':
        query = query.filter(PDU.voltage == int(voltage_filter))
    if capacity_filter != 'all':
        query = query.filter(PDU.capacity_amps == float(capacity_filter))
    
    # Get filtered PDUs
    pdus = query.order_by(PDU.identifier).all()
    
    # Add bank usage to each PDU
    for pdu in pdus:
        pdu.bank1_used, pdu.bank2_used = calculate_bank_usage(pdu.id)
    
    # Get all data for filter dropdowns
    datacenters = DataCenter.query.all()
    
    # Get racks based on DC filter
    if dc_filter != 'all':
        filter_racks = Rack.query.join(Floor).filter(
            Floor.datacenter_id == int(dc_filter)
        ).order_by(Rack.rack_id).all()
    else:
        filter_racks = Rack.query.order_by(Rack.rack_id).all()
    
    # Get all racks for Add PDU dropdown
    all_racks = Rack.query.order_by(Rack.rack_id).all()
    
    # Calculate summary statistics
    total_pdus = PDU.query.count()
    total_outlets = db.session.query(func.sum(PDU.total_outlets)).scalar() or 0
    used_outlets = db.session.query(func.sum(PDU.used_outlets)).scalar() or 0
    available_outlets = total_outlets - used_outlets
    total_capacity = db.session.query(func.sum(PDU.capacity_amps)).scalar() or 0
    
    return render_template('pdus/index.html',
                         pdus=pdus,
                         datacenters=datacenters,
                         filter_racks=filter_racks,
                         racks=all_racks,  # For Add PDU dropdown
                         total_pdus=total_pdus,
                         total_outlets=total_outlets,
                         used_outlets=used_outlets,
                         available_outlets=available_outlets,
                         total_capacity=total_capacity,
                         current_filters={
                             'datacenter': dc_filter,
                             'rack': rack_filter,
                             'voltage': voltage_filter,
                             'capacity': capacity_filter
                         })

# ========== CREATE OPERATIONS ==========

@pdus_bp.route('/add/<int:rack_id>', methods=['GET', 'POST'])
def add_pdu(rack_id):
    """
    Add new PDU to a specific rack
    Sequential numbering: APC 1, APC 2, etc. (DC-wide)
    """
    rack = Rack.query.get_or_404(rack_id)
    form = PDUForm()
    
    if form.validate_on_submit():
        # Check if identifier already exists
        existing = PDU.query.filter_by(identifier=form.identifier.data).first()
        if existing:
            flash(f'PDU {form.identifier.data} already exists!', 'error')
            return render_template('pdus/add_pdu.html', form=form, rack=rack)
        
        # Create new PDU
        pdu = PDU(
            rack_id=rack_id,
            identifier=form.identifier.data,
            model=form.model.data,
            circuit_id=form.circuit_id.data,
            capacity_amps=form.capacity_amps.data,
            voltage=form.voltage.data,
            phase=form.phase.data,
            total_outlets=form.total_outlets.data,
            used_outlets=0,  # Start with no outlets used
            ip_address=form.ip_address.data,
            notes=form.notes.data
        )
        
        db.session.add(pdu)
        db.session.commit()
        
        flash(f'PDU {pdu.identifier} added to rack {rack.rack_id}!', 'success')
        return redirect(url_for('pdus.index'))
    
    # Suggest next PDU number
    last_pdu = PDU.query.filter(PDU.identifier.like('APC %')).order_by(PDU.id.desc()).first()
    if last_pdu:
        # Extract number from "APC 8" format
        try:
            last_num = int(last_pdu.identifier.split(' ')[-1])
            form.identifier.data = f"APC {last_num + 1}"
        except:
            form.identifier.data = "APC 1"
    else:
        form.identifier.data = "APC 1"
    
    return render_template('pdus/add_pdu.html', form=form, rack=rack)

# ========== UPDATE OPERATIONS ==========

@pdus_bp.route('/edit/<int:pdu_id>', methods=['GET', 'POST'])
def edit_pdu(pdu_id):
    """Edit PDU configuration"""
    pdu = PDU.query.get_or_404(pdu_id)
    form = PDUForm(obj=pdu)
    
    if form.validate_on_submit():
        # Check if identifier changed and already exists
        if form.identifier.data != pdu.identifier:
            existing = PDU.query.filter_by(identifier=form.identifier.data).first()
            if existing:
                flash(f'PDU {form.identifier.data} already exists!', 'error')
                return render_template('pdus/edit_pdu.html', form=form, pdu=pdu)
        
        # Update PDU
        pdu.identifier = form.identifier.data
        pdu.model = form.model.data
        pdu.circuit_id = form.circuit_id.data
        pdu.capacity_amps = form.capacity_amps.data
        pdu.voltage = form.voltage.data
        pdu.phase = form.phase.data
        pdu.total_outlets = form.total_outlets.data
        pdu.ip_address = form.ip_address.data
        pdu.notes = form.notes.data
        
        db.session.commit()
        flash(f'PDU {pdu.identifier} updated!', 'success')
        return redirect(url_for('pdus.index'))
    
    return render_template('pdus/edit_pdu.html', form=form, pdu=pdu)

# ========== DELETE OPERATIONS ==========

@pdus_bp.route('/delete/<int:pdu_id>', methods=['POST'])
def delete_pdu(pdu_id):
    """
    Delete PDU (only if no outlets are in use)
    """
    pdu = PDU.query.get_or_404(pdu_id)
    
    # Check if PDU has connected devices
    if pdu.used_outlets > 0:
        flash(f'Cannot delete PDU {pdu.identifier} - it has {pdu.used_outlets} outlets in use!', 'error')
    else:
        rack_id = pdu.rack.rack_id
        db.session.delete(pdu)
        db.session.commit()
        flash(f'PDU {pdu.identifier} removed from rack {rack_id}!', 'success')
    
    return redirect(url_for('pdus.index'))

# ========== OUTLET MANAGEMENT ==========

@pdus_bp.route('/outlets/<int:pdu_id>')
def view_outlets(pdu_id):
    """
    View detailed outlet map for a PDU
    Shows which device is on which outlet, organized by banks
    """
    pdu = PDU.query.get_or_404(pdu_id)
    outlet_map = get_outlet_map(pdu_id)
    
    # Build bank arrays
    bank1 = []  # Outlets 1-12
    bank2 = []  # Outlets 13-24 (or more)
    
    for outlet_num in range(1, pdu.total_outlets + 1):
        outlet_info = {
            'number': outlet_num,
            'device': outlet_map.get(outlet_num)
        }
        
        if outlet_num <= 12:
            bank1.append(outlet_info)
        else:
            bank2.append(outlet_info)
    
    return render_template('pdus/outlet_view.html',
                         pdu=pdu,
                         bank1=bank1,
                         bank2=bank2,
                         outlet_map=outlet_map)

# ========== POWER MAPPING ==========

@pdus_bp.route('/power-map')
def power_map():
    """
    Visual power distribution map
    Shows power usage across all racks and circuits
    """
    # Group PDUs by rack
    racks = Rack.query.join(PDU).distinct().order_by(Rack.rack_id).all()
    
    power_data = []
    for rack in racks:
        rack_pdus = []
        total_capacity = 0
        estimated_load = 0
        
        for pdu in rack.pdus:
            pdu.bank1_used, pdu.bank2_used = calculate_bank_usage(pdu.id)
            
            # Estimate load (simple calculation - can be improved)
            # Assume average 150W per device at 120V = 1.25A
            # Or 300W per device at 208V = 1.44A
            if pdu.voltage == 120:
                estimated_amps = pdu.used_outlets * 1.25
            else:
                estimated_amps = pdu.used_outlets * 1.44
            
            rack_pdus.append({
                'pdu': pdu,
                'estimated_load': estimated_amps,
                'utilization': (estimated_amps / pdu.capacity_amps * 100) if pdu.capacity_amps > 0 else 0
            })
            
            total_capacity += pdu.capacity_amps
            estimated_load += estimated_amps
        
        power_data.append({
            'rack': rack,
            'pdus': rack_pdus,
            'total_capacity': total_capacity,
            'estimated_load': estimated_load,
            'utilization': (estimated_load / total_capacity * 100) if total_capacity > 0 else 0
        })
    
    return render_template('pdus/power_map.html', power_data=power_data)

# ========== API ENDPOINTS ==========

@pdus_bp.route('/api/pdu-stats/<int:pdu_id>')
def api_pdu_stats(pdu_id):
    """Get PDU statistics as JSON"""
    pdu = PDU.query.get_or_404(pdu_id)
    bank1_used, bank2_used = calculate_bank_usage(pdu_id)
    
    return jsonify({
        'identifier': pdu.identifier,
        'total_outlets': pdu.total_outlets,
        'used_outlets': pdu.used_outlets,
        'available_outlets': pdu.available_outlets,
        'bank1_used': bank1_used,
        'bank2_used': bank2_used,
        'capacity_amps': pdu.capacity_amps,
        'voltage': pdu.voltage,
        'watts_capacity': pdu.watts_capacity
    })

@pdus_bp.route('/api/check-outlet/<int:pdu_id>/<int:outlet>')
def check_outlet_available(pdu_id, outlet):
    """Check if specific outlet is available"""
    outlet_map = get_outlet_map(pdu_id)
    is_available = outlet not in outlet_map
    
    return jsonify({
        'available': is_available,
        'device': outlet_map.get(outlet) if not is_available else None
    })

@pdus_bp.route('/api/rack-power/<int:rack_id>')
def api_rack_power(rack_id):
    """Get power summary for a rack"""
    rack = Rack.query.get_or_404(rack_id)
    
    pdus_data = []
    total_capacity = 0
    total_used = 0
    
    for pdu in rack.pdus:
        bank1_used, bank2_used = calculate_bank_usage(pdu.id)
        pdus_data.append({
            'id': pdu.id,
            'identifier': pdu.identifier,
            'capacity': pdu.capacity_amps,
            'voltage': pdu.voltage,
            'outlets': {
                'total': pdu.total_outlets,
                'used': pdu.used_outlets,
                'bank1_used': bank1_used,
                'bank2_used': bank2_used
            }
        })
        total_capacity += pdu.capacity_amps
        total_used += pdu.used_outlets
    
    return jsonify({
        'rack_id': rack.rack_id,
        'pdus': pdus_data,
        'total_capacity_amps': total_capacity,
        'total_outlets_used': total_used
    })