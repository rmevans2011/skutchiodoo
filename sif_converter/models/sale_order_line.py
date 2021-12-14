# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    custom_notes = fields.Text(string="Custom Notes")
    display_description = fields.Text(string="Display Description")

    def _compute_display_description(self):
        for rec in self:
            rec.display_description = rec.product_id.computed_description