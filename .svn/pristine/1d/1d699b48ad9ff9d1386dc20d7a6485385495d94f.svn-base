"""
File: forms/ipam_forms.py
Purpose: Form definitions for IP Address Management module
Created: 2025-01-14
Author: DCMS Team

Revision History:
- v1.0.0: Initial creation with all IPAM forms
          Network, VLAN, IP Range, Assignment forms
          Validation to prevent duplicate IPs
- v1.0.1: Added is_public field to NetworkForm to match model
          Field is auto-detected but needed for form processing
- v1.0.2: Added description field to IPRangeForm to fix template error
- v1.0.3: Added ip_range field to BulkAssignForm to fix template error
- v1.0.4: Added create_ips field to IPRangeForm to fix template error
- v1.0.5: Added colo_client fields to VLANForm for tracking colocation customers
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, IntegerField, SelectField, BooleanField, 
    TextAreaField, DecimalField, SubmitField, ValidationError, HiddenField
)
from wtforms.validators import DataRequired, Optional, IPAddress, MacAddress, Length, Regexp
import ipaddress
import re

# ========== NETWORK FORM ==========

class NetworkForm(FlaskForm):
    """
    Form for adding/editing network blocks
    Example: 208.76.80.0/24
    """
    network = StringField('Network (CIDR)', 
                         validators=[DataRequired()],
                         render_kw={"placeholder": "e.g., 208.76.80.0/24"})
    
    cidr = IntegerField('CIDR Prefix', 
                       validators=[DataRequired()],
                       render_kw={"placeholder": "24"})
    
    description = TextAreaField('Description',
                               validators=[Optional()],
                               render_kw={"placeholder": "Main public network block"})
    
    datacenter_id = SelectField('Data Center', 
                               coerce=int,
                               validators=[Optional()])
    
    bgp_advertised = BooleanField('BGP Advertised')
    
    # Added to match model - auto-detected in route based on IP range
    is_public = BooleanField('Public Network', default=True)
    
    submit = SubmitField('Add Network')
    
    def validate_network(self, field):
        """Validate network format"""
        try:
            # Check if it's a valid network
            net = ipaddress.ip_network(field.data, strict=False)
            # Store the normalized version
            field.data = str(net)
        except ValueError:
            raise ValidationError('Invalid network format. Use CIDR notation (e.g., 192.168.1.0/24)')

# ========== VLAN FORM ==========

class VLANForm(FlaskForm):
    """
    Form for adding/editing VLANs
    """
    vlan_number = IntegerField('VLAN Number',
                              validators=[DataRequired()],
                              render_kw={"placeholder": "e.g., 111"})
    
    name = StringField('VLAN Name',
                      validators=[Optional()],
                      render_kw={"placeholder": "e.g., Vlan111"})
    
    description = TextAreaField('Description',
                               validators=[Optional()],
                               render_kw={"placeholder": "Public customer VLAN"})
    
    vrf = StringField('VRF',
                     validators=[Optional()],
                     render_kw={"placeholder": "e.g., private"})
    
    is_private = BooleanField('Private Network (10.x.x.x)')
    is_colo = BooleanField('Colocation VLAN')
    is_vps = BooleanField('VPS Pool VLAN')
    
    # === Colocation Client Tracking ===
    colo_client_id = IntegerField('Colocation Client ID',
                                  validators=[Optional()],
                                  render_kw={"placeholder": "e.g., 1001"})
    
    colo_client_name = StringField('Colocation Client Name',
                                   validators=[Optional(), Length(max=100)],
                                   render_kw={"placeholder": "e.g., Acme Corp"})
    
    submit = SubmitField('Add VLAN')
    
    def validate_vlan_number(self, field):
        """Validate VLAN number range"""
        if field.data < 1 or field.data > 4094:
            raise ValidationError('VLAN number must be between 1 and 4094')
    
    def validate_colo_client_id(self, field):
        """Validate that colo client ID is provided if is_colo is checked"""
        if self.is_colo.data and not field.data and not self.colo_client_name.data:
            raise ValidationError('Please provide Client ID or Name for colocation VLANs')

# ========== IP RANGE FORM ==========

class IPRangeForm(FlaskForm):
    """
    Form for adding IP ranges within networks
    Maps to VLAN interfaces on core switch
    """
    network_id = SelectField('Parent Network',
                            coerce=int,
                            validators=[DataRequired()])
    
    vlan_id = SelectField('VLAN',
                         coerce=int,
                         validators=[Optional()])
    
    start_ip = StringField('Start IP',
                          validators=[DataRequired(), IPAddress()],
                          render_kw={"placeholder": "e.g., 208.76.80.4"})
    
    end_ip = StringField('End IP',
                        validators=[DataRequired(), IPAddress()],
                        render_kw={"placeholder": "e.g., 208.76.80.126"})
    
    gateway = StringField('Gateway IP',
                         validators=[Optional(), IPAddress()],
                         render_kw={"placeholder": "e.g., 208.76.80.3"})
    
    netmask = StringField('Netmask',
                         validators=[Optional()],
                         render_kw={"placeholder": "e.g., 255.255.255.128"})
    
    description = TextAreaField('Description',
                               validators=[Optional()],
                               render_kw={"placeholder": "Description of this IP range"})
    
    range_type = SelectField('Range Type',
                            choices=[('primary', 'Primary'), 
                                   ('secondary', 'Secondary')],
                            default='primary')
    
    status = SelectField('Status',
                        choices=[('active', 'Active'),
                               ('reserved', 'Reserved'),
                               ('deprecated', 'Deprecated')],
                        default='active')
    
    create_ips = BooleanField('Create individual IP records', default=True)
    
    submit = SubmitField('Add IP Range')
    
    def validate_end_ip(self, field):
        """Ensure end IP is after start IP"""
        if self.start_ip.data and field.data:
            try:
                start = ipaddress.ip_address(self.start_ip.data)
                end = ipaddress.ip_address(field.data)
                if end <= start:
                    raise ValidationError('End IP must be after Start IP')
            except ValueError:
                pass  # Let the IPAddress validator handle this

# ========== IP ASSIGNMENT FORM ==========

class IPAssignmentForm(FlaskForm):
    """
    Form for assigning an IP to a device
    This is the KEY form that prevents duplicates!
    """
    ip_address = StringField('IP Address',
                           validators=[DataRequired(), IPAddress()],
                           render_kw={"placeholder": "e.g., 208.76.80.45"})
    
    device_type = SelectField('Device Type',
                            choices=[
                                ('server', 'Physical Server'),
                                ('vps', 'Virtual Private Server'),
                                ('hypervisor', 'Hypervisor'),
                                ('switch', 'Switch'),
                                ('router', 'Router'),
                                ('firewall', 'Firewall'),
                                ('pdu', 'PDU'),
                                ('ipmi', 'IPMI/Management'),
                                ('other', 'Other')
                            ],
                            validators=[DataRequired()])
    
    device_id = IntegerField('Device ID',
                           validators=[DataRequired()],
                           render_kw={"placeholder": "e.g., 1234"})
    
    connection_type = SelectField('Connection Type',
                                choices=[('primary', 'Primary IP'),
                                       ('addon', 'Add-on IP'),
                                       ('ipmi', 'IPMI/Management'),
                                       ('internal', 'Internal Network')],
                                default='primary')
    
    is_primary = BooleanField('Primary IP for Device')
    
    vps_hostname = StringField('VPS Hostname (if applicable)',
                             validators=[Optional()],
                             render_kw={"placeholder": "e.g., vps1234.example.com"})
    
    mac_address = StringField('MAC Address',
                            validators=[Optional(), MacAddress()],
                            render_kw={"placeholder": "00:11:22:33:44:55"})
    
    interface_name = StringField('Interface Name',
                               validators=[Optional()],
                               render_kw={"placeholder": "e.g., eth0, ens192"})
    
    notes = TextAreaField('Notes',
                         validators=[Optional()],
                         render_kw={"rows": 3})
    
    submit = SubmitField('Assign IP')

# ========== IP SEARCH FORM ==========

class IPSearchForm(FlaskForm):
    """
    Form for searching IPs
    """
    search_type = SelectField('Search By',
                            choices=[('ip', 'IP Address'),
                                   ('device', 'Device ID'),
                                   ('hostname', 'VPS Hostname'),
                                   ('mac', 'MAC Address')],
                            default='ip')
    
    search_value = StringField('Search Value',
                             validators=[DataRequired()],
                             render_kw={"placeholder": "Enter search value..."})
    
    include_history = BooleanField('Include History')
    
    submit = SubmitField('Search')

# ========== IP POOL FORM ==========

class IPPoolForm(FlaskForm):
    """
    Form for creating IP pools (for VPS auto-assignment)
    """
    name = StringField('Pool Name',
                      validators=[DataRequired()],
                      render_kw={"placeholder": "e.g., VPS Pool 1"})
    
    ip_range_id = SelectField('IP Range',
                            coerce=int,
                            validators=[DataRequired()])
    
    pool_type = SelectField('Pool Type',
                          choices=[('vps', 'VPS Pool'),
                                 ('addon', 'Add-on IPs'),
                                 ('reserved', 'Reserved Pool')],
                          default='vps')
    
    max_assignments = IntegerField('Max Assignments per Customer',
                                  default=1,
                                  validators=[Optional()])
    
    is_active = BooleanField('Active', default=True)
    
    notes = TextAreaField('Notes',
                         validators=[Optional()],
                         render_kw={"rows": 3})
    
    submit = SubmitField('Create Pool')

# ========== BULK IP ASSIGNMENT FORM ==========

class BulkAssignForm(FlaskForm):
    """
    Form for bulk IP operations
    """
    ip_range = SelectField('IP Range (Optional)',
                          coerce=int,
                          validators=[Optional()],
                          render_kw={"class": "form-select"})
    
    ip_list = TextAreaField('IP Addresses or Range',
                          validators=[DataRequired()],
                          render_kw={"rows": 10,
                                   "placeholder": "Enter IPs:\n"
                                                "- One per line: 192.168.1.10\n"
                                                "- Range: 192.168.1.10-192.168.1.20\n"
                                                "- CIDR: 192.168.1.0/28"})
    
    action = SelectField('Action',
                       choices=[('reserve', 'Reserve'),
                              ('release', 'Release'),
                              ('quarantine', 'Quarantine')],
                       validators=[DataRequired()])
    
    reason = TextAreaField('Reason/Notes',
                         validators=[DataRequired()],
                         render_kw={"rows": 3})
    
    skip_assigned = BooleanField('Skip already assigned IPs', default=True)
    
    submit = SubmitField('Execute Bulk Action')
    
    def validate_ip_list(self, field):
        """Validate bulk IP input"""
        lines = field.data.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for CIDR notation
            if '/' in line:
                try:
                    net = ipaddress.ip_network(line, strict=False)
                    # Limit size for safety
                    if net.num_addresses > 1024:
                        raise ValidationError(f'Network {line} too large. Maximum 1024 IPs at once.')
                except ValueError:
                    raise ValidationError(f'Invalid CIDR notation: {line}')
                    
            # Check for range notation
            elif '-' in line:
                try:
                    parts = line.split('-')
                    if len(parts) != 2:
                        raise ValidationError(f'Invalid range format: {line}')
                    
                    start = ipaddress.ip_address(parts[0].strip())
                    end = ipaddress.ip_address(parts[1].strip())
                    
                    if end <= start:
                        raise ValidationError(f'Invalid range: end must be after start in {line}')
                    
                    # Check size
                    if int(end) - int(start) > 1024:
                        raise ValidationError(f'Range {line} too large. Maximum 1024 IPs at once.')
                        
                except ValueError:
                    raise ValidationError(f'Invalid IP range: {line}')
                    
            # Single IP
            else:
                try:
                    ipaddress.ip_address(line)
                except ValueError:
                    raise ValidationError(f'Invalid IP address: {line}')

# ========== IP RELEASE FORM ==========

class IPReleaseForm(FlaskForm):
    """
    Form for releasing an IP (starts quarantine)
    """
    confirm = BooleanField('I understand this IP will be quarantined for 90 days',
                          validators=[DataRequired()])
    
    skip_quarantine = BooleanField('Skip quarantine (admin only)')
    
    reason = TextAreaField('Reason for release',
                          validators=[Optional()],
                          render_kw={"placeholder": "Why is this IP being released?"})
    
    submit = SubmitField('Release IP')

# ========== NETWORK EDIT FORM ==========

class NetworkEditForm(NetworkForm):
    """
    Form for editing existing networks
    Inherits from NetworkForm but changes submit button
    """
    submit = SubmitField('Update Network')

# ========== VLAN EDIT FORM ==========

class VLANEditForm(VLANForm):
    """
    Form for editing existing VLANs
    """
    submit = SubmitField('Update VLAN')

# ========== END OF IPAM FORMS ===========