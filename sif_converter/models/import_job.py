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
    estimate_id = fields.Many2one('sale.order', string='Linked Estimate')
    #customer_name = fields.Char(string='Customer Name', required=True, translate=True, tracking=True)
    #short_description = fields.Char(string="Short Description", tracking=True)
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

    def action_create_estimate(self):
        order_vals = {
            'partner_id': self.customer_id.id
        }
        order = self.env['sale.order'].create(order_vals)
        sale_order_lines = {}
        line_items = self.import_item_ids
        for line_item in line_items:
            if(line_item.is_custom):
                if (str(line_item.product_id.id) + "p" + line_item.custom_notes in sale_order_lines):
                    sale_order_lines[str(line_item.product_id.id) + "p"]['qty'] += line_item.qty
                else:
                    product_price = self.env['product.product'].search([('id', '=', line_item.product_id.id)])
                    sale_order_lines[str(line_item.product_id.id) + "p" + line_item.custom_notes] = {
                        'import_job_id': line_item.import_job_id.id,
                        'prod_id': line_item.product_id.id,
                        'qty': line_item.qty,
                        'custom_notes': '\nCustom Modifications:\n- '+line_item.custom_notes,
                        'price_unit': product_price.list_price + line_item.upcharge_cost,
                        'category_code': line_item.product_id.categ_id.sort_code,
                        'categ_header': line_item.product_id.categ_id.sale_order_name
                    }
                    _logger.info(sale_order_lines)
            else:
                if(str(line_item.product_id.id)+"p" in sale_order_lines):
                    sale_order_lines[str(line_item.product_id.id)+"p"]['qty'] += line_item.qty
                else:
                    sale_order_lines[str(line_item.product_id.id)+"p"] = {
                        'import_job_id': line_item.import_job_id.id,
                        'prod_id': line_item.product_id.id,
                        'qty': line_item.qty,
                        'category_code': line_item.product_id.categ_id.sort_code,
                        'categ_header': line_item.product_id.categ_id.sale_order_name
                    }


        for so in sale_order_lines:
            merged_item = self.env['import_job.merged_lines'].create(sale_order_lines.get(so))
            """
            _logger.info(merged_item.id)
            item_vals = {
                'order_id': order.id,
                'product_uom_qty': sale_order_lines.get(so)['qty'],
                'product_id': sale_order_lines.get(so)['prod_id'],
            }
            if 'price_unit' in sale_order_lines.get(so):
                item_vals['price_unit'] = sale_order_lines.get(so)['price_unit']
            if 'custom_notes' in sale_order_lines.get(so):
                item_vals['custom_notes'] = sale_order_lines.get(so)['custom_notes']
            _logger.info(item_vals)
            self.env['sale.order.line'].create(item_vals)
            """

        previous_code = ""
        merged_lines = self.env['import_job.merged_lines'].search([('import_job_id', '=', self.id)])
        for mo in merged_lines:
            if(mo.category_code != previous_code):
                previous_code = mo.category_code
                self.env['sale.order.line'].create({'order_id': order.id,
                                                    'display_type': 'line_section',
                                                    'name': mo.categ_header})
            item_vals = {
                'order_id': order.id,
                'product_uom_qty': mo.qty,
                'product_id': mo.prod_id.id,
            }
            if mo.price_unit > 0:
                item_vals['price_unit'] = mo.price_unit
            if 'custom_notes':
                item_vals['custom_notes'] = mo.custom_notes
            _logger.info(item_vals)
            self.env['sale.order.line'].create(item_vals)
        self.estimate_id = order.id
        self.state = 'done'

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
        import_job_id = res.id

        Product = self.env['product.product']
        Matched_Product = self.env['sif_converter.matched_product']
        Sif_Sku = self.env['sif_converter.sif_sku']

        #Load XML File
        decoded_file = base64.b64decode(vals['sif_file'])
        tree = ET.fromstring(decoded_file)
        ns = {'ofda': 'http://www.ofdaxml.org/schema'}

        #Load Line Items
        lineItems = tree.findall('./PurchaseOrder/OrderLineItem')

        for lineItem in lineItems:
            sif_search_id = 0
            next_code = False
            custom_product = False
            custom_text = ""
            upcharge = 0
            add_sku = []
            sif_options = []
            enterprise_code = lineItem.find('VendorRef').text
            catalog_code = lineItem.find('SpecItem/Catalog/Code').text
            options = lineItem.findall('SpecItem/Option')
            base_sku = (lineItem.find('SpecItem/Number').text).upper()
            qty = lineItem.find('Quantity').text
            if enterprise_code == "SKU":
                # Skutchi Products
                _logger.info("Working On Skutchi Product")
                for option in options:
                    code = option.find('Code').text
                    if (next_code):
                        next_code = False
                        if (custom_product):
                            custom_product = False
                            custom_text = code
                        else:
                            add_sku.append('-' + code)
                            sif_options.append(code)
                    else:
                        if (code == 'FAB'):
                            next_code = True
                        elif (code == 'PET'):
                            next_code = True
                        elif (code == 'WB'):
                            add_sku.append('-WB')
                            sif_options.append("WB")
                        elif (code == "MOD-CUT"):
                            next_code = True
                            custom_product = True
                            upcharge += 50
                        else:
                            if(code == 'MOD-NO'):
                                pass
                            else:
                                add_sku.append('-'+code)
                                sif_options.append(code)
            else:
                # Other Vendors Products
                _logger.info("Working On other Products")
                for option in options:
                    code = option.find('Code').text
                    add_sku.append('-' + code)
                    sif_options.append(code)
            search_sku = base_sku + "".join(add_sku)
            sif_opts = "|".join(sif_options)
            _logger.info(search_sku)

            # create import row
            import_row_vals = {
                'import_job_id': import_job_id,
                'sif_sku': base_sku,
                'search_sku': search_sku,
                'qty': qty,
                'sif_options': sif_opts,
                'generic_code': 'need_to_remove',
                'vendor_code': enterprise_code,
                'needs_matching': False
            }

            if(custom_text != ""):
                import_row_vals['is_custom'] = True
                import_row_vals['custom_notes'] = custom_text
                import_row_vals['upcharge_cost'] = upcharge

            #Check to see if there is a sif_sku
            sifskus = Sif_Sku.search([('sif_sku', '=', base_sku)])
            for sifsku in sifskus:
                _logger.info("Searching for: " + sifsku.odoo_sku + "".join(add_sku))
                ps = Product.search([('default_code', '=', sifsku.odoo_sku + "".join(add_sku))])
                if len(ps) != 0:
                    sif_search_id = ps.id

            # Check to see if we need to search the database
            if sif_search_id != 0:
                import_row_vals['product_id'] = sif_search_id
            else:
                p_search = Product.search([('default_code', '=', search_sku)])
                if (len(p_search) == 0):
                    # No default product found search for a matched product
                    if(sif_opts == ''):
                        mp_search = Matched_Product.search([('sif_sku', '=', base_sku)])
                    else:
                        mp_search = Matched_Product.search([('sif_sku', '=', base_sku),
                                                            ('sif_options', '=', sif_opts)])
                    if (len(mp_search) == 0):
                        if (enterprise_code != "SKU"):
                            prod_cat = self.env['product.category']
                            mfg_cat = prod_cat.search([('name', '=', enterprise_code)])
                            if (len(mfg_cat) == 0):
                                vs = prod_cat.search([('name', '=', '11- Vendor Specific Products')])
                                mfg_cat = prod_cat.create({
                                    'name': enterprise_code,
                                    'parent_id': vs.id
                                })
                            _logger.info(mfg_cat.id)
                            product = self.env['product.template'].create({
                                'name': lineItem.find('SpecItem/Description').text,
                                'list_price': lineItem.find('Price/EndCustomerPrice').text,
                                'standard_price': lineItem.find('Price/OrderDealerPrice').text,
                                'default_code': search_sku,
                                'hide_description': True,
                                'categ_id': mfg_cat.id,
                                'base_description': '- Product Sku: ' + search_sku,
                                'box_length': '0',
                                'box_width': '0',
                                'box_height': '0',
                                'product_length': '0',
                                'product_height': '0',
                                'product_width': '0',
                                'product_weight': 0,
                            })
                            _logger.info(product.product_variant_id.id)
                            import_row_vals['product_id'] = product.product_variant_id.id
                        else:
                            import_row_vals['needs_matching'] = True
                            new_status = "needs_matching"
                    else:
                        import_row_vals['product_id'] = mp_search.product_id.id
                        import_row_vals['matched_product_id'] = mp_search.id
                else:
                    import_row_vals['product_id'] = p_search.id


            self.env['import_job.import_item.lines'].create(import_row_vals)


        res.state = new_status
        return res

