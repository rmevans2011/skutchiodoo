# -*- coding: utf-8 -*-
{
    'name': "sif_converter",

    'summary': """
        Module to convert sif files to an estimate""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'sale',
                'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/import_job.xml',
        'views/sale.xml'
    ],
    # only loaded in demonstration mode
    'demo': [],
}
