"""Pre- and post-processing of data prior to being input or output

# Overview
    Assume all data is written as plain-text documents. Formatting occurs
    within the plain-text and is interpreted based on the file-extension.

    E.g. ".json" is run through json.loads() whilst a ".txt" is
    run through str()

Inbetween data being either read or written, processing occurs.


     ------------           -------------          ------------ 
    |    disk    |  ---->  |   process   | ---->  |   output   |
    |____________|         |_____________|        |____________|


     ------------           -------------          ------------ 
    |   python   |  ---->  |   process   | ---->  |   output   |
    |____________|         |_____________|        |____________|    


# Examples
    When reading a plain-text document, processing means to first cast
    the raw data to a string, str()

    Reading a key/value store, such as Json, processing means running it
    through json.loads() which converts the raw string into a Python dict.

    Reading a Google Drive document, processing means authorising with 
    Google and downloading the document from the internet.


# Writing data
    Open Metadata is a file-based database. This means that at the end 
    of each write, a file must get written to disk. Whether it be 
    writing to Shotgun, Google Drive or Streaming data explicitly, a
    record of said operation is always stored on disk.

    When updating a document on Google Drive, it may not be necessary to
    update the link on disk, and thus the disk-writing action may be skipped.

"""

from abc import ABCMeta, abstractmethod
import logging
import json
import ConfigParser

log = logging.getLogger('openmetadata.process')


def preprocess(raw, format):
    """Process outgoing data"""
    format = mapping.get(format)
    if not format:
        raise ValueError('Format "%s" not supported' % format)

    return format.pre(raw)


def postprocess(raw, format):
    """Process incoming data"""
    format = mapping.get(format)
    if not format:
        raise ValueError('Format "%s" not supported' % format)

    return format.post(raw)


class AbstractFormat(object):
    """Required interface to each format"""

    __metaclass__ = ABCMeta

    @abstractmethod
    def pre(cls, raw):
        """Process --> Written

        `raw` is interpreted based on the given format and
        may be of any datatype.

        Output is given in an appropriate Python data-structure.

        """

        pass

    @abstractmethod
    def post(cls, raw):
        """Process <-- Read"""
        pass


class DotTxt(AbstractFormat):
    @classmethod
    def pre(self, raw):
        return str(raw)

    @classmethod
    def post(self, raw):
        return str(raw)


class DotJson(AbstractFormat):
    @classmethod
    def pre(self, raw):
        try:
            processed = json.dumps(raw, indent=4)
        except ValueError as e:
            log.debug(e)
            processed = {}
        except TypeError as e:
            raise TypeError("Data corrupt | %s\n%s" % (raw, e))

        return processed

    @classmethod
    def post(self, raw):
        processed = json.loads(raw)
        return processed


class DotIni(AbstractFormat):
    @classmethod
    def pre(self, raw):
        config = ConfigParser.ConfigParser()
        config.optionxform = str  # Case-sensitive
        config.read_string(raw)

        # Convert to dictionary
        data = {}
        for section in config.sections():
            data[section] = {}
            for option in config.options(section):
                data[section][option] = config.get(section, option)

        return data

    @classmethod
    def post(self, raw):
        pass


class DotGdoc(AbstractFormat):
    @classmethod
    def pre(self, raw):
        raise NotImplementedError

        # Raw is a Gdoc data-structure
        link = raw.get('link')

        # Download document
        google = gdata.login(usr, pw)
        document = google.download(link)

        return document

    @classmethod
    def post(self, raw):
        raise NotImplementedError

        link = raw.get('link')
        data = raw.get('data')

        # Upload document
        google = gdata.login(usr, pw)
        google.upload(data, link)

        # Create what will eventually be written to disk.
        # E.g. {"url": link, "resource_id": "document:1Euj54DtjdkRFd"}
        gdoc = raw.dump()
        
        return gdoc


mapping = {'.txt': DotTxt,
           '.json': DotJson,
           '.ini': DotIni,
           '.gdoc': DotGdoc}


if __name__ == '__main__':
    import openmetadata as om

    path = r'A:\development\marcus\scripts\python\about\test\.meta\chan4.kvs\properties.json'
    file = om.File(path)
    file.read()
    print file.path
    print file.data

    # inputted = {"Key": "Value"}
    # asstring = preprocess(inputted, '.json')
    # asdict = postprocess(asstring, '.json')

    # print asstring
    # print asdict