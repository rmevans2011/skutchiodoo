# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    sort_code = fields.Char(string="Sort Code")
    sale_order_name = fields.Char(string="Sale Order Section")
