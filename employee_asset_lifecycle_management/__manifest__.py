
# -*- coding: utf-8 -*-

{
    'name': 'Employee Asset Lifecycle Management',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Manage the full lifecycle of physical assets assigned to employees',

    'description': """
        Employee Asset Lifecycle Management
        ====================================

        This module allows HR and Asset Managers to:

        - Register and manage physical assets
        - Assign assets to employees
        - Track asset status and condition
        - Manage asset repair requests
        - Calculate asset depreciation
        - Dispose of assets with a complete audit trail
    """,

    'author': 'Custom Development',
    'website': '',
    'license': 'LGPL-3',

    'depends': [
        'hr',
        'mail',
        'base_setup',
    ],

    'data': [
        # Security
        'security/asset_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/asset_sequence.xml',
        'data/asset_cron.xml',

        # Reports (must load before menus that reference report actions)
        'report/asset_report_templates.xml',
        'report/asset_report_actions.xml',

        # Wizards (must load before menus that reference wizard actions)
        'wizard/asset_dispose_wizard_views.xml',
        'wizard/asset_depreciation_wizard_views.xml',

        # Views - Assets
        'views/asset_asset_views.xml',
        'views/asset_assignment_views.xml',
        'views/asset_repair_views.xml',

        # Employee Inherited View
        'views/hr_employee_views.xml',

        # Menus (last — references actions from above)
        'views/asset_menu.xml',
    ],

    'demo': [
        'data/asset_demo.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,

    'images': [
        'static/description/icon.png',
    ],
}
