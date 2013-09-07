# -*- coding: utf-8 -*-

import unittest

from zope import interface
from zope.component import queryUtility
from AccessControl import Unauthorized

from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import logout

from collective.tablepage.interfaces import IDataStorage
from collective.tablepage.testing import TABLE_PAGE_INTEGRATION_TESTING

class SecurityTestCase(unittest.TestCase):
    
    layer = TABLE_PAGE_INTEGRATION_TESTING
    
    def setUp(self):
        portal = self.layer['portal']
        wtool = portal.portal_workflow
        login(portal, 'user1')
        portal.invokeFactory(type_name='TablePage', id='table_page', title="The Table Document")
        tp = portal.table_page
        tp.edit(textBefore='<p>Lorem Ipsum</p>',
                pageColumns=[{'id': 'col_a', 'label': 'Col A', 'description': 'Description',
                              'type': 'String', 'vocabulary': ''}])
        login(portal, TEST_USER_NAME)
        wtool.doActionFor(tp, 'publish')

    def test_base_access(self):
        portal = self.layer['portal']
        tp = portal.table_page
        # Member can access the tablepage but not the edit-table view
        login(portal, 'user0')
        self.assertTrue('Lorem Ipsum' in tp())
        self.assertRaises(Unauthorized, tp.restrictedTraverse, '@@tablepage-edit')
        # Contributor can do both
        login(portal, 'user1')
        self.assertTrue('Lorem Ipsum' in tp())
        self.assertTrue('Add new row' in tp.restrictedTraverse('@@tablepage-edit')())

    def test_add_row(self):
        portal = self.layer['portal']
        tp = portal.table_page
        # every contributor (owner or not) can add new rows
        login(portal, 'user1')
        self.assertTrue('New row' in tp.restrictedTraverse('@@edit-record')())

    def test_modify_my_row(self):
        portal = self.layer['portal']
        tp = portal.table_page
        storage = IDataStorage(tp)
        storage.add({'__creator__': 'user1', 'col_a': 'foo data from user1'})
        # user1 can modify it's own data
        login(portal, 'user1')
        view = tp.restrictedTraverse('@@edit-record')
        view.request.form['row-index'] = 0
        self.assertTrue('Edit row' in view())
        self.assertTrue('foo data from user1' in view())

    def test_modify_his_row(self):
        portal = self.layer['portal']
        tp = portal.table_page
        storage = IDataStorage(tp)
        storage.add({'__creator__': 'user1', 'col_a': 'foo data from user1'})
        # user2 can't modify other user's data
        login(portal, 'user2')
        view = tp.restrictedTraverse('@@edit-record')
        view.request.form['row-index'] = 0
        self.assertRaises(Unauthorized, view)

    def test_editor_modify_his_row(self):
        portal = self.layer['portal']
        tp = portal.table_page
        storage = IDataStorage(tp)
        storage.add({'__creator__': 'user1', 'col_a': 'foo data from user1'})
        # user3 can modify other user's data
        login(portal, 'user3')
        view = tp.restrictedTraverse('@@edit-record')
        view.request.form['row-index'] = 0
        self.assertTrue('Edit row' in view())
        self.assertTrue('foo data from user1' in view())

    def test_move_my_row(self):
        portal = self.layer['portal']
        tp = portal.table_page
        storage = IDataStorage(tp)
        storage.add({'__creator__': 'user1', 'col_a': 'foo data from user1'})
        storage.add({'__creator__': 'user1', 'col_a': 'some other futile data'})
        # owners normally can't move rows
        login(portal, 'user1')
        self.assertRaises(Unauthorized, tp.restrictedTraverse, '@@move-record')

    def test_editor_move_his_row(self):
        portal = self.layer['portal']
        tp = portal.table_page
        storage = IDataStorage(tp)
        storage.add({'__creator__': 'user1', 'col_a': 'foo data from user1'})
        storage.add({'__creator__': 'user1', 'col_a': 'some other futile data'})
        # editor can move rows
        login(portal, 'user3')
        view = tp.restrictedTraverse('@@move-record')
        view.request.form['row-index'] = 0
        view.request.form['direction'] = 'down'
        view()
        self.assertEqual(storage[0].get('col_a'), 'some other futile data')

    def test_delete_my_row(self):
        portal = self.layer['portal']
        tp = portal.table_page
        storage = IDataStorage(tp)
        storage.add({'__creator__': 'user1', 'col_a': 'foo data from user1'})
        # owners can delete proper rows
        login(portal, 'user1')
        view = tp.restrictedTraverse('@@delete-record')
        view.request.form['row-index'] = 0
        view()
        self.assertEqual(len(storage), 0)
