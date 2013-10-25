# -*- coding: utf-8 -*-

from AccessControl import getSecurityManager
from Products.Five.browser import BrowserView
from collective.tablepage import config
from collective.tablepage import tablepageMessageFactory
from collective.tablepage.interfaces import IColumnField
from collective.tablepage.interfaces import IDataStorage
from plone.memoize.view import memoize
from zope.component import getMultiAdapter


class TableViewView(BrowserView):
    """Render only the table"""
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.datagrid = context.getField('pageColumns')
        self.edit_mode = False

    def __call__(self):
        storage = IDataStorage(self.context)
        if not self.edit_mode and len(storage)==0:
            return ""
        return self.index()

    def showHeaders(self):
        """Logic for display table headers"""
        show_headers_options = self.context.getShowHeaders()
        if show_headers_options and show_headers_options!='always':
            if show_headers_options=='view_only' and self.edit_mode:
                return False
            if show_headers_options=='edit_only' and not self.edit_mode:
                return False
        return True

    def headers(self):
        data = self.datagrid.get(self.context)
        results = []
        for d in data:
            if not d:
                continue
            results.append(dict(label=tablepageMessageFactory(d['label'].decode('utf-8')),
                                description=tablepageMessageFactory(d.get('description', '').decode('utf-8')),
                                ))
        return results

    def rows(self):
        storage = IDataStorage(self.context)
        rows = []
        adapters = {}
        # let's cache adapters
        for conf in self.context.getPageColumns():
            col_type = conf['type']
            adapters[col_type] = getMultiAdapter((self.context, self.request),
                                                 IColumnField, name=col_type)
        for record in storage:
            row = []
            for conf in self.context.getPageColumns():
                field = adapters[conf['type']]
                row.append(field.render_view(record.get(conf['id'])))
            rows.append(row)
        return rows

    @memoize
    def portal_url(self):
        return getMultiAdapter((self.context, self.request), name=u'plone_portal_state').portal_url()

    @property
    @memoize
    def member(self):
        return getMultiAdapter((self.context, self.request), name=u'plone_portal_state').member()
        
    def check_tablemanager_permission(self):
        sm = getSecurityManager()
        return sm.checkPermission(config.MANAGE_TABLE, self.context)

    def mine_row(self, index):
        storage = IDataStorage(self.context)
        return storage[index]['__creator__']==self.member.getId()
