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

{
    "name" : "natuurpunt_sale_cmis",
    "version" : "1.0",
    "author" : "Natuurpunt (joeri.belis@natuurpunt.be)",
    "website" : "www.natuurpunt.be",
    "category" : "Sale",
    "description": """
    Custom CMIS support for natuurpunt sale:
    - via mail
    - via cmis alfresco
    - via report
""",
    "depends" : ["natuurpunt_account","natuurpunt_purchase_mail","natuurpunt_sale"],
    "data": ["natuurpunt_sale_cmis_view.xml",
             "natuurpunt_sale_report.xml",
             "security/ir.model.access.csv"],
    "init_xml" : [],
    "update_xml" : [],
    "active": False,
    "installable": True
}
