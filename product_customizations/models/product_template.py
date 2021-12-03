import itertools
import logging
from collections import defaultdict

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    variant_sku = fields.Char(string="Variant SKU")
    box_length = fields.Char(string="Box Length", required=True, default="0")
    box_width = fields.Char(string="Box Width", required=True, default="0")
    box_height = fields.Char(string="Box Height", required=True, default="0")
    product_length = fields.Char(string="Product Length", required=True, default="0")
    product_width = fields.Char(string="Product Width", required=True, default="0")
    product_height = fields.Char(string="Product Height", required=True, default="0")
    product_weight = fields.Integer(string="Product Weight", required=True, default=0)
    base_description = fields.Text(string="Base Desccription", required=True, default="0")
    hide_description = fields.Boolean(string="Hide Description", default=False)

    def _compute_variant_sku(self):
        self.variant_sku = self.default_code

    def _create_variant_ids(self):
        self.flush()
        Product = self.env["product.product"]

        variants_to_create = []
        variants_to_activate = Product
        variants_to_unlink = Product

        for tmpl_id in self:
            lines_without_no_variants = tmpl_id.valid_product_template_attribute_line_ids._without_no_variant_attributes()

            all_variants = tmpl_id.with_context(active_test=False).product_variant_ids.sorted(
                lambda p: (p.active, -p.id))

            current_variants_to_create = []
            current_variants_to_activate = Product

            # adding an attribute with only one value should not recreate product
            # write this attribute on every product to make sure we don't lose them
            single_value_lines = lines_without_no_variants.filtered(
                lambda ptal: len(ptal.product_template_value_ids._only_active()) == 1)
            if single_value_lines:
                for variant in all_variants:
                    combination = variant.product_template_attribute_value_ids | single_value_lines.product_template_value_ids._only_active()
                    # Do not add single value if the resulting combination would
                    # be invalid anyway.
                    if (
                            len(combination) == len(lines_without_no_variants) and
                            combination.attribute_line_id == lines_without_no_variants
                    ):
                        variant.product_template_attribute_value_ids = combination

            # Set containing existing `product.template.attribute.value` combination
            existing_variants = {
                variant.product_template_attribute_value_ids: variant for variant in all_variants
            }

            # Determine which product variants need to be created based on the attribute
            # configuration. If any attribute is set to generate variants dynamically, skip the
            # process.
            # Technical note: if there is no attribute, a variant is still created because
            # 'not any([])' and 'set([]) not in set([])' are True.
            if not tmpl_id.has_dynamic_attributes():
                # Iterator containing all possible `product.template.attribute.value` combination
                # The iterator is used to avoid MemoryError in case of a huge number of combination.
                all_combinations = itertools.product(*[
                    ptal.product_template_value_ids._only_active() for ptal in lines_without_no_variants
                ])
                # For each possible variant, create if it doesn't exist yet.
                for combination_tuple in all_combinations:
                    combination = self.env['product.template.attribute.value'].concat(*combination_tuple)
                    if combination in existing_variants:
                        current_variants_to_activate += existing_variants[combination]
                    else:
                        current_variants_to_create.append(tmpl_id._prepare_variant_values(combination))
                        if len(current_variants_to_create) > 100000:
                            raise UserError(_(
                                'The number of variants to generate is too high. '
                                'You should either not generate variants for each combination or generate them on demand from the sales order. '
                                'To do so, open the form view of attributes and change the mode of *Create Variants*.'))
                variants_to_create += current_variants_to_create
                variants_to_activate += current_variants_to_activate

            else:
                for variant in existing_variants.values():
                    is_combination_possible = self._is_combination_possible_by_config(
                        combination=variant.product_template_attribute_value_ids,
                        ignore_no_variant=True,
                    )
                    if is_combination_possible:
                        current_variants_to_activate += variant
                variants_to_activate += current_variants_to_activate

            variants_to_unlink += all_variants - current_variants_to_activate

        if variants_to_activate:
            variants_to_activate.write({'active': True})
        if variants_to_create:
            Product.create(variants_to_create)
        if variants_to_unlink:
            variants_to_unlink._unlink_or_archive()

        # prefetched o2m have to be reloaded (because of active_test)
        # (eg. product.template: product_variant_ids)
        # We can't rely on existing invalidate_cache because of the savepoint
        # in _unlink_or_archive.
        self.flush()
        self.invalidate_cache()
        return True

    @api.model_create_multi
    def create(self, vals_list):
        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        for vals in vals_list:
            box_string = ''
            weight_string = ''
            product_string = ''
            if 'default_code' in vals:
                vals['variant_sku'] = vals['default_code']
            if ('product_length' in vals) & ('product_width' in vals) & ('product_height' in vals):
                if(vals['product_length'] == '0') or (vals['product_width'] == '0') or (vals['product_height'] == '0'):
                    product_string = ''
                else:
                    product_string = '\n- Product Dimensions: '+vals['product_length']+'"L x '+vals['product_width']+'"W x '+vals['product_height']+'"H'
            if ('box_length' in vals) & ('box_width' in vals) & ('box_height' in vals):
                if (vals['box_length'] == '0') or (vals['box_width'] == '0') or (vals['box_height'] == '0'):
                    box_string = ''
                else:
                    box_string = '\n- Box Dimensions: '+vals['box_length']+'"L x '+vals['box_width']+'"W x '+vals['box_height']+'"H'
            if 'product_weight' in vals:
                if(vals['product_weight'] > 0):
                    weight_string = '\n- Weight: '+str(vals['product_weight'])+'lbs.'
                else:
                    weight_string = ''
            if vals['base_description'] != '0':
                vals['description_sale'] = vals['base_description']+product_string+box_string+weight_string
            else:
                vals['description_sale'] = product_string + box_string + weight_string
            self._sanitize_vals(vals)
        templates = super(ProductTemplate, self).create(vals_list)
        if "create_product_product" not in self._context:
            templates._create_variant_ids()

        # This is needed to set given values to first variant after creation
        for template, vals in zip(templates, vals_list):
            related_vals = {}
            if vals.get('barcode'):
                related_vals['barcode'] = vals['barcode']
            if vals.get('default_code'):
                related_vals['default_code'] = vals['default_code']
            if vals.get('standard_price'):
                related_vals['standard_price'] = vals['standard_price']
            if vals.get('volume'):
                related_vals['volume'] = vals['volume']
            if vals.get('weight'):
                related_vals['weight'] = vals['weight']
            # Please do forward port
            if vals.get('packaging_ids'):
                related_vals['packaging_ids'] = vals['packaging_ids']
            if related_vals:
                template.write(related_vals)

        return templates

    def write(self, vals):
        self._sanitize_vals(vals)
        _logger.info(vals)
        _logger.info("Box Width: " + self.box_width)
        if 'uom_id' in vals or 'uom_po_id' in vals:
            uom_id = self.env['uom.uom'].browse(vals.get('uom_id')) or self.uom_id
            uom_po_id = self.env['uom.uom'].browse(vals.get('uom_po_id')) or self.uom_po_id
            if uom_id and uom_po_id and uom_id.category_id != uom_po_id.category_id:
                vals['uom_po_id'] = uom_id.id
        if ('product_length' in vals) or ('product_width' in vals) or ('product_height' in vals) \
                or ('box_length' in vals) or ('box_width' in vals) or ('box_height' in vals)\
                or ('product_weight' in vals) or ('base_description' in vals):
            if 'product_length' in vals:
                pl = vals['product_length']
            else:
                pl = self.product_length
            if 'product_width' in vals:
                pw = vals['product_width']
            else:
                pw = self.product_width
            if 'product_height' in vals:
                ph = vals['product_height']
            else:
                ph = self.product_height
            if 'box_length' in vals:
                bl = vals['box_length']
            else:
                bl = self.box_length
            if 'box_width' in vals:
                bw = vals['box_width']
            else:
                bw = self.box_width
            if 'box_height' in vals:
                bh = vals['box_height']
            else:
                bh = self.box_height
            if 'product_weight' in vals:
                wght = vals['product_weight']
            else:
                wght = self.product_weight
            if 'base_description' in vals:
                bd = vals['base_description']
            else:
                bd = self.base_description

            if (pl == '0') or (pw == '0') or (ph == '0'):
                product_string = ''
            else:
                product_string = '\n- Product Dimensions: ' + pl + '"L x ' + pw + '"W x ' + ph + '"H'
            if (bl == '0') or (bw == '0') or (bh == '0'):
                box_string = ''
            else:
                box_string = '\n- Box Dimensions: ' + bl + '"L x ' + bw + '"W x ' + bh + '"H'
            if (wght > 0):
                weight_string = '\n- Weight: ' + str(wght) + 'lbs.'
            else:
                weight_string = ''

            if bd != '0':
                vals['description_sale'] = bd + product_string + box_string + weight_string
            else:
                vals['description_sale'] = product_string + box_string + weight_string
            res = super(ProductTemplate, self).write(vals)
            self.product_variant_ids.write({})
        else:
            res = super(ProductTemplate, self).write(vals)
        if 'attribute_line_ids' in vals or (vals.get('active') and len(self.product_variant_ids) == 0):
            self._create_variant_ids()
        if 'active' in vals and not vals.get('active'):
            self.with_context(active_test=False).mapped('product_variant_ids').write({'active': vals.get('active')})
        if 'image_1920' in vals:
            self.env['product.product'].invalidate_cache(fnames=[
                'image_1920',
                'image_1024',
                'image_512',
                'image_256',
                'image_128',
                'can_image_1024_be_zoomed',
            ])
            # Touch all products that will fall back on the template field
            # This is done because __last_update is used to compute the 'unique' SHA in image URLs
            # for making sure that images are not retrieved from the browser cache after a change
            # Performance discussion outcome:
            # Actually touch all variants to avoid using filtered on the image_variant_1920 field
            self.product_variant_ids.write({})
        return res

    @api.onchange('description_sale')
    def _onchange_description_sale(self):
        _logger.info("Product_Template Sale Description Changed")