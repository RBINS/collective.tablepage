# -*- coding: utf-8 -*-

import unittest

from Products.CMFCore.utils import getToolByName
from collective.tablepage.interfaces import IColumnField
from collective.tablepage.interfaces import IDataStorage
from collective.tablepage.testing import TABLE_PAGE_INTEGRATION_TESTING
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from zope.component import getMultiAdapter


class ViewTestCase(unittest.TestCase):

    layer = TABLE_PAGE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)

    def test_encoding(self):
        """Be sure that we have no problems with non-ASCII chars"""
        self.portal.invokeFactory(type_name='TablePage', id='table_page', title="The Table Document")
        tp = self.portal.table_page
        tp.edit(textBefore='<p>L\xc3\xb2r\xc3\xa8m Ips\xc3\xb9m</p>',
                pageColumns=[{'id': 'col_a', 'label': 'Col A', 'description': 'Th\xc3\xacs data is futile',
                              'type': 'String', 'vocabulary': '', 'options': []}])
        storage = IDataStorage(tp)
        storage.add({'__creator__': 'user1', 'col_a': 'F\xc3\xb2\xc3\xb2 data from user1',
                     '__uuid__': 'aaa'})
        try:
            tp.getText()
        except UnicodeDecodeError:
            self.fail("getText() raised UnicodeDecodeError unexpectedly!")

    def test_selection_encoding(self):
        """Be sure that we have no problems with non-ASCII chars in vocabulary of selection field"""
        self.portal.invokeFactory(type_name='TablePage', id='table_page', title="The Table Document")
        tp = self.portal.table_page
        tp.edit(pageColumns=[{'id': 'col_a', 'label': 'Col A', 'description': '',
                              'type': 'Select', 'vocabulary': 'F\xc3\xb2\xc3\xb2\nBar\nBaz', 'options': []}])
        view = getMultiAdapter((tp, self.request), name='edit-record')
        try:
            output = view()
        except UnicodeDecodeError:
            self.fail("@@edit-record raised UnicodeDecodeError unexpectedly with vocabulary values!")
        self.assertTrue('F\xc3\xb2\xc3\xb2'.decode('utf-8') in output)

    def test_encoding_on_rendering(self):
        """Be sure that we have no problems with non-ASCII chars"""
        self.portal.invokeFactory(type_name='TablePage', id='table_page', title="The Table Document")
        tp = self.portal.table_page
        tp.edit(textBefore='<p>L\xc3\xb2r\xc3\xa8m Ips\xc3\xb9m</p>',
                pageColumns=[{'id': 'col_a', 'label': 'Col A', 'description': 'Th\xc3\xacs data is futile',
                              'type': 'String', 'vocabulary': '', 'options': []}])
        storage = IDataStorage(tp)
        storage.add({'__creator__': 'user1', 'col_a': 'F\xc3\xb2\xc3\xb2 data from user1',
                     '__uuid__': 'aaa'})
        adapter = getMultiAdapter((tp, self.request), interface=IColumnField, name=u'String')
        adapter.configuration = tp.getPageColumns()[0]
        try:
            adapter.render_edit('F\xc3\xb2\xc3\xb2 data from user1')
        except UnicodeDecodeError:
            self.fail("getText() raised UnicodeDecodeError unexpectedly!")

    def test_emtpy_table(self):
        """Prevent regression om Plone 4.2 and below: empty table should display proper message""" 
        self.portal.invokeFactory(type_name='TablePage', id='table_page', title="The Table Document")
        tp = self.portal.table_page
        tp.edit(pageColumns=[{'id': 'col_a', 'label': 'Col A', 'description': 'Th\xc3\xacs data is futile',
                              'type': 'String', 'vocabulary': '', 'options': []}])
        view = getMultiAdapter((tp, self.request), name='tablepage-edit')
        self.assertTrue('No rows' in view())

    def test_hidden_column(self):
        self.portal.invokeFactory(type_name='TablePage', id='table_page', title="The Table Document")
        tp = self.portal.table_page
        tp.edit(pageColumns=[{'id': 'col_a', 'label': 'Col A', 'description': '',
                              'type': 'String', 'vocabulary': '', 'options': []},
                             {'id': 'col_b', 'label': 'Col B', 'description': '',
                              'type': 'String', 'vocabulary': '', 'options': ['hidden']}],
                sortBy='col_b',
                sortOrder='desc')
        view = self._get_view(tp)
        self.assertEqual(view.sort_order(), 'desc')
        storage = IDataStorage(tp)
        storage.add({'__creator__': 'user1', 'col_a': 'Lorem', 'col_b': 'Ipsum', '__uuid__': 'aaa'})
        storage.add({'__creator__': 'user1', 'col_a': 'Lorem', 'col_b': 'Ipsum', '__uuid__': 'bbb'})
        storage.add({'__creator__': 'user1', 'col_a': 'Sit', 'col_b': 'Sit', '__uuid__': 'ccc'})
        out = view()
        self.assertIn('Lorem', out)
        self.assertNotIn('Ipsum', out)

    def test_sort(self):
        self.portal.invokeFactory(type_name='TablePage', id='table_page', title="The Table Document")
        tp = self.portal.table_page
        tp.edit(pageColumns=[{'id': 'col_a', 'label': 'Col A', 'description': '',
                              'type': 'String', 'vocabulary': '', 'options': []},
                             {'id': 'col_b', 'label': 'Col B', 'description': '',
                              'type': 'String', 'vocabulary': '', 'options': []}],
                sortBy='col_b',
                sortOrder='desc')
        view = self._get_view(tp)
        self.assertEqual(view.sort_by(), 1)
        self.assertEqual(view.sort_order(), 'desc')
        storage = IDataStorage(tp)
        storage.add({'__creator__': 'user1', 'col_a': 'Lorem', 'col_b': 'Lorem', '__uuid__': 'aaa'})
        storage.add({'__creator__': 'user1', 'col_a': 'Ipsum', 'col_b': 'Ipsum', '__uuid__': 'bbb'})
        storage.add({'__creator__': 'user1', 'col_a': 'Sit', 'col_b': 'Sit', '__uuid__': 'ccc'})
        out = view()
        self.assertIn('data-sort-by="1"', out)
        self.assertIn('data-sort-order="desc"', out)

    def test_sort_no_values(self):
        self.portal.invokeFactory(type_name='TablePage', id='table_page', title="The Table Document")
        tp = self.portal.table_page
        tp.edit(pageColumns=[{'id': 'col_a', 'label': 'Col A', 'description': '',
                              'type': 'String', 'vocabulary': '', 'options': []},
                             {'id': 'col_b', 'label': 'Col B', 'description': '',
                              'type': 'String', 'vocabulary': '', 'options': []}])
        view = self._get_view(tp)
        self.assertEqual(view.sort_by(), None)
        self.assertEqual(view.sort_order(), 'asc')
        storage = IDataStorage(tp)
        storage.add({'__creator__': 'user1', 'col_a': 'Lorem', 'col_b': 'Lorem', '__uuid__': 'aaa'})
        storage.add({'__creator__': 'user1', 'col_a': 'Ipsum', 'col_b': 'Ipsum', '__uuid__': 'bbb'})
        storage.add({'__creator__': 'user1', 'col_a': 'Sit', 'col_b': 'Sit', '__uuid__': 'ccc'})
        out = view()
        self.assertNotIn('data-sort-by', out)
        self.assertIn('data-sort-order="asc"', out)

    def _get_view(self, tp):
        return getMultiAdapter((tp, self.request), name='view-table')

