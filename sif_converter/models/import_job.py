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
    import_item_ids = fields.One2many('import_job.import_item.lines', 'import_job_id', string="Imported Items")

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
        # Create Import Job
        res = super(import_job, self).create(vals)
        _logger.info(res)
        _logger.info(res.id)
        import_job_id = res.id
        Product = self.env['product.template']
        Matched_Product = self.env['sif_converter.matched_product']

        #Process csv file
        decoded_csv_file = base64.b64decode(vals['csv_file'])
        data = io.StringIO(decoded_csv_file.decode("unicode_escape"))
        csv_reader = csv.reader(data)
        next(csv_reader)
        for row in csv_reader:
            _logger.info(row)
            _logger.info(row[4].split())
            _logger.info(row[5].split('|'))
            needs_matching = False

            if(len(Product.search([('default_code', '=', row[2])])) == 0):
                # Continue needs matching logic
                if(len(Matched_Product.search([('sif_sku', '=', row[2]),('sif_options', '=', row[4])])) == 0):
                    needs_matching = True


            import_row_vals = {
                'import_job_id': import_job_id,
                'sif_sku': row[2],
                'sif_options': row[4],
                'generic_code': row[32],
                'needs_matching': needs_matching
            }
            self.env['import_job.import_item.lines'].create(import_row_vals)
            _logger.info(len(self.env['product.product'].search([('default_code', '=', 'E-COM111')])))

        if not vals.get('short_description'):
            vals['short_description'] = "Some text"
        return res
