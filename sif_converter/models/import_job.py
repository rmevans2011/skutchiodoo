# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
import base64
import csv
import io
_logger = logging.getLogger(__name__)


class import_job(models.Model):
    _name = "sif_converter.import_job"
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = "Import Job"

    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    customer_name = fields.Char(string='Customer Name', required=True, translate=True, tracking=True)
    short_description = fields.Char(string="Short Description", tracking=True)
    csv_file = fields.Binary(string="CSV File")
    state = fields.Selection([
        ('new_import', 'New Import Job'), ('needs_matching', 'Needs Matching'),
        ('estimate_ready', 'Ready to Create Estimate'), ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default="new_import", string="Status", tracking=True)

    def action_confirm(self):
        self.state = 'needs_matching'

    def action_estimate(self):
        self.state = 'estimate_ready'

    def action_reset(self):
        self.state = 'new_import'

    def action_cancel(self):
        self.state = 'cancel'

    @api.model
    def create(self, vals):
        _logger.info("Saved import_job")
        _logger.info(self.customer_id)
        _logger.info(self.customer_name)
        _logger.info(self.csv_file)
        _logger.info("=======Logging Vals=======")
        _logger.info(vals['csv_file'])
        decoded_csv_file = base64.b64decode(vals['csv_file'])
        data = io.StringIO(decoded_csv_file.decode("ANSI", 'repalce'))
        csv_reader = csv.reader(data)
        for row in csv_reader:
            _logger.info(row)

        return super(import_job, self).create(vals)