class RefreshViewTestCase(unittest.TestCase):

    layer = TABLE_PAGE_INTEGRATION_TESTING

    def setUp(self):
        portal = self.layer['portal']
        login(portal, TEST_USER_NAME)
        portal.invokeFactory(type_name='TablePage', id='table_page', title="The Table Document")
        tp = portal.table_page
        tp.edit(pageColumns=[{'id': 'col_a', 'label': 'Col A', 'description': '',
                              'type': 'String', 'vocabulary': '', 'options': []}])
        storage = IDataStorage(tp)
        storage.add({'__creator__': 'user1', 'col_a': 'Lorem', '__uuid__': 'aaa'})
        storage.add({'__creator__': 'user1', 'col_a': 'Ipsum', '__uuid__': 'bbb'})
        storage.add({'__creator__': 'user1', 'col_a': 'Sit', '__uuid__': 'ccc'})
        self.tp_catalog = getToolByName(portal, 'tablepage_catalog')

    def test_refreshing(self):
        portal = self.layer['portal']
        request = self.layer['request']
        tp_catalog = self.tp_catalog
        self.assertEqual(len(tp_catalog.searchTablePage(portal.table_page)), 0)
        view = getMultiAdapter((portal.table_page, request), name=u'refresh-catalog')
        view()
        self.assertEqual(len(tp_catalog.searchTablePage(portal.table_page)), 3)


class DeleteViewTestCase(unittest.TestCase):

    layer = TABLE_PAGE_INTEGRATION_TESTING

    def setUp(self):
        portal = self.layer['portal']
        login(portal, TEST_USER_NAME)
        portal.invokeFactory(type_name='TablePage', id='table_page', title="The Table Document")
        tp = portal.table_page
        tp.edit(pageColumns=[{'id': 'col_a', 'label': 'Col A', 'description': '',
                              'type': 'String', 'vocabulary': '', 'options': []}])
        storage = IDataStorage(tp)
        storage.add({'__creator__': 'user1', 'col_a': 'Lorem', '__uuid__': 'aaa'})
        storage.add({'__creator__': 'user1', 'col_a': 'Ipsum', '__uuid__': 'bbb'})
        storage.add({'__creator__': 'user1', 'col_a': 'Sit', '__uuid__': 'ccc'})
        self.tp_catalog = getToolByName(portal, 'tablepage_catalog')
        self.tp_catalog.manage_catalogRebuild()

    def test_getObjPositionInParent_on_delete(self):
        # When deleting a row all following rows must update position information to fill the hole
        portal = self.layer['portal']
        request = self.layer['request']
        view = getMultiAdapter((portal.table_page, request), name=u'delete-record')
        request.form['row-index'] = 1
        view()
        results = self.tp_catalog.searchTablePage(portal.table_page)
        self.assertEqual(results[0].getObjPositionInParent, 1)
        self.assertEqual(results[1].getObjPositionInParent, 2)
