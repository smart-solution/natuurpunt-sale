# -*- encoding: utf-8 -*-
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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class sale_order(osv.osv):
    _inherit = "sale.order"

    def create_print_quotation(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'sale.order', ids[0], 'quotation_sent', cr)
        datas = {
          'model': 'sale.order',
          'ids': ids,
          'form': self.read(cr, uid, ids[0], context=context),
        }
        return {'type': 'ir.actions.report.xml', 'report_name': 'natuurpunt.sale.order', 'datas': datas, 'nodestroy': True}  

    def print_quotation(self, cr, uid, ids, context=None):
        '''
        This function prints the sales order and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        report = self.create_print_quotation(cr, uid, ids, context=context)
        for so in self.browse(cr,uid,ids):
            if so.email_attachments:
                feedback = 'Verkoop order met extra bijlagen!'
                return self.pool.get('print.quotation.feedback').info(cr, uid, title='Afdrukken', message=feedback, sale_order_id=ids[0])
            else:
                return self.create_print_quotation(cr, uid, ids, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
