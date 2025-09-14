"""
File: forms/ipam_forms.py
Purpose: Form definitions for IP Address Management module
Created: 2025-01-14
Author: DCMS Team

Revision History:
- 2025-01-14: Initial creation with all IPAM forms
             Network, VLAN, IP Range, Assignment forms
             Validation to prevent duplicate IPs
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, IntegerField, SelectField, BooleanField, 
    TextAreaField, DecimalField, SubmitField, ValidationError
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
    
    submit = SubmitField('Add VLAN')
    
    def validate_vlan_number(self, field):
        """Validate VLAN number range"""
        if field.data < 1 or field.data > 4094:
            raise ValidationError('VLAN number must be between 1 and 4094')

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
    
    range_type = SelectField('Range Type',
                            choices=[('primary', 'Primary'), 
                                   ('secondary', 'Secondary')],
                            default='primary')
    
    status = SelectField('Status',
                        choices=[('active', 'Active'),
                               ('reserved', 'Reserved'),
                               ('deprecated', 'Deprecated'),
                               ('not_in_use', 'Not In Use')],
                        default='active')
    
    description = TextAreaField('Description',
                               validators=[Optional()])
    
    create_ips = BooleanField('Pre-create all IP addresses in range', default=True)
    
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
                pass  # Let the IPAddress validator handle format errors

# ========== IP ASSIGNMENT FORM ==========

class IPAssignmentForm(FlaskForm):
    """
    Form for assigning an IP to a device
    The form that kills "ping and pray"!
    """
    ip_address = StringField('IP Address',
                           validators=[DataRequired(), IPAddress()],
                           render_kw={"placeholder": "e.g., 208.76.80.5"})
    
    device_type = SelectField('Device Type',
                            choices=[
                                ('', '-- Select Type --'),
                                ('server', 'Physical Server'),
                                ('vps', 'VPS Instance'),
                                ('hypervisor', 'VPS Hypervisor'),
                                ('switch', 'Network Switch'),
                                ('router', 'Router'),
                                ('firewall', 'Firewall'),
                                ('pdu', 'PDU'),
                                ('ipmi', 'IPMI Interface'),
                                ('other', 'Other')
                            ],
                            validators=[DataRequired()])
    
    device_id = IntegerField('Device ID',
                           validators=[DataRequired()],
                           render_kw={"placeholder": "Device ID from system"})
    
    is_primary = BooleanField('Primary IP for this device')
    
    # Optional fields
    interface_name = StringField('Interface Name',
                                validators=[Optional()],
                                render_kw={"placeholder": "e.g., eth0, bond0"})
    
    mac_address = StringField('MAC Address',
                            validators=[Optional()],
                            render_kw={"placeholder": "00:11:22:33:44:55"})
    
    vps_hostname = StringField('VPS Hostname',
                              validators=[Optional()],
                              render_kw={"placeholder": "e.g., server.example.com"})
    
    ptr_record = StringField('PTR Record',
                           validators=[Optional()],
                           render_kw={"placeholder": "Reverse DNS hostname"})
    
    notes = TextAreaField('Notes',
                         validators=[Optional()],
                         render_kw={"placeholder": "Additional notes about this assignment"})
    
    submit = SubmitField('Assign IP Address')
    
    def validate_mac_address(self, field):
        """Validate MAC address format if provided"""
        if field.data:
            # Accept common MAC formats
            mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
            if not mac_pattern.match(field.data):
                raise ValidationError('Invalid MAC address format. Use XX:XX:XX:XX:XX:XX')

# ========== IP SEARCH FORM ==========

class IPSearchForm(FlaskForm):
    """
    Simple form for IP lookups
    """
    ip_address = StringField('IP Address',
                           validators=[DataRequired(), IPAddress()],
                           render_kw={"placeholder": "Enter IP to search"})
    
    submit = SubmitField('Search')

# ========== IP POOL FORM ==========

class IPPoolForm(FlaskForm):
    """
    Form for managing VPS IP pools
    """
    name = StringField('Pool Name',
                      validators=[DataRequired()],
                      render_kw={"placeholder": "e.g., vps14"})
    
    vlan_id = SelectField('VLAN',
                         coerce=int,
                         validators=[DataRequired()])
    
    description = TextAreaField('Description',
                               validators=[Optional()],
                               render_kw={"placeholder": "VPS pool for hypervisor 14"})
    
    is_active = BooleanField('Active', default=True)
    
    submit = SubmitField('Create Pool')

# ========== BULK ASSIGNMENT FORM ==========

class BulkAssignForm(FlaskForm):
    """
    Form for bulk IP assignments
    When someone needs an entire /24!
    """
    ip_range = StringField('IP Range',
                          validators=[DataRequired()],
                          render_kw={"placeholder": "e.g., 192.168.1.0/24 or 192.168.1.1-192.168.1.10"})
    
    device_type = SelectField('Device Type',
                            choices=[
                                ('server', 'Physical Server'),
                                ('vps', 'VPS Instance'),
                                ('hypervisor', 'VPS Hypervisor'),
                                ('other', 'Other')
                            ],
                            validators=[DataRequired()])
    
    device_id = IntegerField('Device ID',
                           validators=[DataRequired()],
                           render_kw={"placeholder": "Device ID to assign all IPs to"})
    
    notes = TextAreaField('Notes',
                         validators=[Optional()],
                         render_kw={"placeholder": "Reason for bulk assignment"})
    
    skip_unavailable = BooleanField('Skip unavailable IPs', default=True)
    
    submit = SubmitField('Bulk Assign IPs')
    
    def validate_ip_range(self, field):
        """Validate range format"""
        if '/' in field.data:
            # CIDR notation
            try:
                net = ipaddress.ip_network(field.data, strict=False)
                if net.num_addresses > 1024:
                    raise ValidationError('Range too large. Maximum 1024 IPs at once.')
            except ValueError:
                raise ValidationError('Invalid CIDR notation')
        elif '-' in field.data:
            # Range notation
            try:
                parts = field.data.split('-')
                if len(parts) != 2:
                    raise ValidationError('Invalid range format')
                
                start = ipaddress.ip_address(parts[0].strip())
                end = ipaddress.ip_address(parts[1].strip())
                
                if end <= start:
                    raise ValidationError('End IP must be after start IP')
                
                # Check size
                if int(end) - int(start) > 1024:
                    raise ValidationError('Range too large. Maximum 1024 IPs at once.')
                    
            except ValueError:
                raise ValidationError('Invalid IP range format')
        else:
            raise ValidationError('Use CIDR (192.168.1.0/24) or range (192.168.1.1-192.168.1.10) format')

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

# ========== END OF IPAM FORMS ==========