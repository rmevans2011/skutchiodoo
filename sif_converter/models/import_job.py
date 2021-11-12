# -*- coding: utf-8 -*-
from odoo import api, fields, models


class import_job(models.Model):
    _name = "sif_converter.import_job"
    _inherit = ["mail.thread"]
    _description = "Import Job"

    customer_name = fields.Char(string='Customer Name', required=True, translate=True)
    short_description = fields.Char(string="Short Description")
    