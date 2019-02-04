# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################## 

from osv import osv, fields
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from natuurpunt_tools import sql_wrapper

def get_company_id(obj,cr,uid):
    user = obj.browse(cr, uid, uid)
    return user.company_id.id

class res_partner(osv.osv):
    _inherit = 'res.partner'

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=80):
        """
        Returns a list of tupples containing id, name, as internally it is called {def name_get}
        result format: {[(id, name), (id, name), ...]}

        @param cr: A database cursor
        @param user: ID of the user currently logged in
        @param name: name to search
        @param args: other arguments
        @param operator: default operator is 'ilike', it can be changed
        @param context: context arguments, like lang, time zone
        @param limit: Returns first 'n' ids of complete result, default is 80.

        @return: Returns a list of tupples containing id and name
        """       
        if not args:
            args = []
        if context is None:
            context = {}
        ids = []
        if context and 'offerte' in context:
            sql_stat = "select distinct on (partner_id) id from sale_order where state in ('draft','sent')" + \
                       " and company_id = {}".format(get_company_id(self.pool.get('res.users'),cr,user))
            res = sql_wrapper(sql_stat)(cr)
            if res:
                quotation_ids = [x['id'] for x in res]
                for quotation in self.pool.get('sale.order').browse(cr, user, quotation_ids, context=context or {}):
                    if name.lower() in quotation.partner_id.name.lower():
                        ids.append(quotation.partner_id.id)
	elif context and 'natuurpunt_sale' in context:
            sql_stat = "select distinct on (partner_id) id from sale_order where state not in ('draft','sent','cancel')" + \
                       " and company_id = {}".format(get_company_id(self.pool.get('res.users'),cr,user))
            res = sql_wrapper(sql_stat)(cr)
            if res:
                sale_ids = [x['id'] for x in res]
                for sale in self.pool.get('sale.order').browse(cr, user, sale_ids, context=context or {}):
                    if name.lower() in sale.partner_id.name.lower():
                        ids.append(sale.partner_id.id)
	else:
            ids = self.search(cr, user, args, limit=limit, context=context or {})
        return self.name_get(cr, user, ids, context=context)

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        result = super(sale_order,self).onchange_partner_id(cr, uid, ids, partner_id, context=context)

        if partner_id:
            customer = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if not customer.is_company:
                result['value']['is_company_with_contact'] = False
            else:
                if not customer.child_ids:
                    result['value']['is_company_with_contact'] = False
                else:
                    result['value']['is_company_with_contact'] = True
            result['value']['customer_contact_id'] = False
            result['value']['use_company_address'] = False

        return result

    def onchange_customer_contact_id(self, cr, uid, ids, customer_company_id):
        """
        Reset the flag
        """
        result = {'value':{}}
        result['value']['use_company_address'] = False
        return result

    _columns = {
        'customer_contact_id': fields.many2one('res.partner', 'Contact', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},),
        'use_company_address': fields.boolean('Gebruik bedrijfsadres', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},),
        'is_company_with_contact': fields.boolean('Is company with contact'),
    }

sale_order()

class sale_order_line_make_invoice(osv.osv_memory):
    _inherit = 'sale.order.line.make.invoice'

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
         invoice_vals = super(sale_order_line_make_invoice,self)._prepare_invoice(cr, uid, order, lines, context=context)
         invoice_vals['customer_contact_id'] = order.customer_contact_id.id
         invoice_vals['use_company_address'] = order.use_company_address
         invoice_vals['is_company_with_contact'] = order.is_company_with_contact
         return invoice_vals

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
