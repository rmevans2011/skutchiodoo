from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class merged_lines(models.Model):
    _name = "import_job.merged_lines"
    _description = "Merged Lines"
    _order = "category_code asc"

    import_job_id = fields.Many2one('sif_converter.import_job', string='Import Job')
    prod_id = fields.Many2one('product.product', string='Matched Product')
    custom_notes = fields.Text(string="Custom Notes 3")
    price_unit = fields.Float(string="Product Upcharge")
    category_code = fields.Char(string="Category Code")
    categ_header = fields.Char(string="Category Header")
    qty = fields.Integer(string='Quantity')