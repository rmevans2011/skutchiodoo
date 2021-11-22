from odoo import api, fields, models


class product_product(models.Model):
    _inherit = "product.product"

    def name_get(self):
        product_list = []
        for product in self:
            name = ""
            if product.categ_id.display_name:
                name = product.categ_id.display_name + "/" + product.name
            else:
                name = product.name
            product_list.append((product.id, name))
