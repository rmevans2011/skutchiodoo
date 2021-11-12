# -*- coding: utf-8 -*-
from odoo import api, fields, models


class import_job(models.Model):
    _name = "sif_converter.import_job"
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = "Import Job"

    customer_name = fields.Char(string='Customer Name', required=True, translate=True)
    short_description = fields.Char(string="Short Description")
    state = fields.Selection([
        ('new_import', 'New Import Job'), ('needs_matching', 'Needs Matching'),
        ('estimate_ready', 'Ready to Create Estimate'), ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default="new_import", string="Status")

    def action_confirm(self):
        self.state = 'needs_matching'

    def action_estimate(self):
        self.state = 'estimate_ready'