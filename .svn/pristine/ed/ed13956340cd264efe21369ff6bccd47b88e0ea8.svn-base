"""
File: routes/datacenters.py
Purpose: Route handlers for data center management
Created: 2024-09-13
Author: iambilky

Revision History:
- 2024-09-13: Initial creation with CRUD operations for DCs, floors, racks
- 2024-09-13: Added bulk rack creation functionality
- 2024-09-13: Added API endpoint for dashboard summary
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.datacenter import db, DataCenter, Floor, Rack, PDU
from forms.datacenter_forms import DataCenterForm, FloorForm, RackForm, PDUForm

# ========== BLUEPRINT INITIALIZATION ==========

datacenters_bp = Blueprint('datacenters', __name__, url_prefix='/datacenters')

# ========== MAIN VIEWS ==========

@datacenters_bp.route('/')
def index():
    """
    Main data center view - shows everything
    Displays all racks across all data centers in a single table
    """
    # Get all data centers
    datacenters = DataCenter.query.all()
    
    # Build the complete rack list with all info
    rack_data = []
    for dc in datacenters:
        for floor in dc.floors:
            for rack in floor.racks:
                rack_data.append({
                    'dc_code': dc.code,
                    'dc_name': dc.name,
                    'rack_id': rack.rack_id,
                    'floor_actual': floor.actual_floor,
                    'floor_provider': floor.provider_designation,
                    'u_height': rack.u_height,
                    'u_used': rack.u_used,
                    'u_available': rack.u_available,
                    'utilization': rack.utilization_percent,
                    'power_capacity': rack.power_capacity,
                    'power_used': rack.power_used,
                    'power_utilization': rack.power_utilization_percent,
                    'rack_obj_id': rack.id  # For edit/delete operations
                })
    
    # Calculate summary stats
    total_dcs = len(datacenters)
    total_racks = len(rack_data)
    total_capacity = sum(r['u_height'] for r in rack_data)
    total_used = sum(r['u_used'] for r in rack_data)
    overall_utilization = round((total_used / total_capacity * 100), 1) if total_capacity > 0 else 0
    
    return render_template('datacenters/index.html',
                         rack_data=rack_data,
                         total_dcs=total_dcs,
                         total_racks=total_racks,
                         total_capacity=total_capacity,
                         overall_utilization=overall_utilization)

# ========== CREATE OPERATIONS ==========

@datacenters_bp.route('/add-dc', methods=['GET', 'POST'])
def add_datacenter():
    """Add new data center"""
    form = DataCenterForm()
    
    if form.validate_on_submit():
        # Create new data center
        dc = DataCenter(
            code=form.code.data.upper(),
            name=form.name.data,
            address=form.address.data,
            contact_phone=form.contact_phone.data,
            contact_email=form.contact_email.data,
            notes=form.notes.data
        )
        db.session.add(dc)
        db.session.commit()
        flash(f'Data Center {dc.code} added successfully!', 'success')
        return redirect(url_for('datacenters.index'))
    
    return render_template('datacenters/add_dc.html', form=form)


@datacenters_bp.route('/add-floor/<int:dc_id>', methods=['GET', 'POST'])
def add_floor(dc_id):
    """Add floor to a data center"""
    dc = DataCenter.query.get_or_404(dc_id)
    form = FloorForm()
    
    if form.validate_on_submit():
        # Create new floor
        floor = Floor(
            datacenter_id=dc_id,
            provider_designation=form.provider_designation.data,
            actual_floor=form.actual_floor.data,
            description=form.description.data
        )
        db.session.add(floor)
        db.session.commit()
        flash(f'Floor {floor.provider_designation} added to {dc.code}!', 'success')
        return redirect(url_for('datacenters.index'))
    
    return render_template('datacenters/add_floor.html', form=form, dc=dc)


@datacenters_bp.route('/add-rack/<int:floor_id>', methods=['GET', 'POST'])
def add_rack(floor_id):
    """Add rack to a floor"""
    floor = Floor.query.get_or_404(floor_id)
    form = RackForm()
    
    if form.validate_on_submit():
        # Construct rack ID
        rack_id = f"{floor.datacenter.code}-{form.row_number.data}.{form.cabinet_number.data}"
        
        # Check if rack ID already exists
        existing = Rack.query.filter_by(rack_id=rack_id).first()
        if existing:
            flash(f'Rack {rack_id} already exists!', 'error')
            return render_template('datacenters/add_rack.html', form=form, floor=floor)
        
        # Create new rack
        rack = Rack(
            floor_id=floor_id,
            rack_id=rack_id,
            row_number=form.row_number.data,
            cabinet_number=form.cabinet_number.data,
            u_height=form.u_height.data,
            power_capacity=form.power_capacity.data,
            notes=form.notes.data
        )
        db.session.add(rack)
        db.session.commit()
        flash(f'Rack {rack_id} added successfully!', 'success')
        return redirect(url_for('datacenters.index'))
    
    return render_template('datacenters/add_rack.html', form=form, floor=floor)


@datacenters_bp.route('/bulk-add-racks/<int:floor_id>', methods=['GET', 'POST'])
def bulk_add_racks(floor_id):
    """
    Bulk add multiple racks
    Useful for adding an entire row of racks at once
    """
    floor = Floor.query.get_or_404(floor_id)
    
    if request.method == 'POST':
        # Get form data
        row_number = request.form.get('row_number')
        cabinet_start = int(request.form.get('cabinet_start', 1))
        cabinet_end = int(request.form.get('cabinet_end', 1))
        u_height = int(request.form.get('u_height', 42))
        power_capacity = float(request.form.get('power_capacity') or 0)
        
        # Add multiple racks
        added_count = 0
        for i in range(cabinet_start, cabinet_end + 1):
            cabinet_num = str(i).zfill(2)  # Pad with zero (01, 02, etc.)
            rack_id = f"{floor.datacenter.code}-{row_number}.{cabinet_num}"
            
            # Skip if already exists
            if not Rack.query.filter_by(rack_id=rack_id).first():
                rack = Rack(
                    floor_id=floor_id,
                    rack_id=rack_id,
                    row_number=row_number,
                    cabinet_number=cabinet_num,
                    u_height=u_height,
                    power_capacity=power_capacity
                )
                db.session.add(rack)
                added_count += 1
        
        db.session.commit()
        flash(f'Added {added_count} racks successfully!', 'success')
        return redirect(url_for('datacenters.index'))
    
    return render_template('datacenters/bulk_add_racks.html', floor=floor)

# ========== UPDATE OPERATIONS ==========

@datacenters_bp.route('/edit-rack/<int:rack_id>', methods=['GET', 'POST'])
def edit_rack(rack_id):
    """Edit rack details"""
    rack = Rack.query.get_or_404(rack_id)
    form = RackForm(obj=rack)
    
    if form.validate_on_submit():
        # Update rack information
        rack.u_height = form.u_height.data
        rack.power_capacity = form.power_capacity.data
        rack.notes = form.notes.data
        db.session.commit()
        flash(f'Rack {rack.rack_id} updated!', 'success')
        return redirect(url_for('datacenters.index'))
    
    return render_template('datacenters/edit_rack.html', form=form, rack=rack)

# ========== DELETE OPERATIONS ==========

@datacenters_bp.route('/delete-rack/<int:rack_id>', methods=['POST'])
def delete_rack(rack_id):
    """
    Delete a rack (only if empty)
    Prevents deletion if rack contains equipment
    """
    rack = Rack.query.get_or_404(rack_id)
    
    # Check if rack has equipment (will add this check later when equipment module is built)
    if rack.u_used > 0:
        flash(f'Cannot delete rack {rack.rack_id} - it has equipment!', 'error')
    else:
        db.session.delete(rack)
        db.session.commit()
        flash(f'Rack {rack.rack_id} deleted!', 'success')
    
    return redirect(url_for('datacenters.index'))

# ========== API ENDPOINTS ==========

@datacenters_bp.route('/api/dc-summary')
def api_dc_summary():
    """
    API endpoint for dashboard summary
    Returns JSON data about data center utilization
    """
    datacenters = DataCenter.query.all()
    
    summary = []
    for dc in datacenters:
        rack_count = dc.rack_count
        total_u = dc.total_u_capacity
        
        # Calculate used U (will be calculated from equipment later)
        used_u = sum(rack.u_used for floor in dc.floors for rack in floor.racks)
        
        summary.append({
            'code': dc.code,
            'name': dc.name,
            'rack_count': rack_count,
            'total_u': total_u,
            'used_u': used_u,
            'utilization': round((used_u / total_u * 100), 1) if total_u > 0 else 0
        })
    
    return jsonify(summary)