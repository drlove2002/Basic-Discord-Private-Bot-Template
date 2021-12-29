from nextcord.enums import Enum

from . import logging
from typing import List, Optional, Dict, Any, Union, Iterator

from pymongo import UpdateOne, ReturnDocument, DeleteOne
from pymongo.errors import BulkWriteError
from pymongo.results import DeleteResult, BulkWriteResult

"""
A helper file for using mongo db
Class document aims to make using mongo calls easy, saves
needing to know the syntax for it. Just pass in the db instance
on init and the document to create an instance on and boom
"""


class Opcode(Enum):
    set = "$set"
    push = "$push"
    push_if_missing = "$addToSet"
    pull = "$pull"
    inc = "$inc"
    unset = "$unset"
    rename = "$rename"

    def __str__(self):
        return self.value


class Document:
    __slots__ = ("db", "logger")

    def __init__(self, connection, document_name):
        """
        Our init function, sets up the connection to the specified document
        Params:
         - connection (Mongo Connection) : Our database connection
         - documentName (str) : The document this instance should be
        """
        self.db = connection[document_name]
        self.logger = logging.get_logger(__name__)

    # <-- Pointer Methods -->
    async def find(
            self, _id: int,
            projection: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        For simpler calls, points to self.find_by_id
        """
        return await self.find_by_id(_id, projection)

    async def delete(self, _id: int) -> DeleteResult:
        """
        For simpler calls, points to self.delete_by_id
        """
        return await self.delete_by_id(_id)

    async def update(
            self, _id: int,
            _dict: Dict[str, Any],
            _return: Optional[bool] = False) -> Optional[Dict[str, Any]]:
        """
        For simpler calls, points to self.delete_by_id
        """
        return await self.update_by_id(_id, _dict, _return)

    # <-- Actual Methods -->

    async def find_many(
            self,
            _dict: Dict[str, Any] = None, *,
            limit: int = 0,
            skip: int = 0,
            sort: Dict[str, int] = None,
            group: Dict[str, Any] = None,
            projection: Dict[str, Any] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Returns the data found under quarry dict
        Params:
         -  _dict (Dictionary) : The Dictionary to quarry
         -  limit () : To limit the result in MongoDB, we use the limit() method.
        Returns:
         - None if nothing is found
         - If somethings found, return that
        """
        if (limit <= 0) and sort is None and _dict is not None:
            cursor = self.db.find(_dict, projection)
        else:
            payload = []
            if sort is not None:
                payload.append({"$sort": sort})
            if skip > 0:
                payload.append({"$skip": skip})
            if projection is not None:
                payload.append({"$project": projection})
            if group is not None:
                payload.append({"$group": group})
            if _dict is not None:
                payload.append({"$match": _dict})
            if limit > 0:
                payload.append({"$limit": limit})
            cursor = self.db.aggregate(payload)
        data = []
        async for document in cursor:
            data.append(document)
        return data

    async def aggregate(self, payload: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Aggregates data from database collection
        Params:
         -  payload (Dict[str, Any]) : The payload to aggregate data
        """
        cursor = self.db.aggregate(payload)
        data = []
        async for doc in cursor:
            data.append(doc)
        return data

    async def delete_by_id(self, _id: int) -> DeleteResult:
        """
        Deletes all items found with _id: `id`
        Params:
         -  id () : The id to search for and delete
        """
        return await self.db.delete_many({"_id": _id})

    async def insert(self, _dict: Dict):
        """
        insert something into the db
        Params:
        - _dict (Dictionary) : The Dictionary to insert
        """
        # Check if its actually a Dictionary
        if not isinstance(_dict, Dict):
            raise TypeError("Expected Dictionary.")

        # Always use your own _id
        if not _dict["_id"]:
            raise KeyError("_id not found in supplied dict.")

        await self.db.insert_one(_dict)

    async def upsert(
            self,
            _id: int,
            _dict: Dict[str, Any], _return: Optional[bool] = False) -> Optional[Dict[str, Any]]:
        """
        Makes a new item in the document, if it already exists
        it will update that item instead
        This function parses an input Dictionary to get
        the relevant information needed to insert.
        Supports inserting when the document already exists
        Params:
            - _dict (Dictionary) : Dictionary to parse for info

        """
        if _return:
            return await self.db.find_one_and_update(
                {"_id": _id}, {"$set": _dict},
                upsert=True, return_document=ReturnDocument.AFTER)
        await self.db.update_one({"_id": _id}, {"$set": _dict}, upsert=True)

    async def unset(self, _id: int, *_fields: str, _return: Optional[bool] = False) -> Optional[Dict[str, Any]]:
        """
        For when you want to remove a field from
        a pre-existing document in the collection
        This function parses an input Dictionary to get
        the relevant information needed to unset.
        Params:
         - _list (list[str]) : The elements to delete from collection
        """
        _dict = {}
        for field in _fields:
            _dict[field] = None
        if _return:
            return await self.db.find_one_and_update(
                {"_id": _id}, {"$unset": _dict},
                upsert=True, return_document=ReturnDocument.AFTER)
        await self.db.update_one({"_id": _id}, {"$unset": _dict})

    async def update_by_id(
            self,
            _id: int,
            _dict: Dict[str, Any],
            _return: bool = False) -> Optional[Dict[str, Any]]:
        """
        Makes a new item in the document, if it already exists
        it will update that item instead
        This function parses an input Dictionary to get
        the relevant information needed to insert.
        Supports inserting when the document already exists
        Params:
            - _dict (Dictionary) : Dictionary to parse for info

        """
        if _return:
            return await self.db.find_one_and_update(
                {"_id": _id}, _dict, upsert=True, return_document=ReturnDocument.AFTER)
        else:
            await self.db.update_one({"_id": _id}, _dict, upsert=True)
            return None

    async def replace(self, _id: int, _dict: Dict[str, Any]):
        """
        If you want to keep everything from the old document, include it in the dictionary object.
        >WARNING: You’ll forever lose any of the original document’s
        data that you don’t pass to the method replace_one().
         - _dict (Dictionary) : Dictionary to parse for info
        """
        await self.db.replace_one({"_id": _id}, _dict, upsert=True)

    async def increment(
            self,
            _id: int,
            _dict: Dict[str, Any],
            _return: bool = False
    ) -> Dict[str, Any]:
        """
        Increment a given `field` by `amount`
        Params:
        - _id () : The id to search for
        - _dict (Dictionary) : Dictionary to parse for info
        - _return (bool) : Return the edited value or not
        """
        if _return:
            return await self.db.find_one_and_update(
                {"_id": _id}, {"$inc": _dict},
                upsert=True, return_document=ReturnDocument.AFTER)
        await self.db.update_one({"_id": _id}, {"$inc": _dict}, upsert=True)

    async def bulk_write(
            self,
            requests: List[Union[UpdateOne, DeleteOne]],
            ordered: bool = False
    ) -> Optional[BulkWriteResult]:
        if requests is None or not requests:
            return
        return await self.db.bulk_write(requests, ordered=ordered)

    async def bulk_update(
            self, _list: Iterator[Dict[str, Any]],
            fields: List[str] = None, opcode: Union[str, Opcode] = Opcode.set) -> Optional[BulkWriteResult]:
        """
        Update many Docs a given `field` is needed
        Params:
        - id () : The id to search for
        - _list (List[Dict[str, Any]]) : List of Dictionary objects
        - field () : field to increment
        """
        requests = []
        opcode = str(opcode)
        for _dict in _list:
            field_dict = {}
            if fields is None:
                for field in _dict.keys():
                    if field == '_id':
                        continue
                    field_dict[field] = _dict[field]
            else:
                for field in fields:
                    field_dict[field] = _dict[field]
            requests.append(UpdateOne({"_id": _dict["_id"]}, {opcode: field_dict}, upsert=True))
        if not requests:
            return None
        try:
            return await self.db.bulk_write(requests, ordered=False)
        except BulkWriteError as bwe:
            self.logger.critical(bwe.details)

    async def filter_dump(self) -> None:
        """
        Delete many Docs a given by the list
        Params:
        - _list (List[Dict[str, Any]]) : List of Dictionary objects
        """
        requests = []
        for _dict in tuple(await self.get_all()):
            if len(_dict) == 1:
                requests.append(DeleteOne(_dict))
        try:
            await self.db.bulk_write(requests, ordered=False)
        except BulkWriteError as bwe:
            self.logger.critical(bwe.details)

    async def bulk_unset(self, field: str):
        """
        Unset many Docs a given `field` is needed
        Params:
        - field () : field to increment
        - _list (Optional[List[Dict[str, Any]]]) : list of dictionary
        """
        requests = []
        _list: List[Dict] = await self.find_many({field: {"$exists": True}}, projection={field: 1})
        for _dict in _list:
            requests.append(UpdateOne(
                {"_id": _dict["_id"]},
                {"$unset": {field: None}}
            ))
        if not requests:
            return
        try:
            await self.db.bulk_write(requests, ordered=False)
        except BulkWriteError as bwe:
            self.logger.error(bwe.details)

    async def get_all(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all data in the document
        """
        data = []
        async for document in self.db.find({}):
            data.append(document)
        return data

    # <-- Private methods -->
    async def find_by_id(
            self, _id: int,
            projection: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Returns the data found under `id`
        Params:
         -  id () : The id to search for
        Returns:
         - None if nothing is found
         - If somethings found, return that
        """
        if projection is not None:
            return await self.db.find_one({"_id": _id}, projection=projection)
        return await self.db.find_one({"_id": _id})

    async def find_one(
            self, query: Dict[str, Any],
            projection: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        if projection is not None:
            return await self.db.find_one(query, projection=projection)
        return await self.db.find_one(query)

    async def delete_many(self, quarry: Dict[str, Any] = None) -> DeleteResult:
        """
        Deletes many items found with quarry
        Params:
        """
        if quarry is None:
            quarry = dict()
        return await self.db.delete_many(quarry)
