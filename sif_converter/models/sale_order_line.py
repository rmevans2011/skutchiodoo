# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    custom_notes = fields.Text(string="Custom Notes")
    display_description = fields.Text(string="Display Description")