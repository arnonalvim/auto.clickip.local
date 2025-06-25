from flask import Flask
from .auth import auth_bp

from .dmos.downstream_fec import downstream_fec_bp
from .dmos.shutdown_gpon import shutdown_gpon_bp
from .dmos.reset_onus_gpon import reset_onus_gpon_bp
from .dmos.get_mpls_brief import get_mpls_brief_bp
from .dmos.vlan_config import vlan_config_bp
from .dmos.mpls_l2vpn_tunnel import mpls_l2vpn_tunnel_bp

from .junos.interface_dhcp import int_dhcp_bp
from .junos.bgp_manager import bgp_manager_bp
from .junos.get_interface_ae0_config import int_conf_bp
from .junos.get_interface_ae0_summary import int_summary_bp
from .junos.interface_static_router import int_static_route_bp
from .junos.set_policy_whitelist import set_policy_whitelist_bp
from .junos.set_interface_ae0_unit_vlan import set_interface_ae0_unit_vlan_bp


def register_blueprints(app: Flask):
    app.register_blueprint(auth_bp, url_prefix='/auth')

    app.register_blueprint(downstream_fec_bp, url_prefix='/network')
    app.register_blueprint(shutdown_gpon_bp, url_prefix='/network')
    app.register_blueprint(reset_onus_gpon_bp, url_prefix='/network')
    app.register_blueprint(get_mpls_brief_bp, url_prefix='/network')
    app.register_blueprint(vlan_config_bp, url_prefix='/network')
    app.register_blueprint(mpls_l2vpn_tunnel_bp, url_prefix='/network')
    app.register_blueprint(int_conf_bp, url_prefix='/network')
    app.register_blueprint(int_dhcp_bp, url_prefix='/network')
    app.register_blueprint(int_summary_bp, url_prefix='/network')
    app.register_blueprint(bgp_manager_bp, url_prefix='/network')
    app.register_blueprint(int_static_route_bp, url_prefix='/network')
    app.register_blueprint(set_policy_whitelist_bp, url_prefix='/network')
    app.register_blueprint(set_interface_ae0_unit_vlan_bp, url_prefix='/network')
