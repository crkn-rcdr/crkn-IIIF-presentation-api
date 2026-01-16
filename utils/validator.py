"""IIIF Presentation Validation Service."""
import json
from jsonschema.exceptions import ValidationError
import traceback    
from utils.schema import schemavalidator
from iiif_prezi.loader import ManifestReader
from bottle import response
import logging
#config logger
logging.basicConfig(level=logging.INFO,handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


class Validator(object):
    """Validator class that runs with Bottle."""

    def __init__(self):
        """Initialize Validator with default_version."""
        self.default_version = "3.0"

    def check_manifest(self, data, version="3.0", url=None, warnings=[]):
        """Check manifest data at version, return JSON."""
        infojson = {}
        # Check if 3.0 if so run through schema rather than this version...
        if version == '3.0':
            try:
                infojson = schemavalidator.validate(data, version, url)
                logger.info(json.dumps(infojson, indent=2))
                for error in infojson['errorList']:
                    error.pop('error', None)

                mf = json.loads(data)
                if url and 'id' in mf and mf['id'] != url:
                    raise ValidationError("The manifest id ({}) should be the same as the URL it is published at ({}).".format(mf["id"], url))
            except ValidationError as e:
                if infojson:
                    infojson['errorList'].append({
                        'title': 'Resolve Error',
                        'detail': str(e),
                        'description': '',
                        'path': '/id',
                        'context': '{ \'id\': \'...\'}'
                        })
                else:
                    infojson = {
                        'okay': 0,
                        'error': str(e),
                        'url': url,
                        'warnings': []
                    }
            except Exception as e:    
                traceback.print_exc()
                infojson = {
                    'okay': 0,
                    'error': 'Presentation Validator bug: "{}". Please create a <a href="https://github.com/IIIF/presentation-validator/issues">Validator Issue</a>, including a link to the manifest.'.format(e),
                    'url': url,
                    'warnings': []
                }

        else:
            reader = ManifestReader(data, version=version)
            err = None
            try:
                mf = reader.read()
                mf.toJSON()
                if url and mf.id != url:
                    raise ValidationError("Manifest @id ({}) is different to the location where it was retrieved ({})".format(mf.id, url))
                # Passed!
                okay = 1
            except KeyError as e:    
                print ('Failed validation due to:')
                traceback.print_exc()
                err = 'Failed due to KeyError {}, check trace for details'.format(e)
                okay = 0
            except Exception as e:
                # Failed
                print ('Failed validation due to:')
                traceback.print_exc()
                err = e
                okay = 0

            warnings.extend(reader.get_warnings())
            infojson = {
                'okay': okay,
                'warnings': warnings,
                'error': str(err),
                'url': url
            }
        return self.return_json(infojson)

    def return_json(self, js):
        """Set header and return JSON response."""
        response.content_type = "application/json"
        return json.dumps(js)

