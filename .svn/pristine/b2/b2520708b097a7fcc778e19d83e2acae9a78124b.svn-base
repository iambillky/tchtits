"""
File: forms/network_device_forms.py
Purpose: WTForms form definitions for network device management
Version: 1.0.0
Author: iambilky

Revision History:
- v1.0.0: Initial creation with NetworkDeviceForm
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, IPAddress, ValidationError
import re

# ========== CUSTOM VALIDATORS ==========

def validate_identifier(form, field):
    """
    Validate identifier follows the naming convention
    Examples: INT5, DISTRO5, INT1051, CORE, PRIVCORE
    """
    if field.data:
        # Allow CORE, PRIVCORE, or pattern like INT/DISTRO + numbers
        pattern = r'^(CORE|PRIVCORE|INT\d+|DISTRO\d+|[A-Z]+\d*)$'
        if not re.match(pattern, field.data.upper()):
            raise ValidationError('Invalid identifier format. Use INT5, DISTRO5, CORE, etc.')

def validate_hostname(form, field):
    """
    Validate hostname follows the naming convention
    Example: TCH-SFJ-INT5
    """
    if field.data:
        # Basic pattern: COMPANY-DC-IDENTIFIER
        pattern = r'^[A-Z]+-[A-Z]+-[A-Z0-9]+$'
        if not re.match(pattern, field.data.upper()):
            raise ValidationError('Invalid hostname format. Use format like TCH-SFJ-INT5')

# ========== FORM DEFINITIONS ==========

class NetworkDeviceForm(FlaskForm):
    """
    Form for adding/editing network devices
    Simplified to match actual infrastructure needs
    """
    
    # ========== IDENTIFICATION ==========
    hostname = StringField('Hostname', 
                          validators=[DataRequired(), Length(max=100), validate_hostname],
                          render_kw={'placeholder': 'TCH-SFJ-INT5', 
                                   'style': 'text-transform: uppercase;'})
    
    identifier = StringField('Identifier', 
                           validators=[DataRequired(), Length(max=50), validate_identifier],
                           render_kw={'placeholder': 'INT5 (what you call it)',
                                    'style': 'text-transform: uppercase;'})
    
    # ========== DEVICE CLASSIFICATION ==========
    device_type = SelectField('Device Type',
                            choices=[
                                ('Switch', 'Switch'),
                                ('Core', 'Core Switch/Router'),
                                ('Firewall', 'Firewall'),
                                ('Load Balancer', 'Load Balancer'),
                                ('Other', 'Other')
                            ],
                            validators=[DataRequired()])
    
    device_role = SelectField('Device Role',
                            choices=[
                                ('', '-- Select Role --'),
                                ('Core', 'Core Switch/Router'),
                                ('Distribution', 'Distribution'),
                                ('Access', 'Access/TOR'),
                                ('Management', 'Management'),
                                ('Other', 'Other')
                            ],
                            validators=[Optional()])
    
    network_type = SelectField('Network Type',
                             choices=[
                                 ('private', 'Private Network (INT)'),
                                 ('public', 'Public Network (DISTRO/CORE)')
                             ],
                             validators=[DataRequired()],
                             render_kw={'onchange': 'updateNetworkTypeHint()'})
    
    # ========== HARDWARE INFO ==========
    manufacturer = SelectField('Manufacturer',
                              choices=[
                                  ('', '-- Select Manufacturer --'),
                                  ('Cisco', 'Cisco'),
                                  ('Arista', 'Arista'),
                                  ('Juniper', 'Juniper'),
                                  ('HP', 'HP/Aruba'),
                                  ('Dell', 'Dell'),
                                  ('Netgear', 'Netgear'),
                                  ('Other', 'Other')
                              ],
                              validators=[Optional()])
    
    model = StringField('Model', 
                       validators=[Optional(), Length(max=100)],
                       render_kw={'placeholder': 'Catalyst 2960, Nexus 9000, etc.'})
    
    serial_number = StringField('Serial Number', 
                              validators=[Optional(), Length(max=100)],
                              render_kw={'placeholder': 'Optional'})
    
    # ========== SOFTWARE ==========
    software_version = StringField('Software Version', 
                                  validators=[Optional(), Length(max=100)],
                                  render_kw={'placeholder': '15.2(7)E3, 9.3(8), etc.'})
    
    # ========== PHYSICAL LOCATION ==========
    # Rack will be a SelectField populated dynamically in the route
    rack_id = SelectField('Rack Location',
                         coerce=int,
                         validators=[DataRequired()])
    
    start_u = IntegerField('Starting U Position', 
                          validators=[DataRequired(), NumberRange(min=1, max=50)],
                          render_kw={'placeholder': '42 (top of rack)'})
    
    size_u = IntegerField('Size (in U)', 
                         validators=[DataRequired(), NumberRange(min=1, max=10)],
                         default=1,
                         render_kw={'placeholder': '1'})
    
    # ========== NETWORK INFO ==========
    management_ip = StringField('Management IP', 
                               validators=[Optional(), IPAddress(ipv4=True, ipv6=False)],
                               render_kw={'placeholder': '10.10.5.236'})
    
    port_count = IntegerField('Port Count', 
                            validators=[Optional(), NumberRange(min=1, max=96)],
                            render_kw={'placeholder': '24, 48, etc.'})
    
    # ========== POWER CONFIGURATION ==========
    # PDU fields will be SelectFields populated dynamically in the route
    pdu_1_id = SelectField('Primary PDU',
                          coerce=int,
                          validators=[Optional()])
    
    pdu_1_outlet = IntegerField('Primary PDU Outlet', 
                               validators=[Optional(), NumberRange(min=1, max=48)],
                               render_kw={'placeholder': 'Outlet number'})
    
    pdu_2_id = SelectField('Redundant PDU (optional)',
                          coerce=int,
                          validators=[Optional()])
    
    pdu_2_outlet = IntegerField('Redundant PDU Outlet', 
                               validators=[Optional(), NumberRange(min=1, max=48)],
                               render_kw={'placeholder': 'Outlet number'})
    
    power_consumption = FloatField('Power Consumption (Watts)', 
                                  validators=[Optional(), NumberRange(min=0)],
                                  render_kw={'placeholder': '150'})
    
    # ========== STATUS ==========
    status = SelectField('Status',
                        choices=[
                            ('active', 'Active'),
                            ('spare', 'Spare'),
                            ('failed', 'Failed'),
                            ('maintenance', 'Maintenance')
                        ],
                        default='active',
                        validators=[DataRequired()])
    
    # ========== NOTES ==========
    notes = TextAreaField('Notes', 
                         validators=[Optional()],
                         render_kw={'rows': 3, 
                                  'placeholder': 'Any additional notes about this device'})
    
    def validate(self, **kwargs):
        """
        Custom validation to ensure network type matches identifier
        """
        # First run standard validation
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        
        # Check if identifier matches network type
        if self.identifier.data and self.network_type.data:
            identifier_upper = self.identifier.data.upper()
            
            # Private network identifiers
            if self.network_type.data == 'private':
                if not (identifier_upper.startswith('INT') or 
                       identifier_upper == 'PRIVCORE' or
                       identifier_upper.startswith('PRIV')):
                    self.identifier.errors.append(
                        'Private network devices should use INT or PRIV prefix'
                    )
                    return False
            
            # Public network identifiers  
            elif self.network_type.data == 'public':
                if identifier_upper.startswith('INT') or identifier_upper.startswith('PRIV'):
                    self.identifier.errors.append(
                        'Public network devices should use DISTRO or CORE prefix'
                    )
                    return False
        
        # Check redundant PDU configuration
        if self.pdu_2_id.data and not self.pdu_1_id.data:
            self.pdu_2_id.errors.append('Cannot set redundant PDU without primary PDU')
            return False
        
        if self.pdu_2_outlet.data and not self.pdu_2_id.data:
            self.pdu_2_outlet.errors.append('Select a redundant PDU first')
            return False
        
        return True