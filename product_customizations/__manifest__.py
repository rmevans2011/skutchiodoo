# -*- coding: utf-8 -*-
{
    'name': "product_customizations",

    'summary': """
        Module to add customizations to products and their attributes""",

    'description': """
        Module to add customizations to products and their attributes
    """,

    'author': "Skutchi Designs",
    'website': "http://www.skutchi.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.5',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'sale',
                'mail'],

    # always loaded
    'data': [
        'views/product_attribute.xml',
        'views/product_template.xml'
    ],
    # only loaded in demonstration mode
    'demo': [],
    'application': True,
    'installable': True
}
