import pymongo
import sys
import datetime
import bson
import re

ATOMIC_BSON_TYPES = {
    int     : 'int',
    float   : 'double', 
    str     : 'string', 
    bool    : 'boolean', 
    datetime.datetime   : 'date', 
    bson.regex.Regex    : 'regex',
    re.Pattern          : 'regex',
    bson.binary.Binary  : 'binary',
    bytes               : 'binary'
}




def mongocache(port, db_name, collection_name):
    # test connection and check if collection exists
    try:
        # create connection
        client = pymongo.MongoClient("localhost", port)

        # create database if not exists
        db = client[db_name]
    except:
        # connection failed
        # log error and disable cacheing
        mongo_collection = None
    else:
        # check if collection exists
        if collection_name in db.list_collection_names():
            mongo_collection = db[collection_name]
        else:
            mongo_collection = None


    def wrapper(func):
        def wrapped_func(*args):
            nonlocal mongo_collection, port, db_name, collection_name

            # create schema based on *args and data
            if not mongo_collection:
                # create a collection and start cacheing

                # get function output
                data = func(*args)

                # create schema from data and keys
                keys, schema = _create_schema(data, *args)

                # create collection
                mongo_collection = _create_collection(port, db_name, collection_name, keys, schema)

                # push function output to collection
            else:
                # try fetching data from database
                pass

        return wrapped_func
    return wrapper

def _create_schema_recursive(data):
    '''
        Input:
            structured data

        Return:
            schema for input object
            Keys:
            - bsonType of data
            - properties if bsonType is object or items if bsonType is array
    '''
    # check if atomic type
    if data is None:
        raise Exception("null value encountered")

    if type(data) in ATOMIC_BSON_TYPES:
        bsonType = ATOMIC_BSON_TYPES[type(data)]
        return {'bsonType': bsonType}
    elif type(data) == list:
        # get bsonType for each item
        item_bson_types = [_create_schema_recursive(item) for item in data]

        # check if bson types are all the same
        bson_type_same = all(item_bson_type['bsonType'] == item_bson_types[0]['bsonType'] for item_bson_type in item_bson_types)
        if not bson_type_same:
            raise Exception("items in array do not belong to the same BSON type")

        return {
            'bsonType'  : 'array',
            'items'     :  item_bson_types[0]
        }
    elif type(data) == dict:
        # get bson Type for each item
        properties = {key: _create_schema_recursive(val) for key, val in data.items()}

        return {
            'bsonType'  : 'object',
            'properties': properties
        }
    else:
        raise Exception(f"could not convert data of type {type(data)} into known BSON types")


def _create_schema(data, *args):
    '''
        Input:
            sample data

        Return:
            return schema based on sample entry and 
            return list of keys corresponding to list of inputs to function
    '''

    # construct entry
    entry = {}
    keys = []

    for i, arg in enumerate(args):
        entry['key_' + i] = arg
        keys.append('key_' + i)

    entry['response'] = data

    # iterate through the entry recursively to get the schema
    # throw error when an entry does not match a BSON type
    schema = _create_schema_recursive(data)

    return keys, schema

def _create_collection(port, db_name, collection_name, keys, schema):
    '''
        Input:
            - port: port id
            - db_name: name of database
            - collection_name: name of collection
            - keys: keys for creating index
            - schema: schema for collection

        Return:
            create a collection and return it
    '''
    try:
        # create database
        client = pymongo.MongoClient("localhost", port)
        db = client[db_name]

        # create collection
        if collection_name not in db.list_collection_names():
            db.create_collection(
                collection_name,
                validator = {
                    '$jsonSchema': schema
                }
            )
        collection = db[collection_name]

        # create index
        collection.create_index(keys, unique=True)
    except:
        sys.exit()
    else:
        return collection
