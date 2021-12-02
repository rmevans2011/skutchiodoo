# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
import base64
import xml.etree.ElementTree as ET
import io
_logger = logging.getLogger(__name__)


class import_job(models.Model):
    _name = "sif_converter.import_job"
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = "Import Job"

    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    customer_name = fields.Char(string='Customer Name', required=True, translate=True, tracking=True)
    short_description = fields.Char(string="Short Description", tracking=True)
    sif_file = fields.Binary(string="SIF File (.xml)")

    state = fields.Selection([
        ('new_import', 'New Import Job'), ('needs_matching', 'Needs Matching'),
        ('estimate_ready', 'Ready to Create Estimate'), ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default="new_import", string="Status", tracking=True)
    import_item_ids = fields.One2many('import_job.import_item.lines', 'import_job_id', string="Imported Items")
    nm_import_item_ids = fields.One2many('import_job.import_item.lines', 'import_job_id',
                                         string="Needs Matching Imported Items", compute='_compute_nm_import_item_ids')

    def _compute_nm_import_item_ids(self):
        needs_matching_items = self.env['import_job.import_item.lines'].search([('import_job_id', '=', self.id),
                                                                                ('needs_matching', '=', True)])
        self.nm_import_item_ids = needs_matching_items

    def action_confirm(self):
        order_vals = {
            'partner_id': self.customer_id.id
        }
        order = self.env['sale.order'].create(order_vals)
        line_items = self.import_item_ids
        for line_item in line_items:
            item_vals = {
                'order_id': order.id,
                'product_uom_qty': line_item.qty,
                'product_id': line_item.product_id.id
            }
            self.env['sale.order.line'].create(item_vals)
        self.state = 'needs_matching'

    def action_estimate(self):
        self.state = 'estimate_ready'

    def action_reset(self):
        self.state = 'new_import'

    def action_cancel(self):
        self.state = 'cancel'

    @api.model
    def create(self, vals):
        new_status = "estimate_ready"
        res = super(import_job, self).create(vals)

        Product = self.env['product.product']
        Matched_Product = self.env['sif_converter.matched_product']

        #Load XML File
        decoded_file = base64.b64decode(vals['sif_file'])
        tree = ET.fromstring(decoded_file)
        ns = {'ofda': 'http://www.ofdaxml.org/schema'}

        #Load Line Items
        lineItems = tree.findall('./ofda:PurchaseOrder/ofda:OrderLineItem', ns)

        for lineItem in lineItems:
            next_code = False
            add_sku = []
            enterprise_code = lineItem.find('ofda:VendorRef', ns).text
            catalog_code = lineItem.find('ofda:SpecItem/ofda:Catalog/ofda:Code', ns).text
            options = lineItem.findall('ofda:SpecItem/ofda:Option', ns)
            base_sku = lineItem.find('ofda:SpecItem/ofda:Number', ns).text
            #Build Product Line specific sku
            if (enterprise_code == 'SKU'):
                if (catalog_code == 'ECS'):
                    for option in options:
                        code = option.find('ofda:Code', ns).text
                        if (next_code):
                            next_code = False
                            add_sku.insert(0, '-' + code)
                        else:
                            if (code == 'FAB'):
                                next_code = True
                            if (code == 'PET'):
                                next_code = True
                            if (code == 'WB'):
                                add_sku.insert(0, '-WB')
                    _logger.info(base_sku + "".join(add_sku))

        import_job_id = res.id

        return res

