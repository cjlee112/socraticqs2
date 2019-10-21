import base64

from django.core.files.base import ContentFile

from lti.utils import key_secret_generator


def base64_to_file(data_attachment, prefix='image'):
    """
    convert base64 attachment string to django File
    :return: django ContentFile
    """
    if data_attachment and data_attachment.startswith('data:image'):
        format, image_string = data_attachment.split(';base64,')
        extension = format.split('/')[-1].split('+')[0]
        name = '{}-{}.{}'.format(prefix, key_secret_generator(), extension)
        return ContentFile(base64.b64decode(image_string), name=name)
    return None
