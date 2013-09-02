# No shebang line, this module is meant to be imported
#
# Copyright 2013 Oliver Palmer
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os import urandom
from random import randint, choice
from binascii import b2a_hex
from sqlalchemy.types import Integer, BigInteger
from sqlalchemy.exc import StatementError
from netaddr.ip import IPAddress

from utcore import ModelTestCase
from pyfarm.models.core.cfg import TABLE_PREFIX
from pyfarm.models.core.app import db
from pyfarm.models.core.types import (
    IPv4Address as IPv4AddressType,
    JSONDict as JSONDictType,
    JSONList as JSONListType,
    JSONSerializable)


class JSONDictModel(db.Model):
    __tablename__ = "%s_jsondict_model_test" % TABLE_PREFIX
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    data = db.Column(JSONDictType)


class JSONListModel(db.Model):
    __tablename__ = "%s_jsonlist_model_test" % TABLE_PREFIX
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    data = db.Column(JSONListType)


class IPv4AddressModel(db.Model):
    __tablename__ = "%s_ipaddress_model_test" % TABLE_PREFIX
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    data = db.Column(IPv4AddressType)


class JSONDict(JSONDictModel):
    def __init__(self, data):
        self.data = data


class JSONList(JSONListModel):
    def __init__(self, data):
        self.data = data


class IPv4Address(IPv4AddressModel):
    def __init__(self, data):
        self.data = data


class TestJsonTypes(ModelTestCase):
    def test_types_notimplemented(self):
        class TestType(JSONSerializable):
            pass

        with self.assertRaises(NotImplementedError):
            TestType()

    def test_dict(self):
        for test_type in JSONDictType.serialize_types:
            for i in xrange(10):
                test_data = test_type({
                    "str": b2a_hex(urandom(1024)),
                    "int": randint(-1024, 1024),
                    "list": [
                        b2a_hex(urandom(1024)), -1024, 1024, True, None],
                    "bool": choice([True, False]), "none": None,
                    "dict": {
                        "str": b2a_hex(urandom(1024)),
                        "true": True, "false": False,
                        "int": randint(-1024, 1024),
                        "list": [
                            b2a_hex(urandom(1024)), -1024, 1024, True, None]}})

                model = JSONDict(test_data)
                self.assertIsInstance(model.data, test_type)
                db.session.add(model)
                db.session.commit()
                insert_id = model.id
                db.session.remove()
                result = JSONDict.query.filter_by(id=insert_id).first()
                self.assertIsNot(model, result)
                self.assertIsInstance(model.data, dict)
                self.assertDictEqual(model.data, result.data)

    def test_dict_error(self):
        data = JSONDict([])
        db.session.add(data)

        with self.assertRaises(StatementError):
            db.session.commit()

    def test_list(self):
        for test_type in JSONListType.serialize_types:
            for i in xrange(10):
                test_data = test_type(
                    [b2a_hex(urandom(1024)), -1024, 1024, True, None])

                model = JSONList(test_data)
                self.assertIsInstance(model.data, test_type)
                db.session.add(model)
                db.session.commit()
                insert_id = model.id
                db.session.remove()
                result = JSONList.query.filter_by(id=insert_id).first()
                self.assertIsNot(model, result)
                self.assertIsInstance(model.data, list)
                self.assertListEqual(model.data, result.data)

    def test_list_error(self):
        data = JSONList({})
        db.session.add(data)

        with self.assertRaises(StatementError):
            db.session.commit()


class TestIPAddressType(ModelTestCase):
    def test_implementation(self):
        # IP addrs are a spec, we need to be specific
        self.assertIs(IPv4AddressType.impl, BigInteger)
        self.assertEqual(IPv4AddressType.MAX_INT, 4294967295)

        with self.assertRaises(ValueError):
            instance = IPv4AddressType()
            instance.checkInteger(-1)

        with self.assertRaises(ValueError):
            instance = IPv4AddressType()
            instance.checkInteger(IPv4AddressType.MAX_INT + 1)

    def test_insert_int(self):
        ipvalue = int(IPAddress("192.168.1.1"))
        model = IPv4Address(ipvalue)
        self.assertEqual(model.data, ipvalue)
        db.session.add(model)
        db.session.commit()
        insert_id = model.id
        db.session.remove()
        result = IPv4Address.query.filter_by(id=insert_id).first()
        self.assertIsInstance(result.data, IPAddress)
        self.assertEqual(int(result.data), ipvalue)

    def test_insert_string(self):
        ipvalue = "192.168.1.1"
        model = IPv4Address(ipvalue)
        self.assertEqual(model.data, ipvalue)
        db.session.add(model)
        db.session.commit()
        insert_id = model.id
        db.session.remove()
        result = IPv4Address.query.filter_by(id=insert_id).first()
        self.assertIsInstance(result.data, IPAddress)
        self.assertEqual(str(result.data), ipvalue)

    def test_insert_ipclass(self):
        ipvalue = IPAddress("192.168.1.1")
        model = IPv4Address(ipvalue)
        self.assertEqual(model.data, ipvalue)
        db.session.add(model)
        db.session.commit()
        insert_id = model.id
        db.session.remove()
        result = IPv4Address.query.filter_by(id=insert_id).first()
        self.assertIsInstance(result.data, IPAddress)
        self.assertEqual(result.data, ipvalue)