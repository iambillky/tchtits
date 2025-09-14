"""
File: routes/ipam.py
Purpose: Route handlers for IP Address Management module
Created: 2025-01-14
Author: DCMS Team

Revision History:
- 2025-01-14: Initial creation with core IPAM routes
             Dashboard, IP assignment, search, network management
             Implements "suggest next IP" to replace ping-and-pray
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.ipam import (
    db, Network, VLAN, IPRange, IPPool, IPAddress, IPHistory,
    check_duplicate_ip, suggest_next_available_ip, process_quarantine_expirations
)
from forms.ipam_forms import (
    NetworkForm, VLANForm, IPRangeForm, IPAssignmentForm, 
    IPSearchForm, IPPoolForm, BulkAssignForm
)
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import ipaddress

# ========== BLUEPRINT INITIALIZATION ==========

ipam_bp = Blueprint('ipam', __name__, url_prefix='/ipam')

# ========== UTILITY FUNCTIONS ==========

def calculate_network_stats(network):
    """
    Calculate statistics for a network
    Returns counts of available, assigned, quarantine, reserved IPs
    """
    # Get all IP addresses in this network's ranges
    ranges = network.ip_ranges.all()
    range_ids = [r.id for r in ranges]
    
    if not range_ids:
        return {
            'total': 0,
            'available': 0,
            'assigned': 0,
            'quarantine': 0,
            'reserved': 0,
            'utilization': 0
        }
    
    # Count by status
    total = IPAddress.query.filter(IPAddress.ip_range_id.in_(range_ids)).count()
    available = IPAddress.query.filter(
        IPAddress.ip_range_id.in_(range_ids),
        IPAddress.status == 'available'
    ).count()
    assigned = IPAddress.query.filter(
        IPAddress.ip_range_id.in_(range_ids),
        IPAddress.status == 'assigned'
    ).count()
    quarantine = IPAddress.query.filter(
        IPAddress.ip_range_id.in_(range_ids),
        IPAddress.status == 'quarantine'
    ).count()
    reserved = IPAddress.query.filter(
        IPAddress.ip_range_id.in_(range_ids),
        IPAddress.status == 'reserved'
    ).count()
    
    utilization = (assigned / total * 100) if total > 0 else 0
    
    return {
        'total': total,
        'available': available,
        'assigned': assigned,
        'quarantine': quarantine,
        'reserved': reserved,
        'utilization': round(utilization, 1)
    }

def validate_ip_in_range(ip_addr, ip_range):
    """
    Check if an IP address falls within a given range
    """
    try:
        ip = ipaddress.ip_address(ip_addr)
        start = ipaddress.ip_address(ip_range.start_ip)
        end = ipaddress.ip_address(ip_range.end_ip)
        return start <= ip <= end
    except:
        return False

# ========== MAIN DASHBOARD ==========

@ipam_bp.route('/')
def index():
    """
    Main IPAM dashboard
    Shows overview of all networks, VLANs, and IP utilization
    No more ping and pray!
    """
    # Process any expired quarantines first
    expired_count = process_quarantine_expirations()
    if expired_count > 0:
        flash(f'Released {expired_count} IPs from quarantine', 'info')
    
    # Get all networks with stats
    networks = Network.query.all()
    for network in networks:
        stats = calculate_network_stats(network)
        network.total_ips = stats['total']
        network.available_count = stats['available']
        network.assigned_count = stats['assigned']
        network.utilization = stats['utilization']
    
    # Get all VLANs
    vlans = VLAN.query.order_by(VLAN.vlan_number).all()
    
    # Get VPS pools
    vps_pools = IPPool.query.filter_by(pool_type='vps').all()
    
    # Calculate totals
    total_ips = IPAddress.query.count()
    available_ips = IPAddress.query.filter_by(status='available').count()
    assigned_ips = IPAddress.query.filter_by(status='assigned').count()
    quarantine_ips = IPAddress.query.filter_by(status='quarantine').count()
    reserved_ips = IPAddress.query.filter_by(status='reserved').count()
    
    return render_template('ipam/index.html',
                         networks=networks,
                         vlans=vlans,
                         vps_pools=vps_pools,
                         total_ips=total_ips,
                         available_ips=available_ips,
                         assigned_ips=assigned_ips,
                         quarantine_ips=quarantine_ips,
                         reserved_ips=reserved_ips)

# ========== IP ASSIGNMENT - THE GAME CHANGER ==========

@ipam_bp.route('/assign', methods=['GET', 'POST'])
def assign_ip():
    """
    Assign an IP address to a device
    This replaces the "ping and pray" method!
    Suggests next available IP automatically
    """
    form = IPAssignmentForm()
    
    # Get filter parameters for suggestion
    connection_type = request.args.get('type', 'public')
    vlan_id = request.args.get('vlan')
    pool_id = request.args.get('pool')
    
    # Get suggested IP - THE MAGIC HAPPENS HERE!
    suggested_ip = suggest_next_available_ip(
        vlan_id=vlan_id,
        pool_id=pool_id,
        connection_type=connection_type
    )
    
    # Get other available IPs in same range (for alternatives)
    available_nearby = []
    if suggested_ip and suggested_ip.ip_range:
        available_nearby = IPAddress.query.filter(
            IPAddress.ip_range_id == suggested_ip.ip_range_id,
            IPAddress.status == 'available',
            IPAddress.id != suggested_ip.id
        ).limit(20).all()
    
    if form.validate_on_submit():
        ip_address = form.ip_address.data
        
        # Check for duplicates - CRITICAL!
        existing = check_duplicate_ip(ip_address)
        if existing:
            flash(f'ERROR: IP {ip_address} is already assigned!', 'error')
            return redirect(url_for('ipam.assign_ip'))
        
        # Find or create the IP record
        ip = IPAddress.query.filter_by(address=ip_address).first()
        if not ip:
            # IP doesn't exist in system yet - create it
            # Find which range it belongs to
            ip_range = None
            for range_obj in IPRange.query.all():
                if validate_ip_in_range(ip_address, range_obj):
                    ip_range = range_obj
                    break
            
            if not ip_range:
                flash(f'ERROR: IP {ip_address} does not belong to any configured range!', 'error')
                return redirect(url_for('ipam.assign_ip'))
            
            ip = IPAddress(
                address=ip_address,
                ip_range_id=ip_range.id,
                status='available'
            )
            db.session.add(ip)
            db.session.flush()
        
        # Assign the IP
        try:
            ip.assign(
                device_type=form.device_type.data,
                device_id=form.device_id.data,
                user=request.remote_addr,  # In production, use actual username
                is_primary=form.is_primary.data,
                interface_name=form.interface_name.data,
                mac_address=form.mac_address.data,
                vps_hostname=form.vps_hostname.data,
                ptr_record=form.ptr_record.data,
                connection_type=connection_type
            )
            
            # Add notes if provided
            if form.notes.data:
                ip.notes = form.notes.data
            
            db.session.commit()
            
            flash(f'Successfully assigned IP {ip_address} to {form.device_type.data} #{form.device_id.data}!', 'success')
            
            # Redirect based on device type
            if form.device_type.data == 'server':
                return redirect(url_for('servers.view', server_id=form.device_id.data))
            else:
                return redirect(url_for('ipam.ip_detail', ip_id=ip.id))
                
        except ValueError as e:
            flash(str(e), 'error')
            db.session.rollback()
    
    return render_template('ipam/assign.html',
                         form=form,
                         suggested_ip=suggested_ip,
                         available_nearby=available_nearby)

# ========== SUGGEST NEXT IP API ==========

@ipam_bp.route('/suggest')
def suggest():
    """
    API endpoint for getting next available IP
    The heart of "no more ping and pray"!
    """
    connection_type = request.args.get('type', 'public')
    vlan_id = request.args.get('vlan')
    pool_id = request.args.get('pool')
    
    suggested_ip = suggest_next_available_ip(
        vlan_id=vlan_id,
        pool_id=pool_id,
        connection_type=connection_type
    )
    
    if suggested_ip:
        return jsonify({
            'success': True,
            'ip': suggested_ip.address,
            'network': suggested_ip.ip_range.network.network if suggested_ip.ip_range else None,
            'vlan': suggested_ip.ip_range.vlan.vlan_number if suggested_ip.ip_range and suggested_ip.ip_range.vlan else None,
            'gateway': suggested_ip.ip_range.gateway if suggested_ip.ip_range else None
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No available IPs found with specified criteria'
        }), 404

# ========== IP SEARCH & LOOKUP ==========

@ipam_bp.route('/search')
def search():
    """
    Search for a specific IP address
    Quick lookup to see assignment status
    """
    ip_address = request.args.get('ip', '').strip()
    
    if not ip_address:
        return render_template('ipam/search.html', ip=None)
    
    # Validate IP format
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        flash(f'Invalid IP address format: {ip_address}', 'error')
        return render_template('ipam/search.html', ip=None)
    
    # Find the IP
    ip = IPAddress.query.filter_by(address=ip_address).first()
    
    if not ip:
        # IP not in system - check if it belongs to any range
        belongs_to_range = None
        for ip_range in IPRange.query.all():
            if validate_ip_in_range(ip_address, ip_range):
                belongs_to_range = ip_range
                break
        
        return render_template('ipam/search.html', 
                             ip=None, 
                             searched_ip=ip_address,
                             belongs_to_range=belongs_to_range)
    
    # Get history
    history = ip.history.limit(10).all()
    
    return render_template('ipam/search.html', 
                         ip=ip, 
                         history=history)

# ========== CHECK DUPLICATE API ==========

@ipam_bp.route('/check-duplicate')
def check_duplicate():
    """
    AJAX endpoint to check if IP is already assigned
    Critical for preventing duplicates!
    """
    ip_address = request.args.get('ip', '').strip()
    
    if not ip_address:
        return jsonify({'error': 'No IP provided'}), 400
    
    existing = check_duplicate_ip(ip_address)
    
    if existing:
        assigned_to = f"{existing.assigned_to_type} #{existing.assigned_to_id}"
        if existing.vps_hostname:
            assigned_to += f" ({existing.vps_hostname})"
        
        return jsonify({
            'available': False,
            'assigned_to': assigned_to,
            'status': existing.status,
            'assigned_date': existing.assignment_date.isoformat() if existing.assignment_date else None
        })
    else:
        return jsonify({
            'available': True,
            'message': 'IP is available for assignment'
        })

# ========== NETWORK MANAGEMENT ==========

@ipam_bp.route('/networks')
def networks():
    """List all networks"""
    networks = Network.query.order_by(Network.network).all()
    for network in networks:
        stats = calculate_network_stats(network)
        network.stats = stats
    
    return render_template('ipam/networks.html', networks=networks)

@ipam_bp.route('/network/add', methods=['GET', 'POST'])
def add_network():
    """
    Add a new network block
    This is the starting point for tracking IPs
    """
    form = NetworkForm()
    
    if form.validate_on_submit():
        # Check if network already exists
        existing = Network.query.filter_by(network=form.network.data).first()
        if existing:
            flash(f'Network {form.network.data} already exists!', 'error')
            return redirect(url_for('ipam.add_network'))
        
        network = Network(
            network=form.network.data,
            cidr=form.cidr.data,
            description=form.description.data,
            datacenter_id=form.datacenter_id.data if form.datacenter_id.data else None,
            bgp_advertised=form.bgp_advertised.data
        )
        
        db.session.add(network)
        db.session.commit()
        
        flash(f'Network {network.network} added successfully!', 'success')
        
        # Redirect to add ranges for this network
        return redirect(url_for('ipam.add_range', network_id=network.id))
    
    return render_template('ipam/add_network.html', form=form)

# ========== VLAN MANAGEMENT ==========

@ipam_bp.route('/vlans')
def vlans():
    """List all VLANs"""
    vlans = VLAN.query.order_by(VLAN.vlan_number).all()
    return render_template('ipam/vlans.html', vlans=vlans)

@ipam_bp.route('/vlan/add', methods=['GET', 'POST'])
def add_vlan():
    """Add a new VLAN"""
    form = VLANForm()
    
    if form.validate_on_submit():
        # Check if VLAN already exists
        existing = VLAN.query.filter_by(vlan_number=form.vlan_number.data).first()
        if existing:
            flash(f'VLAN {form.vlan_number.data} already exists!', 'error')
            return redirect(url_for('ipam.add_vlan'))
        
        vlan = VLAN(
            vlan_number=form.vlan_number.data,
            name=form.name.data or f"Vlan{form.vlan_number.data}",
            description=form.description.data,
            vrf=form.vrf.data,
            is_private=form.is_private.data,
            is_colo=form.is_colo.data,
            is_vps=form.is_vps.data
        )
        
        db.session.add(vlan)
        db.session.commit()
        
        flash(f'VLAN {vlan.vlan_number} added successfully!', 'success')
        return redirect(url_for('ipam.vlans'))
    
    return render_template('ipam/add_vlan.html', form=form)

# ========== IP RANGE MANAGEMENT ==========

@ipam_bp.route('/range/add', methods=['GET', 'POST'])
def add_range():
    """
    Add an IP range to a network
    This creates the actual assignable IPs
    """
    network_id = request.args.get('network_id')
    form = IPRangeForm()
    
    # Populate network dropdown
    form.network_id.choices = [(n.id, n.network) for n in Network.query.all()]
    if network_id:
        form.network_id.data = int(network_id)
    
    # Populate VLAN dropdown
    form.vlan_id.choices = [(0, '-- No VLAN --')] + [
        (v.id, f"VLAN {v.vlan_number} - {v.name}") for v in VLAN.query.order_by(VLAN.vlan_number).all()
    ]
    
    if form.validate_on_submit():
        # Check if range overlaps with existing
        # TODO: Add overlap validation
        
        ip_range = IPRange(
            network_id=form.network_id.data,
            vlan_id=form.vlan_id.data if form.vlan_id.data != 0 else None,
            start_ip=form.start_ip.data,
            end_ip=form.end_ip.data,
            gateway=form.gateway.data,
            netmask=form.netmask.data,
            range_type=form.range_type.data,
            status=form.status.data,
            description=form.description.data
        )
        
        db.session.add(ip_range)
        db.session.flush()
        
        # Create IP address records for this range
        if form.create_ips.data:
            created_count = create_ips_for_range(ip_range)
            flash(f'Created {created_count} IP addresses for range {ip_range.start_ip}-{ip_range.end_ip}', 'info')
        
        db.session.commit()
        
        flash(f'IP range {ip_range.start_ip}-{ip_range.end_ip} added successfully!', 'success')
        return redirect(url_for('ipam.networks'))
    
    return render_template('ipam/add_range.html', form=form)

def create_ips_for_range(ip_range):
    """
    Create IP address records for all IPs in a range
    Pre-populates the database with all possible IPs
    """
    count = 0
    try:
        start = ipaddress.ip_address(ip_range.start_ip)
        end = ipaddress.ip_address(ip_range.end_ip)
        gateway = ipaddress.ip_address(ip_range.gateway) if ip_range.gateway else None
        
        current = start
        while current <= end:
            ip_str = str(current)
            
            # Check if IP already exists
            existing = IPAddress.query.filter_by(address=ip_str).first()
            if not existing:
                # Determine status
                if gateway and current == gateway:
                    status = 'gateway'
                elif current == start and ip_str.endswith('.0'):
                    status = 'network'
                elif current == end and ip_str.endswith('.255'):
                    status = 'broadcast'
                else:
                    status = 'available'
                
                ip = IPAddress(
                    address=ip_str,
                    ip_range_id=ip_range.id,
                    status=status
                )
                db.session.add(ip)
                count += 1
            
            current += 1
            
            # Commit in batches for performance
            if count % 100 == 0:
                db.session.flush()
    
    except Exception as e:
        print(f"Error creating IPs: {e}")
        db.session.rollback()
        raise
    
    return count

# ========== VPS POOL MANAGEMENT ==========

@ipam_bp.route('/vps-pools')
def vps_pools():
    """
    Manage VPS IP pools
    Shows hypervisor assignments and utilization
    """
    pools = IPPool.query.all()
    
    for pool in pools:
        # Calculate stats
        total = pool.ip_addresses.count()
        assigned = pool.ip_addresses.filter_by(status='assigned').count()
        pool.total_ips = total
        pool.assigned_ips = assigned
        pool.available_ips = pool.ip_addresses.filter_by(status='available').count()
        pool.utilization_percent = pool.utilization
    
    return render_template('ipam/vps_pools.html', pools=pools)

@ipam_bp.route('/vps-pool/add', methods=['GET', 'POST'])
def add_vps_pool():
    """Create a new VPS pool"""
    form = IPPoolForm()
    
    # Populate VLAN dropdown
    form.vlan_id.choices = [(v.id, f"VLAN {v.vlan_number} - {v.name}") 
                           for v in VLAN.query.order_by(VLAN.vlan_number).all()]
    
    if form.validate_on_submit():
        pool = IPPool(
            name=form.name.data,
            pool_type='vps',
            vlan_id=form.vlan_id.data,
            description=form.description.data,
            is_active=form.is_active.data
        )
        
        db.session.add(pool)
        db.session.commit()
        
        flash(f'VPS pool {pool.name} created successfully!', 'success')
        return redirect(url_for('ipam.vps_pools'))
    
    return render_template('ipam/add_vps_pool.html', form=form)

# ========== IP RELEASE ==========

@ipam_bp.route('/ip/<int:ip_id>/release', methods=['POST'])
def release_ip(ip_id):
    """
    Release an IP address and start quarantine
    90-day quarantine period begins!
    """
    ip = IPAddress.query.get_or_404(ip_id)
    
    if ip.status != 'assigned':
        flash(f'IP {ip.address} is not currently assigned!', 'error')
        return redirect(url_for('ipam.ip_detail', ip_id=ip_id))
    
    try:
        # Store info for flash message
        device_info = f"{ip.assigned_to_type} #{ip.assigned_to_id}"
        
        # Release with quarantine
        ip.release(user=request.remote_addr)  # In production, use actual username
        db.session.commit()
        
        flash(f'IP {ip.address} released from {device_info}. In quarantine until {ip.quarantine_until.strftime("%Y-%m-%d")}', 'success')
        
    except Exception as e:
        flash(f'Error releasing IP: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('ipam.search', ip=ip.address))

# ========== QUARANTINE MANAGEMENT ==========

@ipam_bp.route('/quarantine')
def quarantine():
    """
    View all IPs currently in quarantine
    Shows when they will be available again
    """
    quarantined = IPAddress.query.filter_by(status='quarantine').order_by(IPAddress.quarantine_until).all()
    
    # Group by days remaining
    grouped = {}
    today = datetime.utcnow()
    
    for ip in quarantined:
        days_remaining = (ip.quarantine_until - today).days
        if days_remaining not in grouped:
            grouped[days_remaining] = []
        grouped[days_remaining].append(ip)
    
    return render_template('ipam/quarantine.html', 
                         quarantined=quarantined,
                         grouped=grouped,
                         total_count=len(quarantined))

# ========== HISTORY VIEW ==========

@ipam_bp.route('/history')
def history():
    """
    View IP assignment history
    Complete audit trail of all IP operations
    """
    # Get recent history
    recent_history = IPHistory.query.order_by(IPHistory.performed_at.desc()).limit(100).all()
    
    # Get filter parameters
    ip_address = request.args.get('ip')
    device_type = request.args.get('device_type')
    device_id = request.args.get('device_id')
    
    query = IPHistory.query
    
    if ip_address:
        ip = IPAddress.query.filter_by(address=ip_address).first()
        if ip:
            query = query.filter_by(ip_address_id=ip.id)
    
    if device_type:
        query = query.filter_by(assigned_to_type=device_type)
    
    if device_id:
        query = query.filter_by(assigned_to_id=device_id)
    
    history_items = query.order_by(IPHistory.performed_at.desc()).limit(500).all()
    
    return render_template('ipam/history.html', 
                         history_items=history_items if ip_address or device_type or device_id else recent_history,
                         filtered=(ip_address or device_type or device_id))

# ========== BULK OPERATIONS ==========

@ipam_bp.route('/bulk-assign', methods=['GET', 'POST'])
def bulk_assign():
    """
    Bulk assign multiple IPs (like entire /24 for a server)
    Handles those crazy "entire subnet" assignments
    """
    form = BulkAssignForm()
    
    if form.validate_on_submit():
        # Parse the range
        try:
            if '/' in form.ip_range.data:
                # CIDR notation
                network = ipaddress.ip_network(form.ip_range.data, strict=False)
                ips_to_assign = [str(ip) for ip in network.hosts()]
            elif '-' in form.ip_range.data:
                # Range notation (192.168.1.1-192.168.1.10)
                start_ip, end_ip = form.ip_range.data.split('-')
                start = ipaddress.ip_address(start_ip.strip())
                end = ipaddress.ip_address(end_ip.strip())
                
                ips_to_assign = []
                current = start
                while current <= end:
                    ips_to_assign.append(str(current))
                    current += 1
            else:
                flash('Invalid range format. Use CIDR (192.168.1.0/24) or range (192.168.1.1-192.168.1.10)', 'error')
                return redirect(url_for('ipam.bulk_assign'))
            
            # Assign all IPs
            assigned_count = 0
            failed_count = 0
            
            for ip_addr in ips_to_assign:
                # Check if IP exists and is available
                ip = IPAddress.query.filter_by(address=ip_addr).first()
                
                if not ip:
                    # Try to create it
                    # Find which range it belongs to
                    ip_range = None
                    for range_obj in IPRange.query.all():
                        if validate_ip_in_range(ip_addr, range_obj):
                            ip_range = range_obj
                            break
                    
                    if ip_range:
                        ip = IPAddress(
                            address=ip_addr,
                            ip_range_id=ip_range.id,
                            status='available'
                        )
                        db.session.add(ip)
                        db.session.flush()
                    else:
                        failed_count += 1
                        continue
                
                if ip and ip.status == 'available':
                    try:
                        ip.assign(
                            device_type=form.device_type.data,
                            device_id=form.device_id.data,
                            user=request.remote_addr,
                            is_primary=False,  # Bulk assigns are add-ons
                            notes=f"Bulk assignment: {form.notes.data}"
                        )
                        assigned_count += 1
                    except:
                        failed_count += 1
                else:
                    failed_count += 1
            
            db.session.commit()
            
            flash(f'Bulk assignment complete: {assigned_count} IPs assigned, {failed_count} failed', 
                  'success' if failed_count == 0 else 'warning')
            
            return redirect(url_for('ipam.index'))
            
        except Exception as e:
            flash(f'Error processing bulk assignment: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('ipam/bulk_assign.html', form=form)

# ========== API ENDPOINTS ==========

@ipam_bp.route('/api/stats')
def api_stats():
    """API endpoint for dashboard stats"""
    stats = {
        'total_ips': IPAddress.query.count(),
        'available': IPAddress.query.filter_by(status='available').count(),
        'assigned': IPAddress.query.filter_by(status='assigned').count(),
        'quarantine': IPAddress.query.filter_by(status='quarantine').count(),
        'reserved': IPAddress.query.filter_by(status='reserved').count(),
        'networks': Network.query.count(),
        'vlans': VLAN.query.count(),
        'pools': IPPool.query.count()
    }
    return jsonify(stats)

@ipam_bp.route('/api/network/<int:network_id>/ips')
def api_network_ips(network_id):
    """Get all IPs in a network"""
    network = Network.query.get_or_404(network_id)
    ranges = network.ip_ranges.all()
    range_ids = [r.id for r in ranges]
    
    ips = IPAddress.query.filter(IPAddress.ip_range_id.in_(range_ids)).all()
    
    return jsonify([{
        'id': ip.id,
        'address': ip.address,
        'status': ip.status,
        'assigned_to': f"{ip.assigned_to_type} #{ip.assigned_to_id}" if ip.assigned_to_type else None,
        'vlan': ip.ip_range.vlan.vlan_number if ip.ip_range and ip.ip_range.vlan else None
    } for ip in ips])

# ========== END OF IPAM ROUTES ==========