#!/usr/bin/env python
### auto generate sha1: 26c6550c27d0274b9338b2b85891aeaf01146ed8

import itertools
import os.path
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), *itertools.repeat("..", 3)))

from pox.debugger.mock_socket import MockSocket
from pox.debugger.io_worker import *
from nose.tools import eq_

class IOWorkerTest(unittest.TestCase):
  def test_basic_send(self):
    i = IOWorker()
    i.send("foo")
    self.assertTrue(i.ready_to_send)
    self.assertEqual(i.send_buf, "foo")
    i.consume_send_buf(3)
    self.assertFalse(i.ready_to_send)

  def test_basic_receive(self):
    i = IOWorker()
    self.data = None
    def d(worker, new_data):
      self.data = new_data
    i.on_data_receive = d
    i.push_receive_data("bar")
    self.assertEqual(self.data, "bar")
    # d does not consume the data
    i.push_receive_data("hepp")
    self.assertEqual(self.data, "barhepp")

  def test_receive_consume(self):
    i = IOWorker()
    self.data = None
    def consume(worker, new_data):
      self.data = new_data
      worker.consume_receive_buf(len(new_data))
    i.on_data_receive = consume
    i.push_receive_data("bar")
    self.assertEqual(self.data, "bar")
    # data has been consumed
    i.push_receive_data("hepp")
    self.assertEqual(self.data, "hepp")

class RecocoIOLoopTest(unittest.TestCase):
  def test_basic(self):
    loop = RecocoIOLoop()
    (left, right) = MockSocket.pair()
    loop.create_worker_for_socket(left)

  def test_stop(self):
    loop = RecocoIOLoop()
    loop.stop()

  def test_run(self):
    loop = RecocoIOLoop()
    (left, right) = MockSocket.pair()
    worker = loop.create_worker_for_socket(left)

    # callback for ioworker to record receiving
    self.received = None
    def r(worker, data):
      self.received = data
    worker.on_data_receive = r

    # 'start' the run (dark generator magic here). Does not actually execute run, but 'yield' a generator
    g = loop.run()
    # g.next() will call it, and get as far as the 'yield select'
    select = g.next()

    # send data on other socket half
    right.send("hallo")

    # now we emulate the return value of the select ([rlist],[wlist], [elist])
    g.send(([worker], [], []))

    # that should result in the socket being red the data being handed
    # to the ioworker, the callback being called. Everybody happy.
    self.assertEquals(self.received, "hallo")
